from alerts.alert_manager import AlertManager
from app.config import RUNNING_SPEED, RUNNING_FRAME_THRESHOLD


class RunningBehaviour:

    def __init__(self):

        self.alert_manager = AlertManager()

    ##################################################

    def check(self, person):

        ##################################################
        # Zone Policy
        ##################################################

        rules = person.get("zone_rules", {})

        # Running is allowed in this zone
        if rules.get("running_allowed", True):

            person["running_frames"] = 0
            person["running_alerted"] = False
            person["status"] = "Normal"

            self.alert_manager.clear(

                person["id"],

                "Running"

            )

            return None

        ##################################################
        # Speed Check
        ##################################################

        if person["avg_speed"] >= RUNNING_SPEED:

            person["running_frames"] += 1

        else:

            # Reduce counter gradually instead of resetting instantly
            person["running_frames"] = max(0, person["running_frames"] - 1)

            if person["running_frames"] == 0:

                person["running_alerted"] = False
                person["status"] = "Normal"

                self.alert_manager.clear(

                    person["id"],

                    "Running"

                )

            return None

        ##################################################
        # Running Confirmed
        ##################################################

        if (

            person["running_frames"] >= RUNNING_FRAME_THRESHOLD

            and not person["running_alerted"]

        ):

            if self.alert_manager.should_alert(

                person["id"],

                "Running"

            ):

                person["running_alerted"] = True
                person["status"] = "Running"

                ##################################################
                # Terminal Debug
                ##################################################

                print("\n====================================")
                print("RUNNING DETECTED")
                print(f"Person ID : {person['id']}")
                print(f"Speed     : {person['avg_speed']:.1f}")
                print(f"Zone      : {person['zone']}")
                print("====================================")

                ##################################################
                # Alert
                ##################################################

                return {

                    "type": "Running",

                    "person_id": person["id"],

                    "zone": person["zone"],

                    "speed": round(person["avg_speed"], 1),

                    "severity": "HIGH"

                }

        ##################################################
        # Already Running
        ##################################################

        if person["running_alerted"]:

            person["status"] = "Running"

        return None