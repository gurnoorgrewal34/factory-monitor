from alerts.alert_manager import AlertManager


class FireBehaviour:

    def __init__(self):

        self.alert_manager = AlertManager()

    ####################################################

    def check(self, fire_results):

        alerts = []

        if len(fire_results) == 0:
            return alerts

        result = fire_results[0]

        if result.boxes is None:
            return alerts

        ####################################################

        for det in result.boxes:

            cls = int(det.cls[0])

            label = result.names[cls]

            if label != "fire":

                continue

            if self.alert_manager.should_alert(

                "GLOBAL",

                "Fire"

            ):

                alerts.append({

                    "type": "Fire",

                    "severity": "CRITICAL"

                })

        return alerts