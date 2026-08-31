import time

from alerts.alert_manager import (
    AlertManager,
)


class RestrictedAreaBehaviour:

    def __init__(
        self
    ):

        self.alert_manager = (
            AlertManager()
        )


    ##################################################
    # CHECK
    ##################################################

    def check(
        self,
        person,
        is_restricted=False
    ):

        person_id = (
            person.get(
                "id"
            )
        )

        if person_id is None:

            return None


        ##################################################
        # RESTRICTED ZONE NAME
        #
        # Prefer the dedicated restricted-zone metadata.
        #
        # Fall back to normal zone only for compatibility.
        ##################################################

        zone = (
            person.get(
                "restricted_zone"
            )
            or
            person.get(
                "zone"
            )
            or
            "Unknown"
        )


        ##################################################
        # NOT IN RESTRICTED AREA
        ##################################################

        if not is_restricted:

            self.alert_manager.clear(
                person_id,
                "Restricted Area"
            )


            ##################################################
            # Reset entry time
            ##################################################

            person.pop(
                "restricted_enter_time",
                None
            )


            person[
                "restricted_active"
            ] = False


            return None


        ##################################################
        # INSIDE RESTRICTED AREA
        ##################################################

        person[
            "restricted_active"
        ] = True


        current_time = (
            time.time()
        )


        ##################################################
        # FIRST FRAME INSIDE
        ##################################################

        if (
            "restricted_enter_time"
            not in person
        ):

            person[
                "restricted_enter_time"
            ] = current_time


        ##################################################
        # TIME INSIDE
        ##################################################

        restricted_time = (

            current_time
            -
            person[
                "restricted_enter_time"
            ]
        )


        ##################################################
        # DEBUG
        ##################################################

        print(
            "RESTRICTED BEHAVIOUR -> "
            f"ID={person_id} | "
            f"Inside={is_restricted} | "
            f"Zone={zone} | "
            f"Duration={restricted_time:.2f}s"
        )


        ##################################################
        # ALERT
        #
        # Immediate alert once person enters.
        ##################################################

        if (
            self.alert_manager
            .should_alert(
                person_id,
                "Restricted Area"
            )
        ):

            print()

            print(
                "========================================"
            )

            print(
                "RESTRICTED AREA DETECTED"
            )

            print(
                f"Person ID : {person_id}"
            )

            print(
                f"Zone      : {zone}"
            )

            print(
                f"Duration  : {restricted_time:.2f}s"
            )

            print(
                "========================================"
            )


            return {

                "type":
                    "Restricted Area",

                "person_id":
                    person_id,

                "zone":
                    zone,

                "severity":
                    "HIGH",

                "duration":
                    round(
                        restricted_time,
                        2
                    ),

                "message":
                    (
                        f"Person {person_id} "
                        f"entered restricted area "
                        f"{zone}"
                    )
            }


        return None