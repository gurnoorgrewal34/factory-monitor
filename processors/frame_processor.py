from detectors.helmet_detector import HelmetDetector
from detectors.phone_detector import PhoneDetector
from detectors.fire_detector import FireDetector
from detectors.smoking_detector import SmokingDetector

from detectors.pose_detector import PoseDetector
from processors.pose_processor import PoseProcessor
from processors.pose_matcher import PoseMatcher

from detectors.fall_detector import FallDetector

from engine.sleep_engine import SleepEngine

from app.config import (
    POSE_MODEL_PATH,
    INPUT_SOURCE,
    AFTER_SHIFT_VIDEO_START_TIME,
    AFTER_SHIFT_BASE_DATE,
)

from datetime import datetime, timedelta
import cv2


class FrameProcessor:

    def __init__(

        self,

        tracker,

        zone_drawer,

        person_processor,

        drawing_processor,

        group_processor,

        alert_overlay,

        behaviour,

        orchestrator,

        fps=30.0

    ):

        self.tracker = tracker

        self.zone_drawer = zone_drawer

        self.person_processor = person_processor

        self.drawing_processor = drawing_processor

        self.group_processor = group_processor

        self.alert_overlay = alert_overlay

        self.behaviour = behaviour

        self.orchestrator = orchestrator

        # ------------------------------------------------
        # FPS
        #
        # SleepEngine requires the source FPS in order
        # to calculate its processing stride and timing.
        #
        # Keep 30.0 as a safe backwards-compatible default.
        # ------------------------------------------------

        self.fps = fps

        ##################################################
        # FRAME COUNTER
        #
        # SleepEngine requires the original frame index.
        #
        # IMPORTANT:
        # This counter belongs ONLY to SleepEngine.
        # It does not affect the existing tracker,
        # behaviours, or other detectors.
        ##################################################

        self.frame_idx = 0

        ##################################################
        # Detectors
        #
        # IMPORTANT:
        # Nothing is loaded unless the orchestrator
        # says that module is enabled.
        ##################################################

        self.helmet_detector = None

        self.phone_detector = None

        self.fire_detector = None

        self.smoking_detector = None

        self.pose_detector = None

        self.fall_detector = None

        ##################################################
        # Sleep Engine
        ##################################################

        self.sleep_engine = None
        

        ##################################################
        # AFTER-SHIFT
        ##################################################

        self.after_shift_time_anchor = self._build_video_start_time()

        ##################################################
        # Pose Processing
        ##################################################

        self.pose_processor = None

        self.pose_matcher = None

        ##################################################
        # CONDITIONAL MODEL LOADING
        ##################################################

        # ------------------------------------------------
        # Helmet
        # ------------------------------------------------

        if self.orchestrator.enabled("helmet"):

            print(
                "ORCHESTRATOR -> Loading HELMET model"
            )

            self.helmet_detector = (
                HelmetDetector()
            )

        # ------------------------------------------------
        # Phone
        # ------------------------------------------------

        if self.orchestrator.enabled("phone"):

            print(
                "ORCHESTRATOR -> Loading PHONE model"
            )

            self.phone_detector = (
                PhoneDetector()
            )

        # ------------------------------------------------
        # Fire / Smoke
        #
        # Smoke currently uses the same fire_results.
        # Therefore smoke also requires this detector.
        # ------------------------------------------------

        if self.orchestrator.any_enabled(
            "fire",
            "smoke"
        ):

            print(
                "ORCHESTRATOR -> Loading FIRE/SMOKE model"
            )

            self.fire_detector = (
                FireDetector()
            )

        # ------------------------------------------------
        # Smoking
        # ------------------------------------------------

        if self.orchestrator.enabled("smoking"):

            print(
                "ORCHESTRATOR -> Loading SMOKING model"
            )

            self.smoking_detector = (
                SmokingDetector()
            )

        # ------------------------------------------------
        # Fall
        # ------------------------------------------------

        if self.orchestrator.enabled("fall"):

            print(
                "ORCHESTRATOR -> Loading FALL model"
            )

            self.fall_detector = (
                FallDetector()
            )

        # ------------------------------------------------
        # Pose
        # ------------------------------------------------

        if self.orchestrator.enabled("pose"):

            print(
                "ORCHESTRATOR -> Loading POSE model"
            )

            self.pose_detector = (
                PoseDetector()
            )

            self.pose_processor = (
                PoseProcessor()
            )

            self.pose_matcher = (
                PoseMatcher()
            )

        # ------------------------------------------------
        # Sleep
        #
        # IMPORTANT:
        #
        # Sleep does NOT use sleep_detector.pt.
        #
        # SleepEngine internally uses YOLO pose
        # (yolo11n-pose.pt) and applies the sleep/drowsy
        # posture scoring logic.
        #
        # We pass the absolute project pose-model path
        # instead of just "yolo11n-pose.pt".
        #
        # This prevents Ultralytics from looking in the
        # wrong directory or trying to download another
        # model.
        # ------------------------------------------------

        if self.orchestrator.enabled("sleep"):

            print(
                "ORCHESTRATOR -> Loading SLEEP engine"
            )

            print(
                "SLEEP -> Using pose model:",
                POSE_MODEL_PATH
            )

            self.sleep_engine = SleepEngine(

                src_fps=self.fps,

                model=POSE_MODEL_PATH,

                imgsz=640,

                process_fps=10.0

            )
              

        ##################################################
        # Initialization complete
        ##################################################

        print(
            "========================================"
        )

        print(
            "FRAME PROCESSOR INITIALIZED"
        )

        print(
            "Orchestrator controlled model loading"
        )

        print(
            "Sleep engine:",
            "ENABLED"
            if self.sleep_engine is not None
            else "DISABLED"
        )

        print(
            "========================================"
        )

    ############################################################
    # AFTER-SHIFT TIME HELPERS
    ############################################################

    def _build_video_start_time(self):

        try:
            clock_time = datetime.strptime(
                AFTER_SHIFT_VIDEO_START_TIME,
                "%H:%M:%S"
            ).time()

            base_date = datetime.strptime(
                AFTER_SHIFT_BASE_DATE,
                "%Y-%m-%d"
            ).date()

            return datetime.combine(
                base_date,
                clock_time
            )

        except Exception:

            # Safe fallback for development/testing.
            return datetime.combine(
                datetime.now().date(),
                datetime.strptime(
                    "00:00:00",
                    "%H:%M:%S"
                ).time()
            )

    def _get_frame_time(self, frame_idx):

        # Live sources use real wall-clock time.
        if INPUT_SOURCE in ("webcam", "cctv", "rtsp"):

            return datetime.now()

        # Video files use the configured video-start clock
        # plus the frame timeline.
        return (
            self.after_shift_time_anchor
            +
            timedelta(
                seconds=(
                    frame_idx
                    / max(self.fps, 1e-6)
                )
            )
        )

    ############################################################
    # PROCESS FRAME
    ############################################################

    def process(self, frame):

        current_frame_idx = self.frame_idx

        frame_time = self._get_frame_time(
            current_frame_idx
        )

        ##################################################
        # Person Detection & Tracking
        #
        # This remains CORE infrastructure.
        #
        # We do NOT change this.
        ##################################################

        results = self.tracker.track(
            frame
        )

        result = results[0]

        boxes = result.boxes

        annotated = frame.copy()

        ##################################################
        # TIMESTAMP / SHIFT STATUS
        ##################################################

        if self.orchestrator.enabled("after_shift"):

            shift_state = (
                "AFTER-SHIFT"
                if self.behaviour.after_shift.is_after_shift(
                    frame_time
                )
                else "SHIFT ACTIVE"
            )

            timestamp_text = (
                f"{frame_time.strftime('%d/%m/%Y %H:%M:%S')} | "
                f"SHIFT: {shift_state}"
            )

            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.50
            thickness = 1

            (tw, th), baseline = cv2.getTextSize(
                timestamp_text,
                font,
                font_scale,
                thickness
            )

            pad = 6

            x = max(
                5,
                annotated.shape[1] - tw - (pad * 2) - 5
            )

            y = 10 + th + baseline

            cv2.rectangle(
                annotated,
                (x - pad, 5),
                (
                    x + tw + pad,
                    y + baseline + pad
                ),
                (0, 0, 0),
                -1
            )

            cv2.putText(
                annotated,
                timestamp_text,
                (x, y),
                font,
                font_scale,
                (255, 255, 255),
                thickness,
                cv2.LINE_AA
            )

        ##################################################
        # Object Detection Results
        #
        # Default = None
        ##################################################

        helmet_results = None

        phone_results = None

        fire_results = None

        smoking_results = None

        pose_results = None

        fall_results = None

        ##################################################
        # HELMET MODEL
        ##################################################

        if self.orchestrator.enabled(
            "helmet"
        ):

            helmet_results = (
                self.helmet_detector.detect(
                    frame
                )
            )

        ##################################################
        # PHONE MODEL
        ##################################################

        if self.orchestrator.enabled(
            "phone"
        ):

            phone_results = (
                self.phone_detector.detect(
                    frame
                )
            )

        ##################################################
        # FIRE / SMOKE MODEL
        ##################################################

        if self.orchestrator.any_enabled(
            "fire",
            "smoke"
        ):

            fire_results = (
                self.fire_detector.detect(
                    frame
                )
            )

        ##################################################
        # SMOKING MODEL
        ##################################################

        if self.orchestrator.enabled(
            "smoking"
        ):

            smoking_results = (
                self.smoking_detector.detect(
                    frame
                )
            )

        ##################################################
        # FALL MODEL
        ##################################################

        if self.orchestrator.enabled(
            "fall"
        ):

            fall_results = (
                self.fall_detector.detect(
                    frame
                )
            )

        ##################################################
        # POSE MODEL
        ##################################################

        if self.orchestrator.enabled(
            "pose"
        ):

            pose_results = (
                self.pose_detector.detect(
                    frame
                )
            )

        ##################################################
        # Draw Zones
        ##################################################

        annotated = self.zone_drawer.draw(
            annotated
        )

        ##################################################
        # Person Processing
        ##################################################

        current_people = []

        if boxes.id is not None:

            ids = (
                boxes.id
                .int()
                .cpu()
                .tolist()
            )

            xyxy = (
                boxes.xyxy
                .cpu()
                .tolist()
            )

            ##################################################
            # Update Person Memory
            ##################################################

            for track_id, box in zip(
                ids,
                xyxy
            ):

                person, alerts, draw_box = (
                    self.person_processor.process(

                        track_id,

                        box

                    )
                )

                current_people.append(person)

                if alerts:

                    self.alert_overlay.update(
                        alerts
                    )

                    for alert in alerts:

                        print(alert)

            ##################################################
            # POSE PROCESSING
            #
            # Existing pose workflow remains untouched.
            ##################################################

            if (
                self.orchestrator.enabled("pose")
                and pose_results is not None
                and self.pose_matcher is not None
                and self.pose_processor is not None
            ):

                ##################################################
                # Match pose to tracked people
                ##################################################

                self.pose_matcher.match(

                    self.person_processor
                    .memory
                    .all_people(),

                    pose_results[0]

                )

                ##################################################
                # Process pose
                ##################################################

                self.pose_processor.process(

                    self.person_processor
                    .memory
                    .all_people()

                )

                ##################################################
                # Pose Behaviour
                ##################################################

                for person in (

                    self.person_processor
                    .memory
                    .all_people()
                    .values()

                ):

                    self.behaviour.pose.check(
                        person
                    )

            ##################################################
            # CORE PERSON BEHAVIOURS
            #
            # Existing behaviour workflow remains untouched.
            ##################################################

            # self.person_processor.memory.debug()                     # used only for debug

            for person in (

                self.person_processor
                .memory
                .all_people()
                .values()

            ):

                alerts = (
                    self.behaviour.process(
                        person
                    )
                )

                if alerts:

                    self.alert_overlay.update(
                        alerts
                    )

                    for alert in alerts:

                        print(alert)

            ##################################################
            # Draw Person Information
            ##################################################

            for track_id, box in zip(
                ids,
                xyxy
            ):

                person = (
                    self.person_processor
                    .memory
                    .get(track_id)
                )

                # print(
                #     f"DRAW -> "
                #     f"Track={track_id} | "
                #     f"MemoryID={person['id']} | "
                #     f"Status={person['status']} | "
                #     f"Box={box}"
                # )

                annotated = (
                    self.drawing_processor
                    .draw_person(

                        annotated,

                        box,

                        person

                    )
                )

                ##################################################
                # AFTER-SHIFT PERSON LABEL
                ##################################################

                if (
                    self.orchestrator.enabled("after_shift")
                    and self.behaviour.after_shift.is_active(
                        person["id"]
                    )
                ):

                    x1, y1, x2, y2 = map(
                        int,
                        box
                    )

                    label_y = min(
                        annotated.shape[0] - 8,
                        y2 + 45
                    )

                    cv2.putText(
                        annotated,
                        f"AFTER SHIFT - ID {person['id']}",
                        (x1, label_y),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.45,
                        (0, 0, 255),
                        1,
                        cv2.LINE_AA
                    )

        ##################################################
        # SLEEP ENGINE
        #
        # IMPORTANT:
        #
        # SleepEngine works independently from the existing
        # PersonTracker / PersonMemory pipeline.
        #
        # It has its own YOLO-pose tracker because the
        # colleague's sleep logic contains its own IDMerger,
        # temporal smoothing, posture scoring, and state
        # management.
        #
        # We therefore DO NOT try to force sleep into
        # PersonMemory at this stage.
        #
        # SleepEngine receives the SAME annotated frame.
        #
        # It modifies the frame in-place by drawing:
        #
        #   - skeleton
        #   - person box
        #   - AWAKE
        #   - DROWSY
        #   - SLEEPING
        #
        # It runs inference only every configured stride
        # (8 FPS target), while drawing cached results on
        # intermediate frames.
        ##################################################

        if (
            self.orchestrator.enabled("sleep")
            and self.sleep_engine is not None
        ):

            try:

                self.sleep_engine.process_frame(

                    annotated,

                    self.frame_idx

                )

            except Exception as exc:

                print(
                    "SLEEP ENGINE ERROR ->",
                    repr(exc)
                )

                # ------------------------------------------------
                # IMPORTANT:
                #
                # Do not destroy the complete monitoring pipeline
                # if the sleep engine fails.
                #
                # Existing modules continue to operate.
                # ------------------------------------------------

            finally:

                self.frame_idx += 1

        else:

            # ------------------------------------------------
            # Keep frame numbering synchronized even when
            # sleep is disabled.
            #
            # This means enabling sleep later does not create
            # surprising frame-index behaviour.
            # ------------------------------------------------

            self.frame_idx += 1

        
        
       
        ##################################################
        # AFTER-SHIFT BEHAVIOUR
        #
        # Uses the EXISTING PersonTracker IDs, PersonMemory,
        # and zones.json. No second person tracker is used.
        ##################################################

        if self.orchestrator.enabled(
            "after_shift"
        ):

            after_shift_alerts = (
                self.behaviour.process_after_shift(
                    current_people,
                    frame_time
                )
            )

            if after_shift_alerts:

                self.alert_overlay.update(
                    after_shift_alerts
                )

                for alert in after_shift_alerts:

                    print(alert)

        ##################################################
        # HELMET BEHAVIOUR
        ##################################################

        if (
            self.orchestrator.enabled("helmet")
            and helmet_results is not None
        ):

            helmet_alerts = (
                self.behaviour.process_helmet(

                    self.person_processor
                    .memory
                    .all_people(),

                    helmet_results

                )
            )

            if helmet_alerts:

                self.alert_overlay.update(
                    helmet_alerts
                )

                for alert in helmet_alerts:

                    print(alert)

        ##################################################
        # PHONE BEHAVIOUR
        ##################################################

        if (
            self.orchestrator.enabled("phone")
            and phone_results is not None
        ):

            phone_alerts = (
                self.behaviour.process_phone(

                    self.person_processor
                    .memory
                    .all_people(),

                    phone_results

                )
            )

            if phone_alerts:

                self.alert_overlay.update(
                    phone_alerts
                )

                for alert in phone_alerts:

                    print(alert)

        ##################################################
        # SMOKING BEHAVIOUR
        ##################################################

        if (
            self.orchestrator.enabled("smoking")
            and smoking_results is not None
        ):

            smoking_alerts = (
                self.behaviour.process_smoking(

                    self.person_processor
                    .memory
                    .all_people(),

                    smoking_results

                )
            )

            if smoking_alerts:

                self.alert_overlay.update(
                    smoking_alerts
                )

                for alert in smoking_alerts:

                    print(alert)

        ##################################################
        # FIRE BEHAVIOUR
        ##################################################

        if (
            self.orchestrator.enabled("fire")
            and fire_results is not None
        ):

            fire_alerts = (
                self.behaviour.fire.check(

                    fire_results

                )
            )

            if fire_alerts:

                self.alert_overlay.update(
                    fire_alerts
                )

                for alert in fire_alerts:

                    print(alert)

        ##################################################
        # SMOKE BEHAVIOUR
        #
        # Smoke currently receives fire_results.
        ##################################################

        if (
            self.orchestrator.enabled("smoke")
            and fire_results is not None
        ):

            smoke_alerts = (
                self.behaviour.smoke.check(

                    fire_results

                )
            )

            if smoke_alerts:

                self.alert_overlay.update(
                    smoke_alerts
                )

                for alert in smoke_alerts:

                    print(alert)

        ##################################################
        # FALL BEHAVIOUR
        ##################################################

        if (
            self.orchestrator.enabled("fall")
            and fall_results is not None
        ):

            fall_alerts = (
                self.behaviour.process_fall(
                    fall_results
                )
            )

            if fall_alerts:

                self.alert_overlay.update(
                    fall_alerts
                )

                for alert in fall_alerts:

                    print(alert)

        ##################################################
        # GROUP / SOCIAL BEHAVIOUR
        #
        # Existing workflow intentionally retained.
        ##################################################

        if self.orchestrator.any_enabled(
            "group"
        ):

            group_alerts = (
                self.group_processor.process()
            )

            if group_alerts:

                self.alert_overlay.update(
                    group_alerts
                )

                for alert in group_alerts:

                    print(alert)

        ##################################################
        # ALERT OVERLAY
        ##################################################

        annotated = (
            self.alert_overlay.draw(
                annotated
            )
        )

        return annotated

    ############################################################
    # FINALIZE
    #
    # SleepEngine keeps open state events internally.
    #
    # This method is provided now so the main application can
    # call it later at the end of a video/session.
    #
    # It does NOT affect the current frame-processing workflow.
    ############################################################

    def finalize(self):

        if self.sleep_engine is None:

            return []

        try:

            rows = self.sleep_engine.finalize(
                self.frame_idx
            )

            print(
                "SLEEP ENGINE -> Finalized"
            )

            return rows

        except Exception as exc:

            print(
                "SLEEP ENGINE FINALIZE ERROR ->",
                repr(exc)
            )

            return []