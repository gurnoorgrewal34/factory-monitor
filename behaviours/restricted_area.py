# from alerts.alert_manager import AlertManager
# import time


# class RestrictedAreaBehaviour:

#     def __init__(self):

#         self.alert_manager = AlertManager()

#     ####################################################
#     # CHECK
#     ####################################################

#     def check(self, person):

#         person_id = person["id"]

#         ####################################################
#         # Zone Policy
#         ####################################################

#         rules = person.get(
#             "zone_rules",
#             {}
#         )

#         ####################################################
#         # If zone is NOT restricted
#         ####################################################

#         if not rules.get(
#             "restricted_access",
#             False
#         ):

#             self.alert_manager.clear(

#                 person_id,

#                 "Restricted Area"

#             )

#             # Reset restricted timer
#             person.pop(
#                 "restricted_enter_time",
#                 None
#             )

#             return None

#         ####################################################
#         # Restricted zone
#         ####################################################

#         current_time = time.time()

#         ####################################################
#         # First frame inside restricted zone
#         ####################################################

#         if "restricted_enter_time" not in person:

#             person["restricted_enter_time"] = current_time

#         ####################################################
#         # Time spent inside restricted zone
#         ####################################################

#         restricted_time = (
#             current_time
#             -
#             person["restricted_enter_time"]
#         )

#         ####################################################
#         # Maximum allowed time
#         #
#         # Default = 0
#         #
#         # This means:
#         # immediately restricted.
#         ####################################################

#         max_allowed_time = float(
#             rules.get(
#                 "restricted_max_seconds",
#                 0
#             )
#         )

#         ####################################################
#         # Still within allowed time
#         ####################################################

#         if restricted_time < max_allowed_time:

#             return None

#         ####################################################
#         # Alert
#         ####################################################

#         if self.alert_manager.should_alert(

#             person_id,

#             "Restricted Area"

#         ):

#             return {

#                 "type": "Restricted Area",

#                 "person_id": person_id,

#                 "zone": person["zone"],

#                 "severity": "HIGH",

#                 "duration": round(
#                     restricted_time,
#                     2
#                 )

#             }

#         return None



# new  version for cmaera s without zzones
# from alerts.alert_manager import AlertManager
# import time


# class RestrictedAreaBehaviour:

#     def __init__(self):

#         self.alert_manager = (
#             AlertManager()
#         )

#     ####################################################
#     # CHECK
#     ####################################################

#     def check(
#         self,
#         person,
#         is_restricted=False
#     ):

#         person_id = (
#             person["id"]
#         )

#         ####################################################
#         # NOT INSIDE RESTRICTED ZONE
#         ####################################################

#         if not is_restricted:

#             self.alert_manager.clear(

#                 person_id,

#                 "Restricted Area"
#             )

#             person.pop(
#                 "restricted_enter_time",
#                 None
#             )

#             return None

#         ####################################################
#         # INSIDE RESTRICTED ZONE
#         ####################################################

#         current_time = (
#             time.time()
#         )

#         if (
#             "restricted_enter_time"
#             not in person
#         ):

#             person[
#                 "restricted_enter_time"
#             ] = current_time

#         restricted_time = (

#             current_time
#             -
#             person[
#                 "restricted_enter_time"
#             ]
#         )

#         ####################################################
#         # IMMEDIATE RESTRICTION
#         #
#         # No user-configured zone rule/timer required.
#         ####################################################

#         max_allowed_time = 0.0

#         if (
#             restricted_time
#             <
#             max_allowed_time
#         ):

#             return None

#         ####################################################
#         # ALERT
#         ####################################################

#         if (
#             self.alert_manager
#             .should_alert(

#                 person_id,

#                 "Restricted Area"
#             )
#         ):

#             return {

#                 "type":
#                     "Restricted Area",

#                 "person_id":
#                     person_id,

#                 "zone":
#                     person.get(
#                         "zone",
#                         "Unknown"
#                     ),

#                 "severity":
#                     "HIGH",

#                 "duration":
#                     round(
#                         restricted_time,
#                         2
#                     )
#             }

#         return None





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


    def check(
        self,
        person
    ):

        person_id = (
            person["id"]
        )

        zone = person.get(
            "zone",
            "Unknown"
        )

        zone_type = (
            person.get(
                "zone_type"
            )
        )


        ##################################################
        # NOT IN RESTRICTED AREA
        ##################################################

        if zone_type != "restricted":

            self.alert_manager.clear(
                person_id,
                "Restricted Area"
            )

            return None


        ##################################################
        # RESTRICTED AREA
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
                f"Zone Type : {zone_type}"
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

                "message":
                    (
                        f"Person {person_id} "
                        f"entered restricted area "
                        f"{zone}"
                    )
            }


        return None