# import time
# from app.config import DEBUG

# from app.config import (
#     STANDING_SPEED,
#     STANDING_WITHOUT_WORK_TIME,
#     IDLE_TIME
# )


# class IdleBehaviour:

#     def check(self, person):

#         current_time = time.time()

#         ##################################################
#         # Idle behaviour is ONLY for Standing persons
#         ##################################################

#         if person["pose_state"] != "Standing":

#             person["stationary_since"] = None
#             person["idle_time"] = 0
#             person["idle_alerted"] = False

#             return None

#         ##################################################
#         # Hand movement
#         ##################################################

#         hand_speed = max(
#             person["left_hand_speed"],
#             person["right_hand_speed"]
#         )

#         ##################################################
#         # WORKING
#         #
#         # Person is standing and actively moving hands.
#         ##################################################

#         if hand_speed >= 5:

#             person["stationary_since"] = None
#             person["idle_time"] = 0
#             person["idle_alerted"] = False

#             person["status"] = "Working"
#             person["activity"] = "Working"

#             print(
#                 f"IDLE -> "
#                 f"ID={person['id']} | "
#                 f"HandSpeed={hand_speed:.1f} | "
#                 f"Status=Working"
#             )

#             return None

#         ##################################################
#         # Stationary
#         ##################################################

#         stationary = (

#             person["avg_speed"] < STANDING_SPEED

#             and

#             hand_speed < 8
#         )

#         # debug print
#         if DEBUG:
#             print(
#                 f"IDLE DEBUG -> "
#                 f"ID={person['id']} | "
#                 f"Body={person['avg_speed']:.1f} | "
#                 f"LHand={person['left_hand_speed']:.1f} | "
#                 f"RHand={person['right_hand_speed']:.1f} | "
#                 f"Stationary={stationary}"
#             )
#         ##################################################
#         # Reset if moving
#         ##################################################

#         if not stationary:

#             person["stationary_since"] = None
#             person["idle_time"] = 0
#             person["idle_alerted"] = False

#             person["status"] = "Standing"
#             person["activity"] = "Standing"

#             return None

#         ##################################################
#         # Start Timer
#         ##################################################

#         if person["stationary_since"] is None:

#             person["stationary_since"] = current_time

#         ##################################################
#         # Stationary Time
#         ##################################################

#         stationary_time = (
#             current_time - person["stationary_since"]
#         )

#         person["idle_time"] = round(
#             stationary_time,
#             1
#         )

#         ##################################################
#         # Normal Standing
#         ##################################################

#         if stationary_time < STANDING_WITHOUT_WORK_TIME:

#             person["status"] = "Standing"
#             person["activity"] = "Standing"

#         ##################################################
#         # Standing Without Working
#         ##################################################

#         elif stationary_time < IDLE_TIME:

#             person["status"] = "Standing Without Working"
#             person["activity"] = "Standing Without Working"

#         ##################################################
#         # Idle
#         ##################################################

#         else:

#             person["status"] = "Idle"
#             person["activity"] = "Idle"

#             if not person["idle_alerted"]:

#                 person["idle_alerted"] = True

#                 return {

#                     "type": "Idle",

#                     "person": person["id"],

#                     "message":
#                         f"Person {person['id']} "
#                         f"has been idle for "
#                         f"{int(stationary_time)} sec"

#                 }

#         ##################################################
#         # Debug
#         ##################################################

#         print(
#             f"IDLE -> "
#             f"ID={person['id']} | "
#             f"BodySpeed={person['avg_speed']:.1f} | "
#             f"HandSpeed={hand_speed:.1f} | "
#             f"Stationary={stationary_time:.1f}s | "
#             f"Status={person['status']}"
#         )

#         return None





# changes on 01/09/26
import time

from app.config import (
    DEBUG,
    STANDING_SPEED,
    STANDING_WITHOUT_WORK_TIME,
    IDLE_TIME,
    HAND_WORKING_SPEED,
)


class IdleBehaviour:

    def check(
        self,
        person
    ):

        person_id = person.get(
            "id"
        )

        # ==================================================
        # TIME
        #
        # PersonMemory already stores last_seen using:
        #
        # - video timeline for prerecorded videos
        # - real timestamp for live sources
        #
        # Therefore use the same timeline here.
        # ==================================================

        current_time = float(
            person.get(
                "last_seen",
                time.time()
            )
        )

        # ==================================================
        # POSE
        # ==================================================

        pose_state = str(
            person.get(
                "pose_state",
                "UNKNOWN"
            )
        )

        # ==================================================
        # BODY MOVEMENT
        #
        # IMPORTANT:
        #
        # Do NOT use avg_speed here.
        #
        # avg_speed = pixels / second
        #
        # avg_frame_displacement =
        # smoothed movement between source frames.
        # ==================================================

        body_speed = float(
            person.get(
                "avg_frame_displacement",
                person.get(
                    "avg_speed",
                    0.0
                )
            )
        )

        # ==================================================
        # HAND MOVEMENT
        # ==================================================

        left_hand_speed = float(
            person.get(
                "left_hand_speed",
                0.0
            )
        )

        right_hand_speed = float(
            person.get(
                "right_hand_speed",
                0.0
            )
        )

        hand_speed = max(
            left_hand_speed,
            right_hand_speed
        )

        # ==================================================
        # DEBUG INPUT
        # ==================================================

        if DEBUG:

            print(
                f"\nIDLE INPUT -> "
                f"ID={person_id} | "
                f"Pose={pose_state} | "
                f"FrameMove={body_speed:.2f} | "
                f"LHand={left_hand_speed:.2f} | "
                f"RHand={right_hand_speed:.2f} | "
                f"Timer={person.get('idle_time', 0)}"
            )

        # ==================================================
        # POSE VALIDATION
        #
        # A person must genuinely be Standing.
        #
        # IMPORTANT:
        #
        # UNKNOWN is NOT treated as Standing.
        #
        # Pose must be provided correctly by the runtime
        # dependency/orchestration pipeline.
        # ==================================================

        if (
            pose_state.lower()
            !=
            "standing"
        ):

            if DEBUG:

                print(
                    f"IDLE RESET -> "
                    f"ID={person_id} | "
                    f"REASON=POSE | "
                    f"Pose={pose_state}"
                )

            person[
                "stationary_since"
            ] = None

            person[
                "idle_time"
            ] = 0.0

            person[
                "idle_alerted"
            ] = False

            return None

        # ==================================================
        # ACTIVE HAND MOVEMENT
        #
        # Standing + significant hand movement means the
        # person is currently working.
        # ==================================================

        if (
            hand_speed
            >=
            HAND_WORKING_SPEED
        ):

            if DEBUG:

                print(
                    f"IDLE RESET -> "
                    f"ID={person_id} | "
                    f"REASON=HAND_MOVEMENT | "
                    f"Hand={hand_speed:.2f}"
                )

            person[
                "stationary_since"
            ] = None

            person[
                "idle_time"
            ] = 0.0

            person[
                "idle_alerted"
            ] = False

            person[
                "status"
            ] = "Working"

            person[
                "activity"
            ] = "Working"

            return None

        # ==================================================
        # STATIONARY CHECK
        #
        # Body must be below the standing movement threshold
        # AND hands must not indicate active work.
        # ==================================================

        stationary = (

            body_speed
            <
            STANDING_SPEED

            and

            hand_speed
            <
            HAND_WORKING_SPEED
        )

        # ==================================================
        # DEBUG
        # ==================================================

        if DEBUG:

            print(
                f"IDLE DEBUG -> "
                f"ID={person_id} | "
                f"Pose={pose_state} | "
                f"FrameMove={body_speed:.2f} | "
                f"Hand={hand_speed:.2f} | "
                f"Stationary={stationary}"
            )

        # ==================================================
        # PERSON IS MOVING
        # ==================================================

        if not stationary:

            if DEBUG:

                print(
                    f"IDLE RESET -> "
                    f"ID={person_id} | "
                    f"REASON=MOVEMENT | "
                    f"FrameMove={body_speed:.2f}"
                )

            person[
                "stationary_since"
            ] = None

            person[
                "idle_time"
            ] = 0.0

            person[
                "idle_alerted"
            ] = False

            person[
                "status"
            ] = "Standing"

            person[
                "activity"
            ] = "Standing"

            return None

        # ==================================================
        # START STATIONARY TIMER
        #
        # Only start once.
        # ==================================================

        if (
            person.get(
                "stationary_since"
            )
            is None
        ):

            person[
                "stationary_since"
            ] = current_time

            if DEBUG:

                print(
                    f"IDLE TIMER -> "
                    f"ID={person_id} | "
                    f"START"
                )

        # ==================================================
        # STATIONARY DURATION
        # ==================================================

        stationary_time = (
            current_time
            -
            person[
                "stationary_since"
            ]
        )

        # Protection against an unexpected timestamp issue.
        if stationary_time < 0:

            person[
                "stationary_since"
            ] = current_time

            stationary_time = 0.0

        person[
            "idle_time"
        ] = round(
            stationary_time,
            1
        )

        # ==================================================
        # NORMAL STANDING
        # ==================================================

        if (
            stationary_time
            <
            STANDING_WITHOUT_WORK_TIME
        ):

            person[
                "status"
            ] = "Standing"

            person[
                "activity"
            ] = "Standing"

        # ==================================================
        # STANDING WITHOUT WORKING
        # ==================================================

        elif (
            stationary_time
            <
            IDLE_TIME
        ):

            person[
                "status"
            ] = (
                "Standing Without Working"
            )

            person[
                "activity"
            ] = (
                "Standing Without Working"
            )

        # ==================================================
        # IDLE
        # ==================================================

        else:

            person[
                "status"
            ] = "Idle"

            person[
                "activity"
            ] = "Idle"

            # Generate one alert for this idle episode.
            if not person.get(
                "idle_alerted",
                False
            ):

                person[
                    "idle_alerted"
                ] = True

                if DEBUG:

                    print(
                        f"IDLE ALERT -> "
                        f"ID={person_id} | "
                        f"Time={stationary_time:.1f}s"
                    )

                return {

                    "type":
                        "Idle",

                    "person":
                        person_id,

                    "message":
                        (
                            f"Person {person_id} "
                            f"has been idle for "
                            f"{int(stationary_time)} sec"
                        )
                }

        # ==================================================
        # DEBUG TIMER
        # ==================================================

        if DEBUG:

            print(
                f"IDLE TIMER -> "
                f"ID={person_id} | "
                f"Time={stationary_time:.1f}s | "
                f"FrameMove={body_speed:.2f} | "
                f"Pose={pose_state} | "
                f"Status={person['status']}"
            )

        return None