from detectors.helmet_detector import HelmetDetector
from detectors.phone_detector import PhoneDetector
from detectors.fire_detector import FireDetector
from detectors.smoking_detector import SmokingDetector

from detectors.pose_detector import PoseDetector
from processors.pose_processor import PoseProcessor
from processors.pose_matcher import PoseMatcher


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

        orchestrator

    ):

        self.tracker = tracker

        self.zone_drawer = zone_drawer

        self.person_processor = person_processor

        self.drawing_processor = drawing_processor

        self.group_processor = group_processor

        self.alert_overlay = alert_overlay

        self.behaviour = behaviour

        self.orchestrator = orchestrator

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
        # Fire
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
            "========================================"
        )

    ############################################################
    # PROCESS FRAME
    ############################################################

    def process(self, frame):

        ##################################################
        # Person Detection & Tracking
        #
        # This remains CORE infrastructure.
        #
        # Even if only FIRE is selected, person tracking
        # remains available because the rest of the system
        # depends on PersonMemory / tracked people.
        ##################################################

        results = self.tracker.track(
            frame
        )

        result = results[0]

        boxes = result.boxes

        annotated = frame.copy()

        ##################################################
        # Object Detection Results
        #
        # Default = None
        #
        # A detector only runs when the orchestrator
        # enables it.
        ##################################################

        helmet_results = None

        phone_results = None

        fire_results = None

        smoking_results = None

        pose_results = None

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

                if alerts:

                    self.alert_overlay.update(
                        alerts
                    )

                    for alert in alerts:

                        print(alert)

            ##################################################
            # POSE PROCESSING
            #
            # Only runs when pose is enabled.
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
            # These are your existing behaviours:
            #
            # - Restricted Area
            # - Loitering
            # - Activity
            # - Idle
            # - Running
            #
            # We are leaving them intact for now so we
            # don't accidentally change your current
            # working behaviour logic.
            ##################################################

            self.person_processor.memory.debug()

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

                print(
                    f"DRAW -> "
                    f"Track={track_id} | "
                    f"MemoryID={person['id']} | "
                    f"Status={person['status']} | "
                    f"Box={box}"
                )

                annotated = (
                    self.drawing_processor
                    .draw_person(

                        annotated,

                        box,

                        person

                    )
                )

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
        # GROUP / SOCIAL BEHAVIOUR
        #
        # GroupProcessor currently calls:
        #
        # - GroupBehaviour
        # - GroupStandingBehaviour
        # - SocialLoiteringBehaviour
        #
        # So for now we treat them as one group module.
        ##################################################

        if self.orchestrator.any_enabled(
            "group"):

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