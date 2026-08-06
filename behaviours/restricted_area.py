from alerts.alert_manager import AlertManager


class RestrictedAreaBehaviour:

    def __init__(self):

        self.alert_manager = AlertManager()

    ####################################################

    def check(self, person):

        person_id = person["id"]

        ####################################################
        # Zone Policy
        ####################################################

        rules = person.get("zone_rules", {})

        # If this zone is NOT restricted, ignore it
        if not rules.get("restricted_access", False):

            self.alert_manager.clear(

                person_id,

                "Restricted Area"

            )

            return None

        ####################################################
        # Restricted Area Alert
        ####################################################

        if self.alert_manager.should_alert(

            person_id,

            "Restricted Area"

        ):

            return {

                "type": "Restricted Area",

                "person_id": person_id,

                "zone": person["zone"],

                "severity": "HIGH"

            }

        return None