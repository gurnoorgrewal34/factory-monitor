import time
from app.config import DEBUG

from app.config import (
    STANDING_SPEED,
    STANDING_WITHOUT_WORK_TIME,
    IDLE_TIME
)


class IdleBehaviour:

    def check(self, person):

        current_time = time.time()

        ##################################################
        # Idle behaviour is ONLY for Standing persons
        ##################################################

        if person["pose_state"] != "Standing":

            person["stationary_since"] = None
            person["idle_time"] = 0
            person["idle_alerted"] = False

            return None

        ##################################################
        # Hand movement
        ##################################################

        hand_speed = max(
            person["left_hand_speed"],
            person["right_hand_speed"]
        )

        ##################################################
        # WORKING
        #
        # Person is standing and actively moving hands.
        ##################################################

        if hand_speed >= 5:

            person["stationary_since"] = None
            person["idle_time"] = 0
            person["idle_alerted"] = False

            person["status"] = "Working"
            person["activity"] = "Working"

            print(
                f"IDLE -> "
                f"ID={person['id']} | "
                f"HandSpeed={hand_speed:.1f} | "
                f"Status=Working"
            )

            return None

        ##################################################
        # Stationary
        ##################################################

        stationary = (

            person["avg_speed"] < STANDING_SPEED

            and

            hand_speed < 8
        )

        # debug print
        if DEBUG:
            print(
                f"IDLE DEBUG -> "
                f"ID={person['id']} | "
                f"Body={person['avg_speed']:.1f} | "
                f"LHand={person['left_hand_speed']:.1f} | "
                f"RHand={person['right_hand_speed']:.1f} | "
                f"Stationary={stationary}"
            )
        ##################################################
        # Reset if moving
        ##################################################

        if not stationary:

            person["stationary_since"] = None
            person["idle_time"] = 0
            person["idle_alerted"] = False

            person["status"] = "Standing"
            person["activity"] = "Standing"

            return None

        ##################################################
        # Start Timer
        ##################################################

        if person["stationary_since"] is None:

            person["stationary_since"] = current_time

        ##################################################
        # Stationary Time
        ##################################################

        stationary_time = (
            current_time - person["stationary_since"]
        )

        person["idle_time"] = round(
            stationary_time,
            1
        )

        ##################################################
        # Normal Standing
        ##################################################

        if stationary_time < STANDING_WITHOUT_WORK_TIME:

            person["status"] = "Standing"
            person["activity"] = "Standing"

        ##################################################
        # Standing Without Working
        ##################################################

        elif stationary_time < IDLE_TIME:

            person["status"] = "Standing Without Working"
            person["activity"] = "Standing Without Working"

        ##################################################
        # Idle
        ##################################################

        else:

            person["status"] = "Idle"
            person["activity"] = "Idle"

            if not person["idle_alerted"]:

                person["idle_alerted"] = True

                return {

                    "type": "Idle",

                    "person": person["id"],

                    "message":
                        f"Person {person['id']} "
                        f"has been idle for "
                        f"{int(stationary_time)} sec"

                }

        ##################################################
        # Debug
        ##################################################

        print(
            f"IDLE -> "
            f"ID={person['id']} | "
            f"BodySpeed={person['avg_speed']:.1f} | "
            f"HandSpeed={hand_speed:.1f} | "
            f"Stationary={stationary_time:.1f}s | "
            f"Status={person['status']}"
        )

        return None