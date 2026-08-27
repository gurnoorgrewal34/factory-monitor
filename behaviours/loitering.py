from app.config import LOITERING_TIME


class LoiteringBehaviour:

    def check(
        self,
        person
    ):

        ####################################################
        # ALREADY ALERTED
        ####################################################

        if person.get(
            "loitering_alerted",
            False
        ):

            return None

        ####################################################
        # TIME IN CURRENT AREA
        #
        # Works even when zone == "Unknown".
        #
        # If a real zone exists, its zone_time is used.
        # If no zone exists, "Unknown" effectively acts as
        # the camera's default/global area.
        ####################################################

        loitering_time = float(
            person.get(
                "zone_time",
                0.0
            )
        )

        ####################################################
        # TIME EXCEEDED
        ####################################################

        if (
            loitering_time
            >=
            LOITERING_TIME
        ):

            person[
                "status"
            ] = "Loitering"

            person[
                "loitering_alerted"
            ] = True

            return {

                "type":
                    "Loitering",

                "person_id":
                    person["id"],

                "zone":
                    person.get(
                        "zone",
                        "Unknown"
                    ),

                "time":
                    round(
                        loitering_time,
                        1
                    ),

                "severity":
                    "MEDIUM"
            }

        return None