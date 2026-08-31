import math

from collections import deque


# =========================================================
# COCO POSE KEYPOINT INDEXES
# =========================================================

L_SHOULDER = 5
R_SHOULDER = 6

L_WRIST = 9
R_WRIST = 10

L_HIP = 11
R_HIP = 12


# =========================================================
# ORIGINAL V3 THRESHOLDS
#
# Keep these unchanged during initial integration.
# We first want behaviour parity with colleague's version.
# =========================================================

SMOOTH_FRAMES = 3

JUMP_REJECT_FRAC = 0.12

REACH_OUT_FRAC = 0.90

RETRACT_IN_FRAC = 0.55

RETRACT_WINDOW_S = 8.0

CONCEAL_COOLDOWN_S = 3.0

LOITER_SECONDS = 10.0

LOITER_RADIUS_FRAC = 0.05

BEND_ANGLE_DEG = 45

BEND_MIN_FRAMES = 6

EXIT_SPEED_FRAC = 1.1

QUICK_EXIT_WINDOW_S = 3.0

MIN_KPT_CONF = 0.5

MIN_TRACK_AGE_S = 1.0

SUSPICIOUS_SCORE = 5

WATCH_SCORE = 3

EVIDENCE_WINDOW_S = 12.0


# =========================================================
# HELPERS
# =========================================================

def dist(a, b):

    return math.hypot(
        a[0] - b[0],
        a[1] - b[1]
    )


def midpoint(a, b):

    return (
        (a[0] + b[0]) / 2.0,
        (a[1] + b[1]) / 2.0
    )


def avg_points(points):

    valid = [

        point

        for point in points

        if point is not None
    ]

    if not valid:

        return None

    return (

        sum(
            point[0]
            for point in valid
        )
        / len(valid),

        sum(
            point[1]
            for point in valid
        )
        / len(valid)
    )


# =========================================================
# PER-PERSON THEFT STATE
# =========================================================

class TheftTrackState:

    def __init__(
        self,
        fps,
        frame_diag
    ):

        self.fps = max(
            float(fps),
            1.0
        )

        self.frame_diag = max(
            float(frame_diag),
            1.0
        )


        self.center_hist = deque(
            maxlen=
                int(
                    2.0 * self.fps
                )
                + 1
        )

        self.exit_hist = deque(
            maxlen=
                int(
                    QUICK_EXIT_WINDOW_S
                    * self.fps
                )
                + 1
        )


        self._raw_l_wr = deque(
            maxlen=SMOOTH_FRAMES
        )

        self._raw_r_wr = deque(
            maxlen=SMOOTH_FRAMES
        )

        self._raw_hip = deque(
            maxlen=SMOOTH_FRAMES
        )

        self._raw_sh = deque(
            maxlen=SMOOTH_FRAMES
        )


        self.first_seen_t = None

        self.prev_center = None

        self.stationary_start = None


        self.reach_peak = {

            "L": 0.0,
            "R": 0.0
        }

        self.reach_peak_t = {

            "L": None,
            "R": None
        }


        self.last_conceal_t = None

        self.events = []

        self.alert_score = 0

        self.has_conceal_or_exit = False

        self._bend_streak = 0

        self._last_event_time = {}


    # =====================================================
    # UPDATE STATE
    # =====================================================

    def update(
        self,
        frame_idx,
        timestamp_s,
        keypoints,
        confidences,
        bbox
    ):

        if (
            keypoints is None
            or
            confidences is None
        ):

            return


        if (
            len(keypoints) < 17
            or
            len(confidences) < 17
        ):

            return


        cx = (
            bbox[0] + bbox[2]
        ) / 2.0

        cy = (
            bbox[1] + bbox[3]
        ) / 2.0


        if self.first_seen_t is None:

            self.first_seen_t = (
                timestamp_s
            )


        # =================================================
        # TRACK-JUMP REJECTION
        # =================================================

        glitch = False

        if self.prev_center is not None:

            jump = dist(
                (cx, cy),
                self.prev_center
            )

            if (
                jump
                >
                JUMP_REJECT_FRAC
                *
                self.frame_diag
            ):

                glitch = True


        self.prev_center = (
            cx,
            cy
        )


        self.center_hist.append(
            (
                timestamp_s,
                cx,
                cy
            )
        )

        self.exit_hist.append(
            (
                timestamp_s,
                cx,
                cy
            )
        )


        if glitch:

            return


        # =================================================
        # CONFIDENCE FILTER
        # =================================================

        def kp(index):

            try:

                confidence = float(
                    confidences[
                        index
                    ]
                )

                if (
                    confidence
                    <
                    MIN_KPT_CONF
                ):

                    return None


                point = (
                    keypoints[
                        index
                    ]
                )

                return (
                    float(point[0]),
                    float(point[1])
                )

            except (
                IndexError,
                TypeError,
                ValueError
            ):

                return None


        # =================================================
        # SMOOTH WRISTS / TORSO LANDMARKS
        # =================================================

        self._raw_l_wr.append(
            kp(
                L_WRIST
            )
        )

        self._raw_r_wr.append(
            kp(
                R_WRIST
            )
        )


        left_hip = kp(
            L_HIP
        )

        right_hip = kp(
            R_HIP
        )


        if (
            left_hip is not None
            and
            right_hip is not None
        ):

            hip_value = midpoint(
                left_hip,
                right_hip
            )

        else:

            hip_value = (
                left_hip
                or
                right_hip
            )


        self._raw_hip.append(
            hip_value
        )


        left_shoulder = kp(
            L_SHOULDER
        )

        right_shoulder = kp(
            R_SHOULDER
        )


        if (
            left_shoulder is not None
            and
            right_shoulder is not None
        ):

            shoulder_value = midpoint(
                left_shoulder,
                right_shoulder
            )

        else:

            shoulder_value = (
                left_shoulder
                or
                right_shoulder
            )


        self._raw_sh.append(
            shoulder_value
        )


        l_wr = avg_points(
            self._raw_l_wr
        )

        r_wr = avg_points(
            self._raw_r_wr
        )

        hip_mid = avg_points(
            self._raw_hip
        )

        sh_mid = avg_points(
            self._raw_sh
        )


        # =================================================
        # BODY SCALE
        # =================================================

        if (
            sh_mid is not None
            and
            hip_mid is not None
        ):

            torso_h = dist(
                sh_mid,
                hip_mid
            )

        else:

            torso_h = max(

                (
                    bbox[3]
                    -
                    bbox[1]
                )
                *
                0.45,

                5.0
            )


        if torso_h < 5.0:

            torso_h = max(

                (
                    bbox[3]
                    -
                    bbox[1]
                )
                *
                0.45,

                5.0
            )


        # =================================================
        # CONCEALMENT ANCHOR
        #
        # Prefer hips.
        # Fall back to shoulders.
        # =================================================

        anchor = (

            hip_mid

            if hip_mid is not None

            else sh_mid
        )


        too_new = (

            (
                timestamp_s
                -
                self.first_seen_t
            )
            <
            MIN_TRACK_AGE_S
        )


        # =================================================
        # CONCEALMENT
        # =================================================

        if (
            not too_new
            and
            anchor is not None
        ):

            self._check_concealment(

                frame_idx,
                timestamp_s,

                "L",

                l_wr,
                anchor,

                torso_h
            )

            self._check_concealment(

                frame_idx,
                timestamp_s,

                "R",

                r_wr,
                anchor,

                torso_h
            )


        # =================================================
        # BENDING
        # =================================================

        if (
            not too_new
            and
            sh_mid is not None
            and
            hip_mid is not None
        ):

            self._check_bend(
                frame_idx,
                timestamp_s,
                sh_mid,
                hip_mid
            )

        else:

            self._bend_streak = 0


        # =================================================
        # LOITERING + QUICK EXIT
        # =================================================

        if not too_new:

            self._check_loitering(
                frame_idx,
                timestamp_s,
                cx,
                cy
            )

            self._check_quick_exit(
                frame_idx,
                timestamp_s
            )


    # =====================================================
    # CONCEALMENT
    # =====================================================

    def _check_concealment(
        self,
        frame_idx,
        timestamp_s,
        side,
        wrist,
        anchor,
        torso_h
    ):

        if wrist is None:

            return


        distance_ratio = (

            dist(
                wrist,
                anchor
            )

            /

            torso_h
        )


        if (
            distance_ratio
            >
            self.reach_peak[
                side
            ]
        ):

            self.reach_peak[
                side
            ] = distance_ratio

            self.reach_peak_t[
                side
            ] = timestamp_s


        peak_t = (
            self.reach_peak_t[
                side
            ]
        )


        if (

            self.reach_peak[
                side
            ]
            >=
            REACH_OUT_FRAC

            and

            peak_t is not None

            and

            distance_ratio
            <=
            RETRACT_IN_FRAC

            and

            (
                timestamp_s
                -
                peak_t
            )
            <=
            RETRACT_WINDOW_S

        ):

            if (

                self.last_conceal_t
                is None

                or

                (
                    timestamp_s
                    -
                    self.last_conceal_t
                )
                >=
                CONCEAL_COOLDOWN_S

            ):

                self.last_conceal_t = (
                    timestamp_s
                )

                self.has_conceal_or_exit = (
                    True
                )

                self._log_event(

                    frame_idx,
                    timestamp_s,

                    "CONCEALMENT",

                    (
                        f"{side} hand reached out "
                        f"({self.reach_peak[side]:.2f}x torso) "
                        f"then pulled back in within "
                        f"{timestamp_s - peak_t:.1f}s"
                    )
                )


            self.reach_peak[
                side
            ] = distance_ratio

            self.reach_peak_t[
                side
            ] = timestamp_s


        if (

            peak_t is not None

            and

            (
                timestamp_s
                -
                peak_t
            )
            >
            RETRACT_WINDOW_S
            *
            2

        ):

            self.reach_peak[
                side
            ] = distance_ratio

            self.reach_peak_t[
                side
            ] = timestamp_s


    # =====================================================
    # BENDING
    # =====================================================

    def _check_bend(
        self,
        frame_idx,
        timestamp_s,
        shoulder,
        hip
    ):

        dx = (
            hip[0]
            -
            shoulder[0]
        )

        dy = (
            hip[1]
            -
            shoulder[1]
        )


        angle = math.degrees(

            math.atan2(
                abs(dx),
                abs(dy)
                +
                1e-6
            )
        )


        if (
            angle
            >
            BEND_ANGLE_DEG
        ):

            self._bend_streak += 1


            if (
                self._bend_streak
                ==
                BEND_MIN_FRAMES
            ):

                self._log_event(

                    frame_idx,
                    timestamp_s,

                    "BENDING",

                    (
                        f"torso angle "
                        f"{angle:.0f} deg "
                        f"from vertical, held"
                    ),

                    throttle=True
                )

        else:

            self._bend_streak = 0


    # =====================================================
    # LOITERING
    # =====================================================

    def _check_loitering(
        self,
        frame_idx,
        timestamp_s,
        cx,
        cy
    ):

        if (
            len(
                self.center_hist
            )
            <
            2
        ):

            return


        (
            start_t,
            start_x,
            start_y
        ) = self.center_hist[0]


        moved = dist(

            (
                cx,
                cy
            ),

            (
                start_x,
                start_y
            )
        )


        if (

            moved

            <

            LOITER_RADIUS_FRAC
            *
            self.frame_diag

        ):

            if self.stationary_start is None:

                self.stationary_start = (
                    start_t
                )


            elif (

                timestamp_s
                -
                self.stationary_start

                >=

                LOITER_SECONDS

            ):

                self._log_event(

                    frame_idx,
                    timestamp_s,

                    "LOITERING",

                    (
                        f"stationary for "
                        f"{timestamp_s - self.stationary_start:.1f}s"
                    ),

                    throttle=True
                )


                self.stationary_start = (
                    timestamp_s
                )

        else:

            self.stationary_start = None


    # =====================================================
    # QUICK EXIT
    # =====================================================

    def _check_quick_exit(
        self,
        frame_idx,
        timestamp_s
    ):

        if (

            self.last_conceal_t
            is None

            or

            (
                timestamp_s
                -
                self.last_conceal_t
            )
            >
            QUICK_EXIT_WINDOW_S

        ):

            return


        if (
            len(
                self.exit_hist
            )
            <
            2
        ):

            return


        (
            start_t,
            start_x,
            start_y
        ) = self.exit_hist[0]


        (
            end_t,
            end_x,
            end_y
        ) = self.exit_hist[-1]


        dt = (
            end_t
            -
            start_t
        )


        if dt <= 0:

            return


        speed = (

            dist(

                (
                    end_x,
                    end_y
                ),

                (
                    start_x,
                    start_y
                )
            )

            /

            dt
        )


        if (

            speed

            >

            EXIT_SPEED_FRAC
            *
            self.frame_diag

        ):

            self.has_conceal_or_exit = (
                True
            )


            self._log_event(

                frame_idx,
                timestamp_s,

                "QUICK_EXIT",

                (
                    "fast movement shortly "
                    "after concealment"
                ),

                throttle=True
            )


            self.last_conceal_t = None


    # =====================================================
    # LOG INTERNAL EVIDENCE
    # =====================================================

    def _log_event(
        self,
        frame_idx,
        timestamp_s,
        kind,
        note,
        throttle=False
    ):

        last_t = self._last_event_time.get(
            kind
        )

        if (
            throttle
            and
            last_t is not None
            and
            (
                timestamp_s
                -
                last_t
            )
            <
            2.0
        ):
            return

        self._last_event_time[
            kind
        ] = timestamp_s

        self.events.append(
            (
                frame_idx,
                timestamp_s,
                kind,
                note
            )
        )

        ##################################################
        # SCORING
        ##################################################

        existing_types = {
            event[2]
            for event in self.events[:-1]
        }

        # Weak contextual evidence should only count once.
        if (
            kind in (
                "BENDING",
                "LOITERING"
            )
            and
            kind in existing_types
        ):
            return

        weight = {

            "BENDING": 1,

            "LOITERING": 1,

            "CONCEALMENT": 5,

            "QUICK_EXIT": 3

        }.get(
            kind,
            0
        )

        self.alert_score += weight
    # =====================================================
    # STATUS
    # =====================================================

    def status(self, current_time):

        recent_events = [

            event

            for event in self.events

            if (
                0.0
                <=
                current_time - event[1]
                <=
                EVIDENCE_WINDOW_S
            )
        ]


        event_types = {

            event[2]

            for event
            in recent_events
        }


        has_concealment = (
            "CONCEALMENT"
            in event_types
        )


        ##################################################
        # IMPORTANT
        #
        # Without concealment there is NO theft state.
        #
        # Bending alone = NORMAL
        # Loitering alone = NORMAL
        ##################################################

        if not has_concealment:

            return "NORMAL"


        ##################################################
        # SUPPORTING SIGNAL
        ##################################################

        has_supporting_signal = any(

            event_type in event_types

            for event_type in (

                "BENDING",

                "LOITERING",

                "QUICK_EXIT"
            )
        )


        ##################################################
        # Concealment detected but no supporting evidence.
        ##################################################

        if not has_supporting_signal:

            return "WATCH"


        ##################################################
        # Calculate RECENT score only
        ##################################################

        recent_score = 0

        counted_weak_events = set()


        for event in recent_events:

            kind = event[2]


            # Bending and loitering count only once
            # inside the evidence window.

            if kind in (
                "BENDING",
                "LOITERING"
            ):

                if kind in counted_weak_events:

                    continue

                counted_weak_events.add(
                    kind
                )


            recent_score += {

                "BENDING": 1,

                "LOITERING": 1,

                "CONCEALMENT": 5,

                "QUICK_EXIT": 3

            }.get(
                kind,
                0
            )


        ##################################################
        # FINAL DECISION
        ##################################################

        if (
            recent_score
            >=
            SUSPICIOUS_SCORE
        ):

            return "SUSPICIOUS"


        return "WATCH"


# =========================================================
# PROJECT-INTEGRATED PROCESSOR
# =========================================================

class TheftProcessor:

    def __init__(
        self,
        fps=30.0
    ):

        self.fps = max(
            float(fps),
            1.0
        )

        self.states = {}

        # Remember whether final suspicious alert
        # has already been emitted for current track.
        self.alerted = set()


    def process(
        self,
        people,
        frame_idx,
        frame_shape
    ):

        alerts = []


        height, width = (
            frame_shape[:2]
        )

        frame_diag = math.hypot(
            width,
            height
        )


        # Video timeline time.
        #
        # For CCTV this is still perfectly valid
        # as elapsed track-processing time.
        timestamp_s = (

            frame_idx

            /

            self.fps
        )


        active_ids = set()


        for person in people.values():

            person_id = person.get(
                "id"
            )

            if person_id is None:

                continue


            active_ids.add(
                person_id
            )


            keypoints = person.get(
                "pose"
            )

            confidences = person.get(
                "pose_conf"
            )

            bbox = person.get(
                "box"
            )

            
            if (
                frame_idx % 10 == 0
                and confidences is not None
                and len(confidences) >= 13
            ):

                print(
                    "THEFT KPT CONF -> "
                    f"ID={person_id} | "
                    f"LS={confidences[5]:.2f} | "
                    f"RS={confidences[6]:.2f} | "
                    f"LW={confidences[9]:.2f} | "
                    f"RW={confidences[10]:.2f} | "
                    f"LH={confidences[11]:.2f} | "
                    f"RH={confidences[12]:.2f}"
                )

            # =============================================
            # Theft requires reliable pose + bounding box.
            # =============================================

            if (
                keypoints is None
                or
                confidences is None
                or
                bbox is None
            ):

                continue


            if (
                bbox[3]
                -
                bbox[1]
                <
                60
            ):

                continue

            
            ##################################################
            # LYING / HORIZONTAL PERSON FILTER
            ##################################################

            bbox_width = (
                bbox[2]
                -
                bbox[0]
            )

            bbox_height = (
                bbox[3]
                -
                bbox[1]
            )


            if bbox_height <= 0:

                continue


            bbox_aspect_ratio = (
                bbox_width
                /
                bbox_height
            )


            pose_state = str(

                person.get(
                    "pose_state",
                    "Unknown"
                )

            ).strip().lower()


            ##################################################
            # Known lying/fallen state
            ##################################################

            non_theft_pose = (

                pose_state
                in {

                    "fallen",

                    "lying",

                    "sleeping"
                }
            )


            ##################################################
            # Horizontal bounding box
            #
            # Example:
            # person lying on sofa/ground
            ##################################################

            horizontal_person = (

                bbox_aspect_ratio
                >
                1.35
            )


            if (
                non_theft_pose
                or
                horizontal_person
            ):

                person[
                    "theft_status"
                ] = "NORMAL"

                person[
                    "theft_score"
                ] = 0

                person[
                    "theft_evidence"
                ] = None


                ##################################################
                # Remove previous theft state
                #
                # Very important:
                # old concealment must not survive after
                # the person lies down.
                ##################################################

                self.states.pop(
                    person_id,
                    None
                )

                self.alerted.discard(
                    person_id
                )


                continue
            
            
            
            if (
                person_id
                not in
                self.states
            ):

                self.states[
                    person_id
                ] = TheftTrackState(

                    fps=
                        self.fps,

                    frame_diag=
                        frame_diag
                )


            state = self.states[
                person_id
            ]


            previous_event_count = (
                len(
                    state.events
                )
            )
            
            
            
            
            state.update(

                frame_idx=
                    frame_idx,

                timestamp_s=
                    timestamp_s,

                keypoints=
                    keypoints,

                confidences=
                    confidences,

                bbox=
                    bbox
            )


            current_status = (
                state.status(
                    timestamp_s
                )
            )


            person[
                "theft_status"
            ] = current_status

            person[
                "theft_score"
            ] = state.alert_score

            ##################################################
            # TEMPORARY THEFT DEBUG
            ##################################################

            if frame_idx % 10 == 0:

                print(
                    "THEFT DEBUG -> "
                    f"Frame={frame_idx} | "
                    f"ID={person_id} | "
                    f"Status={current_status} | "
                    f"Score={state.alert_score} | "
                    f"ReachL={state.reach_peak['L']:.2f} | "
                    f"ReachR={state.reach_peak['R']:.2f} | "
                    f"Conceal={state.last_conceal_t} | "
                    f"Events={[event[2] for event in state.events]}"
                )
            # =============================================
            # Store latest evidence for debugging/UI.
            # =============================================

            if (
                len(
                    state.events
                )
                >
                previous_event_count
            ):

                latest = (
                    state.events[-1]
                )

                person[
                    "theft_evidence"
                ] = latest[2]


                print(
                    "THEFT EVIDENCE -> "
                    f"ID={person_id} | "
                    f"Event={latest[2]} | "
                    f"Score={state.alert_score} | "
                    f"Status={current_status}"
                )

            ##################################################
            # RECENT EVIDENCE FOR VIDEO DISPLAY
            ##################################################

            recent_evidence = [

                event[2]

                for event
                in state.events

                if (
                    0.0
                    <=
                    timestamp_s - event[1]
                    <=
                    EVIDENCE_WINDOW_S
                )
            ]


            recent_evidence = list(
                dict.fromkeys(
                    recent_evidence
                )
            )


            if recent_evidence:

                person[
                    "theft_evidence"
                ] = " + ".join(
                    recent_evidence
                )

            else:

                person[
                    "theft_evidence"
                ] = None            
            # =============================================
            # FINAL ALERT
            #
            # Emit once per track when it becomes suspicious.
            # =============================================

            if (

                current_status
                ==
                "SUSPICIOUS"

                and

                person_id
                not in
                self.alerted

            ):

                self.alerted.add(
                    person_id
                )


                evidence = [

                    event[2]

                    for event
                    in state.events

                    if (
                        0.0
                        <=
                        timestamp_s - event[1]
                        <=
                        EVIDENCE_WINDOW_S
                    )
                ]


                # Preserve order, remove duplicates.
                evidence = list(
                    dict.fromkeys(
                        evidence
                    )
                )


                alert = {

                    "type":
                            "suspicious_concealment",

                    "title":
                            "SUSPICIOUS CONCEALMENT",

                    "message":
                        (
                            f"Person {person_id} "
                            f"showed suspicious "
                            f"concealment behaviour"
                        ),

                    "person_id":
                        person_id,

                    "severity":
                        "HIGH",

                    "score":
                        state.alert_score,

                    "evidence":
                        evidence,

                    "zone":
                        person.get(
                            "zone",
                            "Unknown"
                        )
                }


                alerts.append(
                    alert
                )


                print(
                    "\n========================================"
                )

                print(
                    "SUSPICIOUS CONCEALMENT"
                )

                print(
                    f"Person ID : {person_id}"
                )

                print(
                    f"Score     : {state.alert_score}"
                )

                print(
                    f"Evidence  : {evidence}"
                )

                print(
                    "========================================"
                )


        return alerts
