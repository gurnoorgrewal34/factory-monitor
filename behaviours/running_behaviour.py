from alerts.alert_manager import AlertManager
from app.config import (
    RUNNING_FRAME_THRESHOLD,
    RUNNING_MOTION_THRESHOLD,
)


class RunningBehaviour:

    def __init__(self):

        self.alert_manager = AlertManager()

    def check(self, person):

        person_id = person["id"]

        motion_speed = float(
            person.get("motion_speed", 0.0)
        )

        avg_motion_speed = float(
            person.get("avg_motion_speed", 0.0)
        )

        running_frames = int(
            person.get("running_frames", 0)
        )

        running_alerted = bool(
            person.get("running_alerted", False)
        )

        # print(
        #     f"RUNNING DEBUG -> "
        #     f"ID={person_id} | "
        #     f"Motion={motion_speed:.3f} | "
        #     f"AvgMotion={avg_motion_speed:.3f} | "
        #     f"Frames={running_frames}/{RUNNING_FRAME_THRESHOLD} | "
        #     f"Alerted={running_alerted}"
        # )

        # ==================================================
        # ZONE POLICY
        # ==================================================

        # rules = person.get("zone_rules") or {}

        # running_allowed = rules.get(
        #     "running_allowed",
        #     False
        # )

        # if running_allowed:

        #     person["running_frames"] = 0
        #     person["running_alerted"] = False

        #     self.alert_manager.clear(
        #         person_id,
        #         "Running"
        #     )

        #     return None

        # ==================================================
        # RUNNING DECISION
        # ==================================================

        above_threshold = (
            avg_motion_speed >= RUNNING_MOTION_THRESHOLD
        )

        # print(
        #     f"RUNNING DECISION -> "
        #     f"ID={person_id} | "
        #     f"AvgMotion={avg_motion_speed:.3f} | "
        #     f"Threshold={RUNNING_MOTION_THRESHOLD:.3f} | "
        #     f"Above={above_threshold}"
        # )

        # ==================================================
        # MOVING FAST ENOUGH
        # ==================================================

        if above_threshold:

            person["running_frames"] = (
                running_frames + 1
            )

            # print(
            #     f"RUNNING COUNTER -> "
            #     f"ID={person_id} | "
            #     f"INCREMENT | "
            #     f"Frames={person['running_frames']}/"
            #     f"{RUNNING_FRAME_THRESHOLD}"
            # )

        # ==================================================
        # NOT MOVING FAST ENOUGH
        # ==================================================

        else:

            person["running_frames"] = max(
                0,
                running_frames - 2
            )

            # print(
            #     f"RUNNING COUNTER -> "
            #     f"ID={person_id} | "
            #     f"DECAY | "
            #     f"Frames={person['running_frames']}/"
            #     f"{RUNNING_FRAME_THRESHOLD}"
            # )

            if person["running_frames"] == 0:

                person["running_alerted"] = False

                self.alert_manager.clear(
                    person_id,
                    "Running"
                )

            return None

        # ==================================================
        # CONFIRM RUNNING
        # ==================================================

        if (
            person["running_frames"]
            >= RUNNING_FRAME_THRESHOLD
            and
            not running_alerted
        ):

            should_alert = (
                self.alert_manager.should_alert(
                    person_id,
                    "Running"
                )
            )

            if should_alert:

                person["running_alerted"] = True

                person["status"] = "Running"
                person["activity"] = "Running"

                print(
                    "\n===================================="
                )
                print("RUNNING DETECTED")
                print(
                    f"Person ID : {person_id}"
                )
                print(
                    f"Motion    : {avg_motion_speed:.3f}"
                )
                print(
                    f"Zone      : {person.get('zone')}"
                )
                print(
                    f"Frames    : "
                    f"{person['running_frames']}/"
                    f"{RUNNING_FRAME_THRESHOLD}"
                )
                print(
                    "===================================="
                )

                return {
                    "type": "Running",
                    "person_id": person_id,
                    "zone": person.get("zone"),
                    "speed": round(
                        avg_motion_speed,
                        3
                    ),
                    "severity": "HIGH",
                }

        # ==================================================
        # ALREADY RUNNING
        # ==================================================

        if person.get("running_alerted", False):

            person["status"] = "Running"
            person["activity"] = "Running"

            # print(
            #     f"RUNNING ACTIVE -> "
            #     f"ID={person_id} | "
            #     f"Frames={person['running_frames']}"
            # )

        return None