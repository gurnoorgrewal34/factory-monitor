from app.config import LOITERING_TIME


class LoiteringBehaviour:

    def check(self, person):

        ####################################################
        # Ignore unknown zone
        ####################################################

        if person["zone"] == "Unknown":
            return None

        ####################################################
        # Zone Policy
        ####################################################

        rules = person.get("zone_rules", {})

        # Loitering is allowed here (Parking, Cafeteria, etc.)
        if rules.get("loitering_allowed", False):
            return None

        ####################################################
        # Already alerted
        ####################################################

        if person.get("loitering_alerted", False):
            return None

        ####################################################
        # Time exceeded
        ####################################################

        if person["zone_time"] >= LOITERING_TIME:

            person["status"] = "Loitering"

            person["loitering_alerted"] = True

            return {

                "type": "Loitering",

                "person_id": person["id"],

                "zone": person["zone"],

                "time": round(person["zone_time"], 1),

                "severity": "MEDIUM"

            }

        return None