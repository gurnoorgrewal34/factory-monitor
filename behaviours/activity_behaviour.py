class ActivityBehaviour:

    def check(self, person):

        speed = float(person.get("avg_speed", 0.0))
        pose = person.get("pose_state", "Unknown")

        print(
            f"ACTIVITY INPUT -> "
            f"ID={person['id']} | "
            f"Pose={pose} | "
            f"Speed={speed:.1f}"
        )

        ####################################################
        # IMPORTANT:
        # Running is NOT decided here.
        #
        # RunningBehaviour is the ONLY component allowed
        # to set status/activity to Running.
        ####################################################

        if pose == "Sitting":

            person["status"] = "Sitting"
            person["activity"] = "Sitting"

        elif pose == "Bending":

            person["status"] = "Bending"
            person["activity"] = "Bending"

        elif pose == "Standing":

            person["status"] = "Standing"
            person["activity"] = "Standing"

        else:

            person["status"] = "Unknown"
            person["activity"] = "Unknown"

        print(
            f"ACTIVITY -> "
            f"{person['id']} | "
            f"Pose={pose} | "
            f"Speed={speed:.1f} | "
            f"Status={person['status']}"
        )