from alerts.alert_manager import AlertManager
from utils.geometry import calculate_iou


class SmokingBehaviour:

    def __init__(self):

        self.alert_manager = AlertManager()

    ##################################################

    def check(self, people, smoking_results):

        alerts = []

        if len(smoking_results) == 0:
            return alerts

        result = smoking_results[0]

        if result.boxes is None:
            return alerts

        ##################################################

        for det in result.boxes:

            cls = int(det.cls[0])

            label = result.names[cls]

            if label != "cigarette":
                continue

            sx1, sy1, sx2, sy2 = map(int, det.xyxy[0])

            best_person = None
            best_iou = 0

            for person in people.values():

                iou = calculate_iou(

                    person["box"],

                    [sx1, sy1, sx2, sy2]

                )

                if iou > best_iou:

                    best_iou = iou
                    best_person = person

            ##################################################

            if best_person is None or best_iou < 0.01:
                continue

            ##################################################
            # Zone Policy
            ##################################################

            rules = best_person.get("zone_rules", {})

            # Smoking allowed here
            if rules.get("smoking_allowed", False):
                continue

            ##################################################

            person_id = best_person["id"]

            if self.alert_manager.should_alert(

                person_id,

                "Smoking"

            ):

                alerts.append({

                    "type": "Smoking",

                    "person_id": person_id,

                    "zone": best_person["zone"],

                    "severity": "HIGH"

                })

        return alerts