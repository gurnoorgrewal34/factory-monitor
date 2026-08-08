from alerts.alert_manager import AlertManager
from app.config import RUNNING_SPEED, RUNNING_FRAME_THRESHOLD


class RunningBehaviour:
    """
    Detects sustained running and raises one alert per running episode.

    Debug output is placed at the actual decision points:
    zone policy -> speed decision -> frame counter -> confirmation -> alert.
    """

    def __init__(self):
        self.alert_manager = AlertManager()

    def check(self, person):
        person_id = person["id"]
        speed = float(person.get("speed", 0.0))
        avg_speed = float(person.get("avg_speed", 0.0))
        running_frames = int(person.get("running_frames", 0))
        running_alerted = bool(person.get("running_alerted", False))

        print(
            f"RUNNING DEBUG -> ID={person_id} | "
            f"Speed={speed:.2f} | AvgSpeed={avg_speed:.2f} | "
            f"Frames={running_frames}/{RUNNING_FRAME_THRESHOLD} | "
            f"Alerted={running_alerted}"
        )

        # --------------------------------------------------
        # Zone Policy
        # --------------------------------------------------
        rules = person.get("zone_rules") or {}
        running_allowed = rules.get("running_allowed", False)

        print(
            f"RUNNING ZONE DEBUG -> ID={person_id} | "
            f"Zone={person.get('zone')} | "
            f"RunningAllowed={running_allowed}"
        )

        if running_allowed is True:
            if running_frames != 0 or running_alerted:
                print(
                    f"RUNNING RESET -> ID={person_id} | "
                    f"Reason=RunningAllowedInZone"
                )

            person["running_frames"] = 0
            person["running_alerted"] = False
            self.alert_manager.clear(person_id, "Running")
            return None

        # --------------------------------------------------
        # Speed Check
        # --------------------------------------------------
        above_threshold = avg_speed >= RUNNING_SPEED

        print(
            f"RUNNING DECISION -> ID={person_id} | "
            f"AvgSpeed={avg_speed:.2f} | Threshold={RUNNING_SPEED} | "
            f"AboveThreshold={above_threshold}"
        )

        if above_threshold:
            person["running_frames"] = running_frames + 1

            print(
                f"RUNNING COUNTER -> ID={person_id} | "
                f"Action=INCREMENT | "
                f"Frames={person['running_frames']}/{RUNNING_FRAME_THRESHOLD}"
            )
        else:
            person["running_frames"] = max(0, running_frames - 1)

            print(
                f"RUNNING COUNTER -> ID={person_id} | "
                f"Action=DECAY | "
                f"Frames={person['running_frames']}/{RUNNING_FRAME_THRESHOLD}"
            )

            if person["running_frames"] == 0:
                if person.get("running_alerted", False):
                    print(
                        f"RUNNING RESET -> ID={person_id} | "
                        f"Reason=CounterReachedZero"
                    )

                person["running_alerted"] = False
                self.alert_manager.clear(person_id, "Running")

            return None

        # --------------------------------------------------
        # Running Confirmation
        # --------------------------------------------------
        threshold_reached = (
            person["running_frames"] >= RUNNING_FRAME_THRESHOLD
        )
        already_alerted = bool(person.get("running_alerted", False))

        print(
            f"RUNNING CONFIRM DEBUG -> ID={person_id} | "
            f"Frames={person['running_frames']} | "
            f"Required={RUNNING_FRAME_THRESHOLD} | "
            f"ThresholdReached={threshold_reached} | "
            f"AlreadyAlerted={already_alerted}"
        )

        if threshold_reached and not already_alerted:
            should_alert = self.alert_manager.should_alert(
                person_id,
                "Running",
            )

            print(
                f"RUNNING ALERT CHECK -> ID={person_id} | "
                f"ShouldAlert={should_alert}"
            )

            if should_alert:
                person["running_alerted"] = True
                person["status"] = "Running"

                print("\n====================================")
                print("RUNNING DETECTED")
                print(f"Person ID : {person_id}")
                print(f"Speed     : {avg_speed:.1f}")
                print(f"Zone      : {person.get('zone')}")
                print(
                    f"Frames    : "
                    f"{person['running_frames']}/{RUNNING_FRAME_THRESHOLD}"
                )
                print("====================================")

                return {
                    "type": "Running",
                    "person_id": person_id,
                    "zone": person.get("zone"),
                    "speed": round(avg_speed, 1),
                    "severity": "HIGH",
                }

        # --------------------------------------------------
        # Already Running
        # --------------------------------------------------
        if person.get("running_alerted", False):
            person["status"] = "Running"

            print(
                f"RUNNING ACTIVE -> ID={person_id} | "
                f"Frames={person['running_frames']} | Status=Running"
            )

        return None