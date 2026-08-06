from alerts.alert_manager import AlertManager
from utils.geometry import calculate_iou


class PhoneBehaviour:

    def __init__(self):

        self.alert_manager = AlertManager()

        # Number of consecutive frames required
        self.FRAME_THRESHOLD = 20

    ####################################################

    def check(self, people, phone_results):

        alerts = []

        # Reset detection flag
        for person in people.values():

            person["phone_detected"] = False

        ####################################################
        # No detections
        ####################################################

        if len(phone_results) == 0:

            self.reset_people(people)

            return alerts

        result = phone_results[0]

        if result.boxes is None:

            self.reset_people(people)

            return alerts

        ####################################################
        # Process every phone detection
        ####################################################

        for det in result.boxes:

            cls = int(det.cls[0])

            label = result.names[cls]

            if label != "mobile_phone":

                continue

            px1, py1, px2, py2 = map(int, det.xyxy[0])

            best_person = None
            best_iou = 0.0

            ####################################################
            # IoU Matching
            ####################################################

            for person in people.values():

                iou = calculate_iou(

                    person["box"],

                    [px1, py1, px2, py2]

                )

                if iou > best_iou:

                    best_iou = iou
                    best_person = person

            ####################################################
            # Ignore weak IoU matches
            ####################################################

            if best_person is None or best_iou < 0.10:

                continue

            ####################################################
            # Zone Policy
            ####################################################

            rules = best_person.get("zone_rules", {})

            # If phone usage is allowed in this zone,
            # ignore this detection completely.
            if rules.get("phone_allowed", True):

                continue

            ####################################################
            # Valid phone detection
            ####################################################

            best_person["phone_detected"] = True

        ####################################################
        # Update frame counters
        ####################################################

        for person in people.values():

            if person["phone_detected"]:

                person["phone_frames"] += 1

            else:

                person["phone_frames"] = 0

                person["phone_alerted"] = False

                self.alert_manager.clear(

                    person["id"],

                    "Phone Usage"

                )

            ####################################################
            # Raise alert after threshold
            ####################################################

            if (

                person["phone_frames"] >= self.FRAME_THRESHOLD

                and not person["phone_alerted"]

            ):

                if self.alert_manager.should_alert(

                    person["id"],

                    "Phone Usage"

                ):

                    alerts.append({

                        "type": "Phone Usage",

                        "person_id": person["id"],

                        "severity": "MEDIUM",

                        "zone": person["zone"]

                    })

                    person["phone_alerted"] = True

        return alerts

    ####################################################

    def reset_people(self, people):

        for person in people.values():

            person["phone_frames"] = 0

            person["phone_alerted"] = False

            self.alert_manager.clear(

                person["id"],

                "Phone Usage"

            )