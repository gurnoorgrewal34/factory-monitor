import math


class GroupBehaviour:

    def __init__(self):

        pass

    # ==========================================================
    # MAIN GROUP CLASSIFICATION
    # ==========================================================

    def classify_pair(self, p1, p2):

        id1 = p1.get("id")
        id2 = p2.get("id")

        # ======================================================
        # POSITION
        # ======================================================

        try:

            x1, y1 = p1["current_center"]
            x2, y2 = p2["current_center"]

        except (
            KeyError,
            TypeError,
            ValueError
        ):

            return "Unknown"

        distance = math.hypot(
            x1 - x2,
            y1 - y2
        )

        # ======================================================
        # NOT A GROUP
        # ======================================================

        if distance > 120:

            return "None"

        # ======================================================
        # MOTION
        # ======================================================

        speed1 = float(
            p1.get(
                "avg_speed",
                0.0
            )
        )

        speed2 = float(
            p2.get(
                "avg_speed",
                0.0
            )
        )

        # ======================================================
        # HAND MOVEMENT
        # ======================================================

        hand1 = max(
            float(
                p1.get(
                    "left_hand_speed",
                    0.0
                )
            ),
            float(
                p1.get(
                    "right_hand_speed",
                    0.0
                )
            )
        )

        hand2 = max(
            float(
                p2.get(
                    "left_hand_speed",
                    0.0
                )
            ),
            float(
                p2.get(
                    "right_hand_speed",
                    0.0
                )
            )
        )

        # ======================================================
        # STRONG WORK EVIDENCE
        # ======================================================

        working1 = (
            speed1 > 8
            or
            hand1 >= 8
        )

        working2 = (
            speed2 > 8
            or
            hand2 >= 8
        )

        # ======================================================
        # BOTH ACTIVE
        #
        # Example:
        #
        # workers collaborating around equipment.
        # ======================================================

        if working1 and working2:

            return "Working in Group"

        # ======================================================
        # ONE ACTIVE + ONE STATIONARY
        #
        # Could be:
        #
        # - worker talking to another worker
        # - worker assisting someone
        # - person observing
        #
        # Do NOT call it social loitering.
        # ======================================================

        if working1 or working2:

            return "Group Interaction"

        # ======================================================
        # BOTH STATIONARY
        # ======================================================

        pose1 = str(
            p1.get(
                "pose_state",
                "Unknown"
            )
        ).lower()

        pose2 = str(
            p2.get(
                "pose_state",
                "Unknown"
            )
        ).lower()

        # ======================================================
        # UNKNOWN POSE
        # ======================================================

        if (
            pose1 == "unknown"
            and
            pose2 == "unknown"
        ):

            return "Unknown"

        # ======================================================
        # STANDING GROUP
        # ======================================================

        if (
            pose1 == "standing"
            and
            pose2 == "standing"
        ):

            return "Standing in Group"

        # ======================================================
        # MIXED POSTURES
        # ======================================================

        return "Group Interaction"

    # ==========================================================
    # PROCESS ALL PEOPLE
    # ==========================================================

    def process(self, people):

        groups = []

        person_list = list(
            people.values()
        )

        visited = set()

        for i in range(
            len(person_list)
        ):

            for j in range(
                i + 1,
                len(person_list)
            ):

                p1 = person_list[i]
                p2 = person_list[j]

                id1 = p1.get("id")
                id2 = p2.get("id")

                if (
                    id1 is None
                    or
                    id2 is None
                ):
                    continue

                pair = tuple(
                    sorted(
                        (
                            id1,
                            id2
                        )
                    )
                )

                if pair in visited:
                    continue

                visited.add(pair)

                classification = (
                    self.classify_pair(
                        p1,
                        p2
                    )
                )

                if classification in (
                    "None",
                    "Unknown"
                ):

                    continue

                zone = p1.get(
                    "zone",
                    "Unknown"
                )

                # ==================================================
                # STORE GROUP INFORMATION ON BOTH PEOPLE
                # ==================================================

                p1.setdefault(
                    "group_info",
                    []
                )

                p2.setdefault(
                    "group_info",
                    []
                )

                group_data = {

                    "partner":
                        id2,

                    "zone":
                        zone,

                    "classification":
                        classification
                }

                p1["group_info"].append(
                    group_data
                )

                p2["group_info"].append({

                    "partner":
                        id1,

                    "zone":
                        zone,

                    "classification":
                        classification
                })

                groups.append({

                    "person1":
                        id1,

                    "person2":
                        id2,

                    "zone":
                        zone,

                    "classification":
                        classification
                })

                print(
                    f"GROUP -> "
                    f"Pair=({id1},{id2}) | "
                    f"Zone={zone} | "
                    f"Classification={classification}"
                )

        return groups