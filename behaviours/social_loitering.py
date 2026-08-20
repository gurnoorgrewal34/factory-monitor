import math
import time

from app.config import DEBUG

from app.config import (
    SOCIAL_DISTANCE,
    SOCIAL_TIME,
    SOCIAL_SPEED,
)


class SocialLoiteringBehaviour:

    def __init__(self):

        # pair -> timestamp when valid social behaviour started
        self.group_history = {}

        # pair -> alert already generated
        self.alerted_pairs = set()

    # ==========================================================
    # MAIN CHECK
    # ==========================================================

    def check(self, people):

        alerts = []

        person_list = list(people.values())

        current_time = time.time()

        active_pairs = set()

        # ======================================================
        # CHECK EVERY PERSON PAIR
        # ======================================================

        for i in range(len(person_list)):

            for j in range(i + 1, len(person_list)):

                p1 = person_list[i]
                p2 = person_list[j]

                id1 = p1.get("id")
                id2 = p2.get("id")

                if id1 is None or id2 is None:
                    continue

                pair = tuple(sorted((id1, id2)))

                # ==================================================
                # ZONE
                # ==================================================

                zone1 = p1.get("zone", "Unknown")
                zone2 = p2.get("zone", "Unknown")

                if zone1 == "Unknown" or zone2 == "Unknown":
                    continue

                if zone1 != zone2:
                    continue

                # ==================================================
                # ZONE POLICY
                # ==================================================

                zone_rules = p1.get("zone_rules", {})

                if zone_rules.get(
                    "loitering_allowed",
                    False
                ):
                    continue

                # ==================================================
                # POSITION
                # ==================================================

                try:

                    x1, y1 = p1["current_center"]
                    x2, y2 = p2["current_center"]

                except (
                    KeyError,
                    TypeError,
                    ValueError
                ):

                    continue

                distance = math.hypot(
                    x1 - x2,
                    y1 - y2
                )

                # ==================================================
                # NOT CLOSE ENOUGH
                # ==================================================

                if distance > SOCIAL_DISTANCE:

                    self.group_history.pop(
                        pair,
                        None
                    )

                    self.alerted_pairs.discard(
                        pair
                    )

                    continue

                # ==================================================
                # MOTION EVIDENCE
                #
                # IMPORTANT:
                #
                # Social loitering does NOT trust status.
                #
                # We use physical motion instead.
                # ==================================================

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

                slow1 = speed1 <= SOCIAL_SPEED
                slow2 = speed2 <= SOCIAL_SPEED

                # ==================================================
                # WORK / ACTIVITY EVIDENCE
                #
                # Do NOT reject the pair merely because status says
                # Working or Standing.
                #
                # Instead look for actual physical evidence.
                # ==================================================

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

                # ==================================================
                # PHYSICAL WORK EVIDENCE
                #
                # High hand movement means we should be careful
                # before calling this loitering.
                # ==================================================

                active_work1 = (
                    speed1 > SOCIAL_SPEED
                    or hand1 >= 8.0
                )

                active_work2 = (
                    speed2 > SOCIAL_SPEED
                    or hand2 >= 8.0
                )

                # ==================================================
                # BOTH PEOPLE MOVING
                #
                # Almost certainly not social loitering.
                # ==================================================

                if not slow1 or not slow2:

                    self.group_history.pop(
                        pair,
                        None
                    )

                    self.alerted_pairs.discard(
                        pair
                    )

                    continue

                # ==================================================
                # BOTH SHOW STRONG WORK MOVEMENT
                #
                # Example:
                #
                # two workers standing together and actively
                # manipulating equipment.
                #
                # Do not call this social loitering.
                # ==================================================

                if active_work1 and active_work2:

                    self.group_history.pop(
                        pair,
                        None
                    )

                    self.alerted_pairs.discard(
                        pair
                    )

                    continue

                # ==================================================
                # UNKNOWN / LOW CONFIDENCE POSE
                #
                # Do not use pose_state as a hard requirement.
                #
                # Pose failure must not automatically create
                # social loitering.
                # ==================================================

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

                # If BOTH are unknown, evidence is too weak.
                if (
                    pose1 == "unknown"
                    and
                    pose2 == "unknown"
                ):

                    self.group_history.pop(
                        pair,
                        None
                    )

                    self.alerted_pairs.discard(
                        pair
                    )

                    continue

                # ==================================================
                # VALID SOCIAL CANDIDATE
                # ==================================================

                active_pairs.add(pair)

                # ==================================================
                # START EPISODE
                # ==================================================

                if pair not in self.group_history:

                    self.group_history[pair] = current_time

                    print(
                        f"SOCIAL START -> "
                        f"Pair={pair} | "
                        f"Zone={zone1} | "
                        f"Distance={distance:.1f} | "
                        f"Speed1={speed1:.1f} | "
                        f"Speed2={speed2:.1f} | "
                        f"Hand1={hand1:.1f} | "
                        f"Hand2={hand2:.1f}"
                    )

                    continue

                # ==================================================
                # DURATION
                # ==================================================

                duration = (
                    current_time
                    -
                    self.group_history[pair]
                )

                if DEBUG:
                    print(
                    f"SOCIAL DEBUG -> "
                    f"Pair={pair} | "
                    f"Zone={zone1} | "
                    f"Distance={distance:.1f} | "
                    f"Speed1={speed1:.1f} | "
                    f"Speed2={speed2:.1f} | "
                    f"Hand1={hand1:.1f} | "
                    f"Hand2={hand2:.1f} | "
                    f"Pose1={pose1} | "
                    f"Pose2={pose2} | "
                    f"Status1={p1.get('status')} | "
                    f"Status2={p2.get('status')} | "
                    f"Duration={duration:.1f}/{SOCIAL_TIME}s"
                    )

                # ==================================================
                # CONFIRM
                # ==================================================

                if (

                    duration >= SOCIAL_TIME

                    and

                    pair not in self.alerted_pairs

                ):

                    self.alerted_pairs.add(pair)

                    alert = {

                        "type":
                            "Social Loitering",

                        "person1":
                            id1,

                        "person2":
                            id2,

                        "zone":
                            zone1,

                        "distance":
                            round(
                                distance,
                                1
                            ),

                        "time":
                            round(
                                duration,
                                1
                            ),

                        "severity":
                            "HIGH"
                    }

                    alerts.append(alert)

                    print(
                        "\n===================================="
                    )

                    print(
                        "SOCIAL LOITERING DETECTED"
                    )

                    print(
                        f"Person 1 : {id1}"
                    )

                    print(
                        f"Person 2 : {id2}"
                    )

                    print(
                        f"Zone     : {zone1}"
                    )

                    print(
                        f"Distance : {distance:.1f}"
                    )

                    print(
                        f"Duration : {duration:.1f}s"
                    )

                    print(
                        "===================================="
                    )

        # ==========================================================
        # CLEAN OLD PAIRS
        # ==========================================================

        for pair in list(
            self.group_history.keys()
        ):

            if pair not in active_pairs:

                self.group_history.pop(
                    pair,
                    None
                )

                self.alerted_pairs.discard(
                    pair
                )

        return alerts