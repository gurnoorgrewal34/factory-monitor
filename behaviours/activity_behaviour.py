from app.config import RUNNING_SPEED


class ActivityBehaviour:

    def check(self, person):

        speed = person["avg_speed"]
        pose = person.get("pose_state", "Unknown")

        print(
            f"ACTIVITY INPUT -> "
            f"ID={person['id']} | "
            f"Pose={pose} | "
            f"Speed={speed:.1f}"
        )

        ####################################################
        # Running
        ####################################################

        if speed >= RUNNING_SPEED:

            person["status"] = "Running"
            person["activity"] = "Running"

        ####################################################
        # Sitting
        ####################################################

        elif pose == "Sitting":

            person["status"] = "Sitting"
            person["activity"] = "Sitting"

        ####################################################
        # Bending
        ####################################################

        elif pose == "Bending":

            person["status"] = "Bending"
            person["activity"] = "Bending"

        ####################################################
        # Standing
        ####################################################

        elif pose == "Standing":

            # Let IdleBehaviour decide whether this person
            # is standing, standing without working, or idle.

            person["status"] = "Standing"
            person["activity"] = "Standing"

        ####################################################
        # Unknown
        ####################################################

        else:

            person["status"] = "Unknown"
            person["activity"] = "Unknown"

        ####################################################
        # Debug
        ####################################################

        print(
            f"ACTIVITY -> "
            f"{person['id']} | "
            f"Pose={pose} | "
            f"Speed={speed:.1f} | "
            f"Status={person['status']}"
        )