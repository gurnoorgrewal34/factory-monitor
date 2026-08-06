from alerts.alert_manager import AlertManager
from utils.geometry import calculate_iou


class HelmetBehaviour:

    def __init__(self):

        self.alert_manager = AlertManager()

    ####################################################

    def check(self, people, helmet_results):

        alerts = []

        if len(helmet_results) == 0:
            return alerts

        result = helmet_results[0]

        if result.boxes is None:
            return alerts

        ####################################################
        # Every detected NO-Hardhat
        ####################################################

        for det in result.boxes:

            cls = int(det.cls[0])

            label = result.names[cls]

            if label != "NO-Hardhat":
                continue

            hx1, hy1, hx2, hy2 = map(int, det.xyxy[0])

            ####################################################
            # Find best matching person
            ####################################################

            best_person = None
            best_iou = 0.0

            for person in people.values():

                iou = calculate_iou(

                    person["box"],

                    [hx1, hy1, hx2, hy2]

                )

                if iou > best_iou:

                    best_iou = iou
                    best_person = person

            ####################################################
            # No matching person
            ####################################################

            IOU_THRESHOLD = 0.10

            if best_person is None or best_iou < IOU_THRESHOLD:

                continue

            ####################################################
            # Zone Policy Check
            ####################################################

            rules = best_person.get("zone_rules", {})

            # Helmet not required in this zone
            if not rules.get("helmet_required", False):

                continue

            ####################################################
            # Raise Alert
            ####################################################

            person_id = best_person["id"]

            if self.alert_manager.should_alert(

                person_id,

                "No Helmet"

            ):

                alerts.append({

                    "type": "No Helmet",

                    "person_id": person_id,

                    "severity": "HIGH",

                    "zone": best_person["zone"]

                })

        return alerts