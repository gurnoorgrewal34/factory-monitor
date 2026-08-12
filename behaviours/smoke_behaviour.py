# from alerts.alert_manager import AlertManager


# class SmokeBehaviour:

#     def __init__(self):

#         self.alert_manager = AlertManager()

#     ####################################################

#     def check(self, fire_results):

#         alerts = []

#         if len(fire_results) == 0:
#             return alerts

#         result = fire_results[0]

#         if result.boxes is None:
#             return alerts

#         ####################################################

#         for det in result.boxes:

#             cls = int(det.cls[0])

#             label = result.names[cls]

#             if label != "smoke":

#                 continue

#             if self.alert_manager.should_alert(

#                 "GLOBAL",

#                 "Smoke"

#             ):

#                 alerts.append({

#                     "type": "Smoke",

#                     "severity": "HIGH"

#                 })

#         return alerts




# version2 a on 10 08 2026


from alerts.alert_manager import AlertManager

class SmokeBehaviour:

    def __init__(self):

        self.alert_manager = AlertManager()

        # Minimum confidence required
        self.CONFIDENCE_THRESHOLD = 0.60

        # Smoke must be present for this many
        # consecutive frames before alerting
        self.FRAME_THRESHOLD = 8

        # Consecutive smoke frames
        self.smoke_frames = 0

        # Prevent repeated alerts
        self.alerted = False

    ####################################################

    def check(self, fire_results):

        alerts = []

        smoke_detected = False

        ####################################################
        # No detection result
        ####################################################

        if len(fire_results) == 0:

            self._reset()

            return alerts

        result = fire_results[0]

        if result.boxes is None:

            self._reset()

            return alerts

        ####################################################
        # Check detections
        ####################################################

        for det in result.boxes:

            cls = int(det.cls[0])

            label = result.names[cls].lower()

            confidence = float(det.conf[0])

            ################################################
            # Only smoke
            ################################################

            if label != "smoke":

                continue

            ################################################
            # Confidence filter
            ################################################

            if confidence < self.CONFIDENCE_THRESHOLD:

                print(
                    f"SMOKE FILTER -> "
                    f"Confidence={confidence:.3f} | "
                    f"Required={self.CONFIDENCE_THRESHOLD:.2f}"
                )

                continue

            ################################################
            # Valid smoke detection
            ################################################

            smoke_detected = True

            print(
                f"SMOKE VALID -> "
                f"Confidence={confidence:.3f}"
            )

            break

        ####################################################
        # Consecutive-frame confirmation
        ####################################################

        if smoke_detected:

            self.smoke_frames += 1

        else:

            self._reset()

            return alerts

        ####################################################
        # Confirmation status
        ####################################################

        print(
            f"SMOKE CONFIRM -> "
            f"Frames={self.smoke_frames}/"
            f"{self.FRAME_THRESHOLD} | "
            f"Alerted={self.alerted}"
        )

        ####################################################
        # Raise alert
        ####################################################

        if (

            self.smoke_frames >= self.FRAME_THRESHOLD

            and not self.alerted

        ):

            if self.alert_manager.should_alert(

                "GLOBAL",

                "Smoke"

            ):

                alerts.append({

                    "type": "Smoke",

                    "severity": "HIGH"

                })

                self.alerted = True

        return alerts

    ####################################################

    def _reset(self):

        if self.smoke_frames > 0:

            print(
                f"SMOKE RESET -> "
                f"PreviousFrames={self.smoke_frames}"
            )

        self.smoke_frames = 0

        self.alerted = False

        self.alert_manager.clear(

            "GLOBAL",

            "Smoke"

        )