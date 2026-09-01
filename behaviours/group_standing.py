import math
import time

from app.config import (
    GROUP_DISTANCE,
    GROUP_TIME,
    GROUP_SPEED,
)


class GroupStandingBehaviour:

    def __init__(self):

        # --------------------------------------------------
        # group_key -> time when group became stable
        # --------------------------------------------------

        self.group_history = {}

        # --------------------------------------------------
        # group_key -> alert already generated
        # --------------------------------------------------

        self.alerted_groups = set()

    # ======================================================
    # DISTANCE
    # ======================================================

    def _distance(self, p1, p2):

        try:

            x1, y1 = p1["current_center"]
            x2, y2 = p2["current_center"]

        except (KeyError, TypeError, ValueError):

            return None

        return math.hypot(
            x1 - x2,
            y1 - y2
        )

    # ======================================================
    # HAND SPEED
    # ======================================================

    def _hand_speed(self, person):

        left = float(
            person.get(
                "left_hand_speed",
                0.0
            )
        )

        right = float(
            person.get(
                "right_hand_speed",
                0.0
            )
        )

        return max(
            left,
            right
        )

    # ======================================================
    # STRONG WORKING EVIDENCE
    #
    # IMPORTANT:
    #
    # We DO NOT use:
    #
    #     person["status"]
    #
    # because status is produced by another behaviour.
    #
    # GroupStandingBehaviour must remain independent.
    # ======================================================

    def _is_working(self, person):

        body_speed = float(
            person.get(
                "avg_frame_displacement",
                person.get(
                    "avg_speed",
                    0.0
                )
            )
        )

        hand_speed = self._hand_speed(
            person
        )

        pose = str(
            person.get(
                "pose_state",
                "Unknown"
            )
        ).lower()

        # --------------------------------------------------
        # Strong body movement
        # --------------------------------------------------

        if body_speed > GROUP_SPEED:

            return True

        # --------------------------------------------------
        # Strong hand movement
        #
        # This is important because a worker may be
        # standing in almost the same place while working.
        # --------------------------------------------------

        if hand_speed >= 8:

            return True

        # --------------------------------------------------
        # Bending is strong evidence of work/activity.
        # --------------------------------------------------

        if pose == "bending":

            return True

        return False

    # ======================================================
    # STANDING EVIDENCE
    # ======================================================

    def _is_standing(self, person):

        pose = str(
            person.get(
                "pose_state",
                "Unknown"
            )
        ).lower()

        if pose != "standing":

            return False

        body_speed = float(
            person.get(
                "avg_frame_displacement",
                person.get(
                    "avg_speed",
                    0.0
                )
            )
        )

        # --------------------------------------------------
        # Pose says Standing, but person is moving too much.
        #
        # Do not call this a standing group.
        # --------------------------------------------------

        if body_speed > GROUP_SPEED:

            return False

        return True

    # ======================================================
    # MAIN
    # ======================================================

    def check(self, people):

        alerts = []

        person_list = list(
            people.values()
        )

        current_time = time.time()

        # ==================================================
        # FIND STANDING CANDIDATES
        # ==================================================

        candidates = []

        for person in person_list:

            zone = person.get(
                "zone",
                "Unknown"
            )

            if zone == "Unknown":

                continue

            if person.get(
                "current_center"
            ) is None:

                continue

            # --------------------------------------------------
            # Only standing people can create a
            # "People Standing in Group" alert.
            # --------------------------------------------------

            if not self._is_standing(
                person
            ):

                continue

            candidates.append(
                person
            )

        # ==================================================
        # BUILD CONNECTED GROUPS
        #
        # Example:
        #
        # A close to B
        # B close to C
        #
        # => A, B, C are treated as one group.
        # ==================================================

        groups = []

        visited = set()

        for person in candidates:

            person_id = person.get(
                "id"
            )

            if person_id is None:

                continue

            if person_id in visited:

                continue

            group = []

            queue = [
                person
            ]

            visited.add(
                person_id
            )

            while queue:

                current = queue.pop()

                group.append(
                    current
                )

                for other in candidates:

                    other_id = other.get(
                        "id"
                    )

                    if other_id is None:

                        continue

                    if other_id in visited:

                        continue

                    # --------------------------------------------------
                    # Same zone
                    # --------------------------------------------------

                    if (
                        other.get("zone")
                        != current.get("zone")
                    ):

                        continue

                    distance = self._distance(
                        current,
                        other
                    )

                    if distance is None:

                        continue

                    if distance <= GROUP_DISTANCE:

                        visited.add(
                            other_id
                        )

                        queue.append(
                            other
                        )

            # --------------------------------------------------
            # At least two people
            # --------------------------------------------------

            if len(group) >= 2:

                groups.append(
                    group
                )

        # ==================================================
        # ACTIVE GROUPS
        # ==================================================

        active_groups = set()

        # ==================================================
        # PROCESS GROUPS
        # ==================================================

        for group in groups:

            ids = tuple(
                sorted(
                    person["id"]
                    for person in group
                )
            )

            zone = group[0].get(
                "zone",
                "Unknown"
            )

            group_key = (
                zone,
                ids
            )

            active_groups.add(
                group_key
            )

            # ==================================================
            # START TIMER
            # ==================================================

            if group_key not in self.group_history:

                self.group_history[
                    group_key
                ] = current_time

                print(
                    f"GROUP START -> "
                    f"Group={ids} | "
                    f"Zone={zone} | "
                    f"People={len(group)}"
                )

                continue

            # ==================================================
            # DURATION
            # ==================================================

            duration = (
                current_time
                - self.group_history[
                    group_key
                ]
            )

            # ==================================================
            # GROUP MOVEMENT ANALYSIS
            # ==================================================

            working_count = 0
            standing_count = 0

            for person in group:

                if self._is_working(
                    person
                ):

                    working_count += 1

                elif self._is_standing(
                    person
                ):

                    standing_count += 1

            # ==================================================
            # DEBUG
            # ==================================================

            print(
                f"GROUP DEBUG -> "
                f"Group={ids} | "
                f"Zone={zone} | "
                f"People={len(group)} | "
                f"Working={working_count}/{len(group)} | "
                f"Standing={standing_count}/{len(group)} | "
                f"Duration={duration:.1f}/{GROUP_TIME}s"
            )

            # ==================================================
            # NOT ENOUGH TIME
            # ==================================================

            if duration < GROUP_TIME:

                continue

            # ==================================================
            # ALREADY ALERTED
            # ==================================================

            if group_key in self.alerted_groups:

                continue

            # ==================================================
            # GROUP CLASSIFICATION
            # ==================================================
            #
            # IMPORTANT:
            #
            # We are deliberately conservative.
            #
            # If everybody is standing and nobody has strong
            # working evidence:
            #
            #     People Standing in Group
            #
            # If everybody has strong working evidence:
            #
            #     People Working in Group
            #
            # Otherwise:
            #
            #     People in Group
            #
            # This prevents one uncertain person from causing
            # a false "working" classification.
            # ==================================================

            if (
                working_count == 0
                and
                standing_count == len(group)
            ):

                group_type = (
                    "People Standing in Group"
                )

            elif (
                working_count == len(group)
            ):

                group_type = (
                    "People Working in Group"
                )

            else:

                group_type = (
                    "People in Group"
                )

            # ==================================================
            # ALERT
            # ==================================================

            self.alerted_groups.add(
                group_key
            )

            alert = {

                "type": group_type,

                "people": list(
                    ids
                ),

                "count": len(
                    group
                ),

                "zone": zone,

                "time": round(
                    duration,
                    1
                ),

                "severity": "INFO",

            }

            alerts.append(
                alert
            )

            # ==================================================
            # DEBUG
            # ==================================================

            print(
                "\n===================================="
            )

            print(
                f"{group_type.upper()}"
            )

            print(
                f"People   : {ids}"
            )

            print(
                f"Count    : {len(group)}"
            )

            print(
                f"Zone     : {zone}"
            )

            print(
                f"Working  : {working_count}/{len(group)}"
            )

            print(
                f"Duration : {duration:.1f}s"
            )

            print(
                "===================================="
            )

        # ==================================================
        # CLEAN OLD GROUPS
        # ==================================================

        for group_key in list(
            self.group_history.keys()
        ):

            if group_key not in active_groups:

                self.group_history.pop(
                    group_key,
                    None
                )

                self.alerted_groups.discard(
                    group_key
                )

        return alerts