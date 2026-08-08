# from alerts.alert_manager import AlertManager


# class FireBehaviour:

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

#             if label != "fire":

#                 continue

#             if self.alert_manager.should_alert(

#                 "GLOBAL",

#                 "Fire"

#             ):

#                 alerts.append({

#                     "type": "Fire",

#                     "severity": "CRITICAL"

#                 })

#         return alerts




# 2ndversion


class FireBehaviour:

    ####################################################

    def check(self, fire_results):

        alerts = []

        fire_detected = False

        ####################################################
        # No detection result
        ####################################################

        if len(fire_results) == 0:
            return alerts

        result = fire_results[0]

        if result.boxes is None:
            return alerts

        ####################################################
        # Check detections
        ####################################################

        for det in result.boxes:

            cls = int(det.cls[0])

            label = result.names[cls].lower()

            if label == "fire":

                fire_detected = True

                break

        ####################################################
        # Fire currently present
        ####################################################

        if fire_detected:

            alerts.append({

                "type": "Fire",

                "severity": "CRITICAL",

                "persistent": True

            })

        return alerts