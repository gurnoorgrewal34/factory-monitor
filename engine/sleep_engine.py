"""
sleep_engine.py
============================================================

Production-oriented SLEEP / DROWSINESS detector for the shared
Factory Monitoring System pipeline.

DESIGN
------------------------------------------------------------

The engine intentionally does NOT classify sleep from one weak cue.

Factory/CCTV pose estimation frequently has:
    - missing face keypoints
    - side-facing workers
    - helmets / PPE
    - occlusion
    - hands close to face
    - noisy wrist positions
    - different camera angles

Therefore:

1. Missing face DOES NOT mean drowsy.
2. Hand near face DOES NOT mean drowsy by itself.
3. A single abnormal frame DOES NOT change the state.
4. Each person gets a rolling normal-head baseline.
5. Head drop is compared with that person's baseline.
6. Drowsy/sleep evidence must persist temporally.
7. UNKNOWN frames do not destroy an existing valid state.
8. State changes use hysteresis to prevent flickering.

The public API remains:

    SleepEngine(...)
    process_frame(frame, frame_idx, min_label_y=0)
    finalize(frame_idx)

so the existing FrameProcessor architecture can remain unchanged.
"""

import os
from collections import deque
from dataclasses import dataclass, field

import numpy as np
from ultralytics import YOLO

from app.config import POSE_MODEL_PATH


# ============================================================
# DEBUG
# ============================================================

SLEEP_DEBUG = False


# ============================================================
# COCO KEYPOINTS
# ============================================================

NOSE = 0

L_EYE = 1
R_EYE = 2

L_EAR = 3
R_EAR = 4

L_SHOULDER = 5
R_SHOULDER = 6

L_ELBOW = 7
R_ELBOW = 8

L_WRIST = 9
R_WRIST = 10

L_HIP = 11
R_HIP = 12


SKELETON_EDGES = [
    (L_EYE, R_EYE),
    (L_EAR, L_EYE),
    (R_EAR, R_EYE),
    (NOSE, L_EYE),
    (NOSE, R_EYE),

    (L_SHOULDER, R_SHOULDER),

    (L_SHOULDER, L_ELBOW),
    (L_ELBOW, L_WRIST),

    (R_SHOULDER, R_ELBOW),
    (R_ELBOW, R_WRIST),

    (L_SHOULDER, L_HIP),
    (R_SHOULDER, R_HIP),

    (L_HIP, R_HIP),
]


STATE_COLOR = {
    "AWAKE": (0, 200, 0),
    "DROWSY": (0, 165, 255),
    "SLEEPING": (0, 0, 255),
    "UNKNOWN": (150, 150, 150),
}


# ============================================================
# TRACKER SETTINGS
# ============================================================

TRACK_BUFFER_FRAMES = 60

REASSOC_SECONDS = 3.0

REASSOC_IOU_MIN = 0.05

REASSOC_CENTER_RATIO = 1.20


# ============================================================
# DETECTOR SETTINGS
# ============================================================

@dataclass
class Thresholds:

    # --------------------------------------------------------
    # Keypoint reliability
    # --------------------------------------------------------

    kp_conf_min: float = 0.30

    face_conf_min: float = 0.25


    # --------------------------------------------------------
    # Absolute head geometry
    #
    # head_ratio =
    #
    #   (head_y - shoulder_y) / person_box_height
    #
    # Normal head is normally ABOVE shoulders => negative.
    #
    # Positive means the estimated head has moved to / below
    # shoulder level and is therefore highly abnormal.
    # --------------------------------------------------------

    absolute_head_drowsy: float = -0.015

    absolute_head_sleep: float = 0.025


    # --------------------------------------------------------
    # PERSONAL BASELINE DELTA
    #
    # Example:
    #
    # normal baseline = -0.12
    # current         = -0.05
    #
    # delta = +0.07
    #
    # Therefore head has moved downward.
    # --------------------------------------------------------

    baseline_drop_drowsy: float = 0.055

    baseline_drop_sleep: float = 0.095


    # --------------------------------------------------------
    # Head tilt
    # --------------------------------------------------------

    tilt_drowsy_deg: float = 30.0

    tilt_sleep_deg: float = 42.0


    # --------------------------------------------------------
    # Hand near face
    #
    # SUPPORTING evidence only.
    # --------------------------------------------------------

    hand_near_head_ratio: float = 0.28


    # --------------------------------------------------------
    # Temporal confirmation
    # --------------------------------------------------------

    drowsy_confirm_seconds: float = 2.0

    sleep_confirm_seconds: float = 4.0

    awake_confirm_seconds: float = 1.0


    # --------------------------------------------------------
    # Baseline
    # --------------------------------------------------------

    baseline_samples: int = 20

    baseline_min_samples: int = 5


    # --------------------------------------------------------
    # Missing-pose tolerance
    # --------------------------------------------------------

    missing_hold_seconds: float = 1.5


    # --------------------------------------------------------
    # Alert
    # --------------------------------------------------------

    alert_seconds: float = 4.0


# ============================================================
# HELPERS
# ============================================================

def _confident(kp, threshold):

    try:

        if kp is None or len(kp) < 3:
            return False

        value = float(kp[2])

        return (
            np.isfinite(value)
            and
            value >= threshold
        )

    except (TypeError, ValueError, IndexError):

        return False


def _dist(a, b):

    return float(
        np.hypot(
            float(a[0]) - float(b[0]),
            float(a[1]) - float(b[1])
        )
    )


def _safe(value, digits=3):

    if value is None:
        return "NA"

    try:

        value = float(value)

        if not np.isfinite(value):
            return "NA"

        return f"{value:.{digits}f}"

    except (TypeError, ValueError):

        return "NA"


def _center(box):

    x1, y1, x2, y2 = box

    return (
        (x1 + x2) / 2.0,
        (y1 + y2) / 2.0
    )


def _iou(a, b):

    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b

    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)

    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)

    iw = max(0.0, ix2 - ix1)
    ih = max(0.0, iy2 - iy1)

    intersection = iw * ih

    if intersection <= 0:
        return 0.0

    area_a = (
        max(0.0, ax2 - ax1)
        *
        max(0.0, ay2 - ay1)
    )

    area_b = (
        max(0.0, bx2 - bx1)
        *
        max(0.0, by2 - by1)
    )

    union = area_a + area_b - intersection

    return intersection / union if union > 0 else 0.0


# ============================================================
# POSE FEATURES
# ============================================================

def extract_sleep_features(kps, box, th):

    """
    Extract geometry only.

    IMPORTANT:

    This function does NOT directly decide DROWSY/SLEEPING.

    Temporal logic is handled later.
    """

    debug = {
        "valid": False,
        "face_visible": False,
        "head_ratio": None,
        "tilt_deg": None,
        "hand_near_head": False,
        "shoulders_visible": False,
    }


    # --------------------------------------------------------
    # Shoulders
    # --------------------------------------------------------

    have_l_sh = _confident(
        kps[L_SHOULDER],
        th.kp_conf_min
    )

    have_r_sh = _confident(
        kps[R_SHOULDER],
        th.kp_conf_min
    )


    if not (have_l_sh or have_r_sh):

        return debug


    debug["shoulders_visible"] = True


    if have_l_sh and have_r_sh:

        shoulder_mid = np.array([
            (
                float(kps[L_SHOULDER][0])
                +
                float(kps[R_SHOULDER][0])
            ) / 2.0,

            (
                float(kps[L_SHOULDER][1])
                +
                float(kps[R_SHOULDER][1])
            ) / 2.0,
        ])


    elif have_l_sh:

        shoulder_mid = np.array(
            kps[L_SHOULDER][:2],
            dtype=float
        )


    else:

        shoulder_mid = np.array(
            kps[R_SHOULDER][:2],
            dtype=float
        )


    # --------------------------------------------------------
    # Person scale
    # --------------------------------------------------------

    x1, y1, x2, y2 = box

    person_height = max(
        float(y2 - y1),
        1.0
    )


    # --------------------------------------------------------
    # Face / head point
    # --------------------------------------------------------

    face_indexes = [
        NOSE,
        L_EYE,
        R_EYE,
        L_EAR,
        R_EAR
    ]


    visible_face_points = []

    for index in face_indexes:

        if _confident(
            kps[index],
            th.face_conf_min
        ):

            visible_face_points.append(
                np.array(
                    kps[index][:2],
                    dtype=float
                )
            )


    debug["face_visible"] = (
        len(visible_face_points) > 0
    )


    if not visible_face_points:

        # Missing face is NOT evidence of sleep.
        return debug


    # Prefer nose because it is more stable for head-drop.
    if _confident(
        kps[NOSE],
        th.face_conf_min
    ):

        head_point = np.array(
            kps[NOSE][:2],
            dtype=float
        )

    else:

        head_point = np.mean(
            visible_face_points,
            axis=0
        )


    # --------------------------------------------------------
    # Head vertical position
    # --------------------------------------------------------

    head_ratio = (
        float(head_point[1])
        -
        float(shoulder_mid[1])
    ) / person_height


    debug["head_ratio"] = float(
        head_ratio
    )


    # --------------------------------------------------------
    # Tilt
    # --------------------------------------------------------

    p1 = None
    p2 = None


    if (
        _confident(
            kps[L_EYE],
            th.face_conf_min
        )
        and
        _confident(
            kps[R_EYE],
            th.face_conf_min
        )
    ):

        p1 = kps[L_EYE][:2]
        p2 = kps[R_EYE][:2]


    elif (
        _confident(
            kps[L_EAR],
            th.face_conf_min
        )
        and
        _confident(
            kps[R_EAR],
            th.face_conf_min
        )
    ):

        p1 = kps[L_EAR][:2]
        p2 = kps[R_EAR][:2]


    if p1 is not None and p2 is not None:

        angle = abs(
            np.degrees(
                np.arctan2(
                    float(p2[1]) - float(p1[1]),
                    float(p2[0]) - float(p1[0])
                )
            )
        )

        angle = min(
            angle,
            180.0 - angle
        )

        debug["tilt_deg"] = float(
            angle
        )


    # --------------------------------------------------------
    # Hand near head
    # --------------------------------------------------------

    wrist_points = []

    for index in (
        L_WRIST,
        R_WRIST
    ):

        if _confident(
            kps[index],
            th.kp_conf_min
        ):

            wrist_points.append(
                kps[index][:2]
            )


    if wrist_points:

        distance = min(
            _dist(
                head_point,
                wrist
            )
            for wrist in wrist_points
        )

        normalized_distance = (
            distance / person_height
        )

        debug["hand_near_head"] = (
            normalized_distance
            <
            th.hand_near_head_ratio
        )


    debug["valid"] = True

    return debug


# ============================================================
# PER-PERSON STATE
# ============================================================

@dataclass
class TrackState:

    stable_state: str = "AWAKE"

    state_since_frame: int = 0

    last_seen_frame: int = 0

    alerted: bool = False


    # --------------------------------------------------------
    # Personal normal-head baseline
    # --------------------------------------------------------

    baseline_history: deque = field(
        default_factory=lambda:
        deque(maxlen=20)
    )


    # --------------------------------------------------------
    # Consecutive evidence
    # --------------------------------------------------------

    drowsy_evidence: int = 0

    sleep_evidence: int = 0

    awake_evidence: int = 0

    invalid_evidence: int = 0


# ============================================================
# CLASSIFICATION
# ============================================================

def classify_evidence(
    features,
    baseline,
    th
):

    """
    Returns:

        AWAKE
        DROWSY
        SLEEPING
        UNKNOWN

    This is RAW evidence.

    Temporal confirmation happens in SleepEngine.
    """

    if not features["valid"]:

        return "UNKNOWN", 0.0


    head_ratio = features["head_ratio"]

    tilt = features["tilt_deg"]

    hand_near = features["hand_near_head"]


    # --------------------------------------------------------
    # Relative head drop
    # --------------------------------------------------------

    baseline_delta = None

    if (
        baseline is not None
        and
        head_ratio is not None
    ):

        baseline_delta = (
            head_ratio - baseline
        )


    # --------------------------------------------------------
    # Strong sleep cues
    # --------------------------------------------------------

    strong_head_drop = False

    moderate_head_drop = False


    if head_ratio is not None:

        if (
            head_ratio
            >=
            th.absolute_head_sleep
        ):

            strong_head_drop = True


        elif (
            head_ratio
            >=
            th.absolute_head_drowsy
        ):

            moderate_head_drop = True


    if baseline_delta is not None:

        if (
            baseline_delta
            >=
            th.baseline_drop_sleep
        ):

            strong_head_drop = True


        elif (
            baseline_delta
            >=
            th.baseline_drop_drowsy
        ):

            moderate_head_drop = True


    # --------------------------------------------------------
    # Tilt
    # --------------------------------------------------------

    strong_tilt = (
        tilt is not None
        and
        tilt >= th.tilt_sleep_deg
    )


    moderate_tilt = (
        tilt is not None
        and
        tilt >= th.tilt_drowsy_deg
    )


    # --------------------------------------------------------
    # Evidence score
    #
    # Head movement dominates.
    #
    # Hand position cannot independently produce DROWSY.
    # --------------------------------------------------------

    score = 0.0


    if strong_head_drop:

        score += 3.0


    elif moderate_head_drop:

        score += 2.0


    if strong_tilt:

        score += 2.0


    elif moderate_tilt:

        score += 1.0


    if (
        hand_near
        and
        (
            moderate_head_drop
            or
            strong_head_drop
            or
            moderate_tilt
            or
            strong_tilt
        )
    ):

        score += 0.5


    # --------------------------------------------------------
    # State
    # --------------------------------------------------------

    if (
        strong_head_drop
        and
        (
            strong_tilt
            or
            score >= 3.5
        )
    ):

        return "SLEEPING", score


    if (
        moderate_head_drop
        or
        strong_head_drop
        or
        strong_tilt
    ):

        return "DROWSY", score


    return "AWAKE", score


# ============================================================
# ID MERGER
# ============================================================

class IDMerger:

    def __init__(
        self,
        source_fps,
        reassoc_seconds,
        iou_min,
        center_ratio
    ):

        self.reassoc_frames = max(
            1,
            round(
                source_fps
                *
                reassoc_seconds
            )
        )

        self.iou_min = iou_min

        self.center_ratio = center_ratio

        self.raw_to_stable = {}

        self.active = {}

        self.lost = {}

        self.next_id = 1


    def resolve(
        self,
        raw_id,
        box,
        frame_idx
    ):

        if raw_id in self.raw_to_stable:

            stable_id = self.raw_to_stable[
                raw_id
            ]

        else:

            stable_id = self._match_lost(
                box,
                frame_idx
            )

            if stable_id is None:

                stable_id = self.next_id

                self.next_id += 1

            else:

                self.lost.pop(
                    stable_id,
                    None
                )

            self.raw_to_stable[
                raw_id
            ] = stable_id


        self.active[
            stable_id
        ] = {
            "box": tuple(box),
            "frame": frame_idx,
            "raw_id": raw_id
        }


        return stable_id


    def _match_lost(
        self,
        box,
        frame_idx
    ):

        best_id = None
        best_iou = 0.0


        for stable_id, record in self.lost.items():

            if (
                frame_idx - record["frame"]
                >
                self.reassoc_frames
            ):
                continue


            value = _iou(
                box,
                record["box"]
            )


            if (
                value >= self.iou_min
                and
                value > best_iou
            ):

                best_id = stable_id
                best_iou = value


        if best_id is not None:

            return best_id


        best_distance = None


        for stable_id, record in self.lost.items():

            if (
                frame_idx - record["frame"]
                >
                self.reassoc_frames
            ):
                continue


            old_box = record["box"]

            height = max(
                old_box[3] - old_box[1],
                1.0
            )


            distance = (
                _dist(
                    _center(box),
                    _center(old_box)
                )
                /
                height
            )


            if (
                distance <= self.center_ratio
                and
                (
                    best_distance is None
                    or
                    distance < best_distance
                )
            ):

                best_id = stable_id
                best_distance = distance


        return best_id


    def end_frame(
        self,
        seen_raw_ids,
        frame_idx
    ):

        active_raw = {
            record["raw_id"]
            for record in self.active.values()
        }


        vanished = (
            active_raw
            -
            seen_raw_ids
        )


        for raw_id in vanished:

            stable_id = self.raw_to_stable.pop(
                raw_id,
                None
            )

            if stable_id is None:
                continue


            record = self.active.pop(
                stable_id,
                None
            )


            if record is not None:

                self.lost[
                    stable_id
                ] = record


        expired = [
            stable_id
            for stable_id, record
            in self.lost.items()

            if (
                frame_idx - record["frame"]
                >
                self.reassoc_frames
            )
        ]


        for stable_id in expired:

            self.lost.pop(
                stable_id,
                None
            )


# ============================================================
# TRACKER CONFIG
# ============================================================

def write_tracker_config(
    path,
    track_buffer
):

    content = (
        "tracker_type: bytetrack\n"
        "track_high_thresh: 0.5\n"
        "track_low_thresh: 0.1\n"
        "new_track_thresh: 0.6\n"
        f"track_buffer: {track_buffer}\n"
        "match_thresh: 0.8\n"
        "fuse_score: True\n"
    )


    # Rewrite so stale configs from previous experiments
    # cannot silently remain active.
    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(content)


    return path


# ============================================================
# DRAWING
# ============================================================

def draw_person(
    frame,
    kps,
    box,
    state,
    tid,
    th,
    seconds_in_state,
    min_label_y=0
):

    import cv2


    h, w = frame.shape[:2]


    color = STATE_COLOR.get(
        state,
        STATE_COLOR["UNKNOWN"]
    )


    x1, y1, x2, y2 = map(
        int,
        box
    )


    cv2.rectangle(
        frame,
        (x1, y1),
        (x2, y2),
        color,
        2
    )


    # --------------------------------------------------------
    # Skeleton
    # --------------------------------------------------------

    for i, j in SKELETON_EDGES:

        if (
            _confident(
                kps[i],
                th.kp_conf_min
            )
            and
            _confident(
                kps[j],
                th.kp_conf_min
            )
        ):

            p1 = tuple(
                map(
                    int,
                    kps[i][:2]
                )
            )

            p2 = tuple(
                map(
                    int,
                    kps[j][:2]
                )
            )


            cv2.line(
                frame,
                p1,
                p2,
                color,
                1,
                cv2.LINE_AA
            )


    for kp in kps:

        if _confident(
            kp,
            th.kp_conf_min
        ):

            cv2.circle(
                frame,
                (
                    int(kp[0]),
                    int(kp[1])
                ),
                3,
                color,
                -1
            )


    # --------------------------------------------------------
    # Label
    # --------------------------------------------------------

    label = f"P{tid}: {state}"


    if state in (
        "DROWSY",
        "SLEEPING"
    ):

        label += (
            f" {seconds_in_state:.1f}s"
        )


    font = cv2.FONT_HERSHEY_SIMPLEX

    font_scale = 0.5

    thickness = 1


    (tw, text_h), baseline = cv2.getTextSize(
        label,
        font,
        font_scale,
        thickness
    )


    label_y = (
        y2 + text_h + 8
    )


    if label_y > h - 4:

        label_y = max(
            min_label_y + text_h + 4,
            y2 - 6
        )


    padding = 3


    tx = max(
        0,
        min(
            x1,
            w - tw - padding * 2
        )
    )


    cv2.rectangle(
        frame,
        (
            tx,
            label_y - text_h - padding
        ),
        (
            tx + tw + padding * 2,
            label_y + baseline
        ),
        color,
        -1
    )


    cv2.putText(
        frame,
        label,
        (
            tx + padding,
            label_y
        ),
        font,
        font_scale,
        (0, 0, 0),
        thickness,
        cv2.LINE_AA
    )


# ============================================================
# SLEEP ENGINE
# ============================================================

class SleepEngine:

    def __init__(
        self,
        src_fps,
        model=POSE_MODEL_PATH,
        imgsz=640,
        process_fps=8.0,
        log=print
    ):

        self.th = Thresholds()

        self.log = log

        self.imgsz = int(imgsz)


        # ----------------------------------------------------
        # FPS
        # ----------------------------------------------------

        try:

            self.src_fps = float(
                src_fps
            )

        except (TypeError, ValueError):

            self.src_fps = 30.0


        if (
            not np.isfinite(self.src_fps)
            or
            self.src_fps <= 1.0
        ):

            self.src_fps = 30.0


        process_fps = max(
            1.0,
            float(process_fps)
        )


        self.stride = max(
            1,
            round(
                self.src_fps
                /
                process_fps
            )
        )


        self.processed_fps = (
            self.src_fps
            /
            self.stride
        )


        # ----------------------------------------------------
        # Temporal thresholds measured in inference samples
        # ----------------------------------------------------

        self.drowsy_confirm = max(
            2,
            round(
                self.processed_fps
                *
                self.th.drowsy_confirm_seconds
            )
        )


        self.sleep_confirm = max(
            2,
            round(
                self.processed_fps
                *
                self.th.sleep_confirm_seconds
            )
        )


        self.awake_confirm = max(
            2,
            round(
                self.processed_fps
                *
                self.th.awake_confirm_seconds
            )
        )


        self.missing_hold = max(
            1,
            round(
                self.processed_fps
                *
                self.th.missing_hold_seconds
            )
        )


        self.alert_frames = max(
            1,
            round(
                self.src_fps
                *
                self.th.alert_seconds
            )
        )


        # ----------------------------------------------------
        # Model
        # ----------------------------------------------------

        model_path = (
            model
            if model
            else POSE_MODEL_PATH
        )


        self.model = YOLO(
            model_path
        )


        # ----------------------------------------------------
        # Tracker
        # ----------------------------------------------------

        self.tracker_cfg = write_tracker_config(
            "custom_bytetrack.yaml",
            TRACK_BUFFER_FRAMES
        )


        self.id_merger = IDMerger(
            self.src_fps,
            REASSOC_SECONDS,
            REASSOC_IOU_MIN,
            REASSOC_CENTER_RATIO
        )


        # ----------------------------------------------------
        # Runtime state
        # ----------------------------------------------------

        self.tracks = {}

        self.open_events = {}

        self.log_rows = []

        self._last_people = []


        self.log(
            "SLEEP ENGINE READY -> "
            f"Model={model_path} | "
            f"SourceFPS={self.src_fps:.2f} | "
            f"PoseFPS={self.processed_fps:.2f} | "
            f"Stride={self.stride}"
        )


    # ========================================================
    # BASELINE
    # ========================================================

    def _get_baseline(
        self,
        track
    ):

        if (
            len(track.baseline_history)
            <
            self.th.baseline_min_samples
        ):

            return None


        return float(
            np.median(
                list(
                    track.baseline_history
                )
            )
        )


    def _update_baseline(
        self,
        track,
        head_ratio,
        raw_state
    ):

        """
        Baseline is learned only from frames that currently
        look awake.

        Therefore an actual sleepy posture should not gradually
        become the new "normal".
        """

        if head_ratio is None:
            return


        if raw_state != "AWAKE":
            return


        track.baseline_history.append(
            float(head_ratio)
        )


    # ========================================================
    # STATE CHANGE
    # ========================================================

    def _set_state(
        self,
        tid,
        track,
        new_state,
        frame_idx
    ):

        if new_state == track.stable_state:
            return


        # ----------------------------------------------------
        # Close old event
        # ----------------------------------------------------

        if tid in self.open_events:

            event = self.open_events.pop(
                tid
            )

            event["end_frame"] = frame_idx

            event["end_time_s"] = round(
                frame_idx / self.src_fps,
                2
            )

            event["duration_s"] = round(
                event["end_time_s"]
                -
                event["start_time_s"],
                2
            )

            self.log_rows.append(
                event
            )


        # ----------------------------------------------------
        # Start new event
        # ----------------------------------------------------

        self.open_events[tid] = {
            "track_id": tid,
            "state": new_state,
            "start_frame": frame_idx,
            "start_time_s": round(
                frame_idx / self.src_fps,
                2
            ),
        }


        track.stable_state = new_state

        track.state_since_frame = frame_idx

        track.alerted = False


    # ========================================================
    # PROCESS TEMPORAL EVIDENCE
    # ========================================================

    def _update_temporal_state(
        self,
        tid,
        track,
        raw_state,
        frame_idx
    ):

        # ----------------------------------------------------
        # Invalid pose
        # ----------------------------------------------------

        if raw_state == "UNKNOWN":

            track.invalid_evidence += 1

            # Do not convert UNKNOWN to DROWSY.
            # Do not immediately destroy previous state.

            return


        track.invalid_evidence = 0


        # ----------------------------------------------------
        # AWAKE
        # ----------------------------------------------------

        if raw_state == "AWAKE":

            track.awake_evidence += 1

            # Strongly decay abnormal evidence instead of
            # resetting on one frame.
            track.drowsy_evidence = max(
                0,
                track.drowsy_evidence - 2
            )

            track.sleep_evidence = max(
                0,
                track.sleep_evidence - 2
            )


            if (
                track.awake_evidence
                >=
                self.awake_confirm
            ):

                self._set_state(
                    tid,
                    track,
                    "AWAKE",
                    frame_idx
                )


            return


        # ----------------------------------------------------
        # DROWSY
        # ----------------------------------------------------

        if raw_state == "DROWSY":

            track.drowsy_evidence += 1

            track.awake_evidence = max(
                0,
                track.awake_evidence - 1
            )

            track.sleep_evidence = max(
                0,
                track.sleep_evidence - 1
            )


            if (
                track.drowsy_evidence
                >=
                self.drowsy_confirm
            ):

                self._set_state(
                    tid,
                    track,
                    "DROWSY",
                    frame_idx
                )


            return


        # ----------------------------------------------------
        # SLEEPING
        # ----------------------------------------------------

        if raw_state == "SLEEPING":

            track.sleep_evidence += 1

            # Sleeping is also evidence of drowsiness.
            track.drowsy_evidence += 1

            track.awake_evidence = max(
                0,
                track.awake_evidence - 1
            )


            if (
                track.sleep_evidence
                >=
                self.sleep_confirm
            ):

                self._set_state(
                    tid,
                    track,
                    "SLEEPING",
                    frame_idx
                )


            elif (
                track.drowsy_evidence
                >=
                self.drowsy_confirm
            ):

                self._set_state(
                    tid,
                    track,
                    "DROWSY",
                    frame_idx
                )


    # ========================================================
    # PROCESS FRAME
    # ========================================================

    def process_frame(
        self,
        frame,
        frame_idx,
        min_label_y=0
    ):

        # ----------------------------------------------------
        # Pose inference
        # ----------------------------------------------------

        if (
            frame_idx
            %
            self.stride
            ==
            0
        ):

            try:

                results = self.model.track(
                    frame,
                    persist=True,
                    verbose=False,
                    imgsz=self.imgsz,
                    tracker=self.tracker_cfg
                )

            except Exception as exc:

                self.log(
                    "SLEEP ENGINE ERROR -> "
                    f"{repr(exc)}"
                )

                results = None


            if results:

                result = results[0]


                if (
                    result.keypoints is not None
                    and
                    result.boxes is not None
                    and
                    result.boxes.id is not None
                ):

                    keypoints = (
                        result.keypoints.data
                        .cpu()
                        .numpy()
                    )


                    raw_ids = (
                        result.boxes.id
                        .int()
                        .cpu()
                        .numpy()
                    )


                    boxes = (
                        result.boxes.xyxy
                        .cpu()
                        .numpy()
                    )


                    seen_raw_ids = {
                        int(raw_id)
                        for raw_id in raw_ids
                    }


                    new_people = []


                    for (
                        person_kps,
                        raw_id,
                        box
                    ) in zip(
                        keypoints,
                        raw_ids,
                        boxes
                    ):

                        # ------------------------------------
                        # Stable ID
                        # ------------------------------------

                        tid = self.id_merger.resolve(
                            int(raw_id),
                            tuple(box),
                            frame_idx
                        )


                        # ------------------------------------
                        # Track state
                        # ------------------------------------

                        if tid not in self.tracks:

                            self.tracks[tid] = TrackState(
                                baseline_history=deque(
                                    maxlen=
                                    self.th.baseline_samples
                                ),
                                state_since_frame=
                                frame_idx
                            )


                        track = self.tracks[tid]

                        track.last_seen_frame = frame_idx


                        # ------------------------------------
                        # Features
                        # ------------------------------------

                        features = extract_sleep_features(
                            person_kps,
                            box,
                            self.th
                        )


                        # ------------------------------------
                        # Baseline
                        # ------------------------------------

                        baseline = self._get_baseline(
                            track
                        )


                        # ------------------------------------
                        # Raw classification
                        # ------------------------------------

                        raw_state, score = classify_evidence(
                            features,
                            baseline,
                            self.th
                        )


                        # ------------------------------------
                        # Update baseline
                        # ------------------------------------

                        self._update_baseline(
                            track,
                            features.get(
                                "head_ratio"
                            ),
                            raw_state
                        )


                        # ------------------------------------
                        # Temporal state machine
                        # ------------------------------------

                        self._update_temporal_state(
                            tid,
                            track,
                            raw_state,
                            frame_idx
                        )


                        # ------------------------------------
                        # Duration
                        # ------------------------------------

                        duration_frames = max(
                            0,
                            frame_idx
                            -
                            track.state_since_frame
                        )


                        seconds_in_state = (
                            duration_frames
                            /
                            self.src_fps
                        )


                        # ------------------------------------
                        # Alert
                        # ------------------------------------

                        if (
                            track.stable_state
                            ==
                            "SLEEPING"
                            and
                            not track.alerted
                            and
                            duration_frames
                            >=
                            self.alert_frames
                        ):

                            track.alerted = True


                            self.log(
                                "[ALERT] [SLEEP] "
                                f"Person={tid} | "
                                f"Duration="
                                f"{seconds_in_state:.1f}s"
                            )


                        # ------------------------------------
                        # Debug
                        # ------------------------------------

                        if SLEEP_DEBUG:

                            delta = None

                            if (
                                baseline is not None
                                and
                                features.get(
                                    "head_ratio"
                                )
                                is not None
                            ):

                                delta = (
                                    features["head_ratio"]
                                    -
                                    baseline
                                )


                            self.log(
                                "SLEEP DEBUG -> "
                                f"ID={tid} | "
                                f"Raw={raw_state} | "
                                f"Stable={track.stable_state} | "
                                f"Score={score:.1f} | "
                                f"Head="
                                f"{_safe(features.get('head_ratio'))} | "
                                f"Base="
                                f"{_safe(baseline)} | "
                                f"Delta="
                                f"{_safe(delta)} | "
                                f"Tilt="
                                f"{_safe(features.get('tilt_deg'), 1)} | "
                                f"Hand="
                                f"{features.get('hand_near_head')} | "
                                f"DrowsyEv="
                                f"{track.drowsy_evidence}/"
                                f"{self.drowsy_confirm} | "
                                f"SleepEv="
                                f"{track.sleep_evidence}/"
                                f"{self.sleep_confirm}"
                            )


                        # ------------------------------------
                        # Drawing cache
                        # ------------------------------------

                        new_people.append(
                            (
                                person_kps,
                                box,
                                tid,
                                track.stable_state,
                                seconds_in_state
                            )
                        )


                    self.id_merger.end_frame(
                        seen_raw_ids,
                        frame_idx
                    )


                    if new_people:

                        self._last_people = new_people


        # ----------------------------------------------------
        # Draw cached pose on every source frame
        # ----------------------------------------------------

        for (
            kps,
            box,
            tid,
            state,
            seconds
        ) in self._last_people:

            draw_person(
                frame,
                kps,
                box,
                state,
                tid,
                self.th,
                seconds,
                min_label_y=min_label_y
            )


    # ========================================================
    # FINALIZE
    # ========================================================

    def finalize(
        self,
        frame_idx
    ):

        for tid, event in list(
            self.open_events.items()
        ):

            event["end_frame"] = frame_idx

            event["end_time_s"] = round(
                frame_idx / self.src_fps,
                2
            )

            event["duration_s"] = round(
                event["end_time_s"]
                -
                event["start_time_s"],
                2
            )

            self.log_rows.append(
                event
            )


        self.open_events = {}


        return sorted(
            self.log_rows,
            key=lambda row:
            row["start_frame"]
        )