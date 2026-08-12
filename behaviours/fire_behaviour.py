from collections import deque
import math

from alerts.alert_manager import AlertManager

from app.config import (
    FIRE_BEHAVIOUR_CONFIDENCE,
)


class FireBehaviour:

    def __init__(self):

        self.alert_manager = AlertManager()

        # ---------------------------------------------
        # Fire confidence
        # ---------------------------------------------

        self.MIN_CONFIDENCE = FIRE_BEHAVIOUR_CONFIDENCE

        # ---------------------------------------------
        # Temporal confirmation
        # ---------------------------------------------

        self.WINDOW_SIZE = 15

        # 10 valid frames out of last 15
        # required to CONFIRM fire.
        self.MIN_VALID_FRAMES = 10

        # ---------------------------------------------
        # Clear confirmation
        # ---------------------------------------------

        # After an alert is active, require this many
        # consecutive frames WITHOUT valid fire before
        # clearing the alert.
        self.CLEAR_FRAMES = 5

        self.no_fire_frames = 0

        # ---------------------------------------------
        # Spatial confirmation
        # ---------------------------------------------

        self.MAX_CENTER_DISTANCE = 120

        # ---------------------------------------------
        # State
        # ---------------------------------------------

        self.history = deque(
            maxlen=self.WINDOW_SIZE
        )

        self.previous_center = None

        self.alerted = False

    # =================================================
    # MAIN CHECK
    # =================================================

    def check(self, fire_results):

        alerts = []

        detection = self._get_fire_detection(
            fire_results
        )

        # ---------------------------------------------
        # No valid fire detection
        # ---------------------------------------------

        if detection is None:

            self.history.append({
                "valid": False,
                "confidence": 0.0,
                "center": None
            })

            self.no_fire_frames += 1

            print(
                f"FIRE EVIDENCE -> "
                f"No valid fire detection | "
                f"NoFireFrames={self.no_fire_frames}/"
                f"{self.CLEAR_FRAMES}"
            )

            # -----------------------------------------
            # Clear active fire alert
            # -----------------------------------------

            if (
                self.alerted
                and self.no_fire_frames >= self.CLEAR_FRAMES
            ):

                print(
                    "🔥 FIRE CLEARED -> "
                    "No valid fire detected"
                )

                self.alerted = False

                self.alert_manager.clear(
                    "GLOBAL",
                    "Fire"
                )

                self.previous_center = None

                # Start a fresh confirmation window
                self.history.clear()

            return self._evaluate(alerts)

        # ---------------------------------------------
        # Valid fire detection
        # ---------------------------------------------

        confidence = detection["confidence"]
        center = detection["center"]

        # Fire exists again
        self.no_fire_frames = 0

        # ---------------------------------------------
        # Spatial consistency
        # ---------------------------------------------

        spatial_ok = True

        if self.previous_center is not None:

            distance = math.sqrt(
                (
                    center[0]
                    - self.previous_center[0]
                ) ** 2
                +
                (
                    center[1]
                    - self.previous_center[1]
                ) ** 2
            )

            spatial_ok = (
                distance
                <= self.MAX_CENTER_DISTANCE
            )

            print(
                f"FIRE SPATIAL -> "
                f"Distance={distance:.1f} | "
                f"Limit={self.MAX_CENTER_DISTANCE} | "
                f"OK={spatial_ok}"
            )

        self.previous_center = center

        # ---------------------------------------------
        # Valid fire evidence
        # ---------------------------------------------

        valid = (
            confidence >= self.MIN_CONFIDENCE
            and spatial_ok
        )

        self.history.append({
            "valid": valid,
            "confidence": confidence,
            "center": center
        })

        print(
            f"FIRE EVIDENCE -> "
            f"Confidence={confidence:.3f} | "
            f"Spatial={spatial_ok} | "
            f"Valid={valid}"
        )

        return self._evaluate(alerts)

    # =================================================
    # GET BEST FIRE DETECTION
    # =================================================

    def _get_fire_detection(self, fire_results):

        if not fire_results:
            return None

        result = fire_results[0]

        if (
            result.boxes is None
            or len(result.boxes) == 0
        ):
            return None

        best = None

        for det in result.boxes:

            cls = int(det.cls[0])

            label = (
                result.names[cls]
                .lower()
                .strip()
            )

            confidence = float(
                det.conf[0]
            )

            print(
                f"FIRE CHECK -> "
                f"Label={label} | "
                f"Confidence={confidence:.3f} | "
                f"Required={self.MIN_CONFIDENCE:.2f}"
            )

            # -----------------------------------------
            # ONLY FIRE
            # -----------------------------------------

            if label != "fire":
                continue

            # -----------------------------------------
            # Confidence filter
            # -----------------------------------------

            if confidence < self.MIN_CONFIDENCE:
                continue

            # -----------------------------------------
            # Bounding box center
            # -----------------------------------------

            x1, y1, x2, y2 = (
                det.xyxy[0].tolist()
            )

            center = (
                (x1 + x2) / 2,
                (y1 + y2) / 2
            )

            # -----------------------------------------
            # Keep highest-confidence fire
            # -----------------------------------------

            if (
                best is None
                or confidence > best["confidence"]
            ):

                best = {
                    "confidence": confidence,
                    "center": center
                }

        return best

    # =================================================
    # FINAL DECISION
    # =================================================

    def _evaluate(self, alerts):

        valid_frames = sum(
            1
            for item in self.history
            if item["valid"]
        )

        total_frames = len(self.history)

        print(
            f"FIRE WINDOW -> "
            f"Valid={valid_frames}/"
            f"{total_frames} | "
            f"Required={self.MIN_VALID_FRAMES}/"
            f"{self.WINDOW_SIZE} | "
            f"Alerted={self.alerted}"
        )

        # ---------------------------------------------
        # Need a full window before making a decision
        # ---------------------------------------------

        if total_frames < self.WINDOW_SIZE:
            return alerts

        # ---------------------------------------------
        # FIRE IS CURRENTLY CONFIRMED
        # ---------------------------------------------

        if valid_frames >= self.MIN_VALID_FRAMES:

            if not self.alerted:

                if self.alert_manager.should_alert(
                    "GLOBAL",
                    "Fire"
                ):

                    print(
                        "🔥 FIRE CONFIRMED"
                    )

                    alerts.append({

                        "type": "Fire",

                        "severity": "CRITICAL",

                        "persistent": True

                    })

                    self.alerted = True

            return alerts

        # ---------------------------------------------
        # FIRE IS NO LONGER CONFIRMED
        # ---------------------------------------------

        if self.alerted:

            print(
                "🔥 FIRE CLEARED -> "
                f"Valid={valid_frames}/"
                f"{self.WINDOW_SIZE}"
            )

        self.alerted = False

        self.alert_manager.clear(
            "GLOBAL",
            "Fire"
        )

        return alerts