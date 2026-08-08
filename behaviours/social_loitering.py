import math
import time

from app.config import SOCIAL_DISTANCE, SOCIAL_TIME, SOCIAL_SPEED


class SocialLoiteringBehaviour:

    def __init__(self):

        # pair_id -> first time seen together
        self.group_history = {}

        # pair_id -> alert already generated for current episode
        self.alerted_pairs = set()

    def check(self, people):

        alerts = []

        person_list = list(people.values())

        current_time = time.time()

        active_pairs = set()

        ####################################################
        # Compare every pair
        ####################################################

        for i in range(len(person_list)):

            for j in range(i + 1, len(person_list)):

                p1 = person_list[i]
                p2 = person_list[j]

                ################################################
                # Zone Check
                ################################################

                if p1.get("zone") == "Unknown":
                    continue

                if p2.get("zone") == "Unknown":
                    continue

                if p1.get("zone") != p2.get("zone"):
                    continue

                ################################################
                # Movement Check
                ################################################

                speed1 = float(p1.get("avg_speed", 0.0))
                speed2 = float(p2.get("avg_speed", 0.0))

                if speed1 > SOCIAL_SPEED:
                    continue

                if speed2 > SOCIAL_SPEED:
                    continue

                ################################################
                # Distance Check
                ################################################

                x1, y1 = p1["current_center"]
                x2, y2 = p2["current_center"]

                distance = math.hypot(
                    x1 - x2,
                    y1 - y2
                )

                pair = tuple(
                    sorted([p1["id"], p2["id"]])
                )

                ################################################
                # Too Far Apart
                ################################################

                if distance > SOCIAL_DISTANCE:

                    self.group_history.pop(pair, None)
                    self.alerted_pairs.discard(pair)

                    continue

                ################################################
                # Valid Social Pair
                ################################################

                active_pairs.add(pair)

                ################################################
                # First Time Together
                ################################################

                if pair not in self.group_history:

                    self.group_history[pair] = current_time

                    print(
                        f"SOCIAL START -> "
                        f"Pair={pair} | "
                        f"Zone={p1.get('zone')} | "
                        f"Distance={distance:.1f}"
                    )

                    continue

                ################################################
                # Calculate Duration
                ################################################

                duration = (
                    current_time
                    - self.group_history[pair]
                )

                print(
                    f"SOCIAL DEBUG -> "
                    f"Pair={pair} | "
                    f"Zone={p1.get('zone')} | "
                    f"Distance={distance:.1f} | "
                    f"Speed1={speed1:.1f} | "
                    f"Speed2={speed2:.1f} | "
                    f"Duration={duration:.1f}/{SOCIAL_TIME}s"
                )

                ################################################
                # Social Loitering Confirmed
                ################################################

                if (
                    duration >= SOCIAL_TIME
                    and pair not in self.alerted_pairs
                ):

                    self.alerted_pairs.add(pair)

                    alert = {

                        "type": "Social Loitering",

                        "person1": p1["id"],

                        "person2": p2["id"],

                        "zone": p1.get("zone"),

                        "time": round(duration, 1),

                        "severity": "HIGH"

                    }

                    alerts.append(alert)

                    print(
                        "\n===================================="
                    )
                    print("SOCIAL LOITERING DETECTED")
                    print(f"Person 1 : {p1['id']}")
                    print(f"Person 2 : {p2['id']}")
                    print(f"Zone     : {p1.get('zone')}")
                    print(f"Distance : {distance:.1f}")
                    print(f"Duration : {duration:.1f}s")
                    print(
                        "===================================="
                    )

        ####################################################
        # Remove Inactive Pairs
        ####################################################

        for pair in list(self.group_history.keys()):

            if pair not in active_pairs:

                self.group_history.pop(pair, None)

                self.alerted_pairs.discard(pair)

        return alerts