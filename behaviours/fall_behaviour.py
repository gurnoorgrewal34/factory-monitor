from collections import deque

from alerts.alert_manager import AlertManager


class FallBehaviour:

    def __init__(self):

        self.alert_manager = AlertManager()

        # =================================================
        # MODEL CONFIDENCE
        # =================================================

        self.MIN_CONFIDENCE = 0.40

        # =================================================
        # TEMPORAL CONFIRMATION
        #
        # We don't want one bad frame to trigger a fall.
        #
        # 3 valid fallen detections inside the last 5 frames
        # will confirm the fall.
        # =================================================

        self.WINDOW_SIZE = 5

        self.MIN_VALID_FRAMES = 3

        # =================================================
        # CLEAR CONFIRMATION
        #
        # Once fall is active, require several consecutive
        # frames without "fallen" before clearing it.
        # =================================================

        self.CLEAR_FRAMES = 8

        self.no_fall_frames = 0

        # =================================================
        # STATE
        # =================================================

        self.history = deque(
            maxlen=self.WINDOW_SIZE
        )

        self.alerted = False

    # =====================================================
    # MAIN CHECK
    # =====================================================

    def check(self, fall_results):

        alerts = []

        detection = self._get_fallen_detection(
            fall_results
        )

        # =================================================
        # NO FALLEN PERSON
        # =================================================

        if detection is None:

            self.history.append(False)

            self.no_fall_frames += 1

            print(
                f"FALL EVIDENCE -> "
                f"No fallen person | "
                f"NoFallFrames="
                f"{self.no_fall_frames}/"
                f"{self.CLEAR_FRAMES}"
            )

            # ---------------------------------------------
            # Clear active alert
            # ---------------------------------------------

            if (
                self.alerted
                and
                self.no_fall_frames >= self.CLEAR_FRAMES
            ):

                print(
                    "⚠️ FALL CLEARED -> "
                    "No fallen person detected"
                )

                self.alerted = False

                self.alert_manager.clear(
                    "GLOBAL",
                    "Fall"
                )

                self.history.clear()

            return self._evaluate(
                alerts
            )

        # =================================================
        # VALID FALLEN DETECTION
        # =================================================

        confidence = detection["confidence"]

        self.no_fall_frames = 0

        valid = (
            confidence >= self.MIN_CONFIDENCE
        )

        self.history.append(
            valid
        )

        print(
            f"FALL EVIDENCE -> "
            f"Label=fallen | "
            f"Confidence={confidence:.3f} | "
            f"Valid={valid}"
        )

        return self._evaluate(
            alerts
        )

    # =====================================================
    # FIND FALLEN PERSON
    # =====================================================

    def _get_fallen_detection(
        self,
        fall_results
    ):

        if not fall_results:

            return None

        result = fall_results[0]

        if (
            result.boxes is None
            or len(result.boxes) == 0
        ):

            return None

        best = None

        # =================================================
        # CHECK ALL DETECTIONS
        # =================================================

        for det in result.boxes:

            cls_id = int(
                det.cls[0]
            )

            confidence = float(
                det.conf[0]
            )

            label = (
                result.names[cls_id]
                .lower()
                .strip()
            )

            print(
                f"FALL CHECK -> "
                f"Label={label} | "
                f"Confidence={confidence:.3f}"
            )

            # ------------------------------------------------
            # IMPORTANT:
            #
            # sitting != fall
            # standing != fall
            #
            # ONLY "fallen" is considered a fall.
            # ------------------------------------------------

            if label != "fallen":

                continue

            if confidence < self.MIN_CONFIDENCE:

                continue

            # ------------------------------------------------
            # Keep highest confidence fallen detection
            # ------------------------------------------------

            if (
                best is None
                or
                confidence > best["confidence"]
            ):

                best = {
                    "confidence": confidence
                }

        return best

    # =====================================================
    # FINAL DECISION
    # =====================================================

    def _evaluate(
        self,
        alerts
    ):

        valid_frames = sum(
            1
            for item in self.history
            if item
        )

        total_frames = len(
            self.history
        )

        print(
            f"FALL WINDOW -> "
            f"Valid={valid_frames}/"
            f"{total_frames} | "
            f"Required={self.MIN_VALID_FRAMES}/"
            f"{self.WINDOW_SIZE} | "
            f"Alerted={self.alerted}"
        )

        # =================================================
        # Need enough history
        # =================================================

        if total_frames < self.WINDOW_SIZE:

            return alerts

        # =================================================
        # FALL CONFIRMED
        # =================================================

        if valid_frames >= self.MIN_VALID_FRAMES:

            if not self.alerted:

                if self.alert_manager.should_alert(
                    "GLOBAL",
                    "Fall"
                ):

                    print(
                        "🚨 FALL CONFIRMED"
                    )

                    alerts.append({

                        "type": "Fall",

                        "severity": "CRITICAL",

                        "persistent": True

                    })

                    self.alerted = True

            return alerts

        # =================================================
        # FALL NO LONGER CONFIRMED
        # =================================================

        if self.alerted:

            print(
                "⚠️ FALL CLEARED -> "
                f"Valid={valid_frames}/"
                f"{self.WINDOW_SIZE}"
            )

        self.alerted = False

        self.alert_manager.clear(
            "GLOBAL",
            "Fall"
        )

        return alerts