import math
import time

from app.config import SOCIAL_DISTANCE, SOCIAL_TIME, SOCIAL_SPEED


class SocialLoiteringBehaviour:

    def __init__(self):

        # pair_id -> first time seen together
        self.group_history = {}

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

                # Ignore unknown zones
                if p1["zone"] == "Unknown":
                    continue

                if p2["zone"] == "Unknown":
                    continue

                # Must be in same zone
                if p1["zone"] != p2["zone"]:
                    continue

                # Ignore moving people
                if p1["speed"] > SOCIAL_SPEED:
                    continue

                if p2["speed"] > SOCIAL_SPEED:
                    continue

                ################################################

                x1, y1 = p1["current_center"]
                x2, y2 = p2["current_center"]

                distance = math.sqrt(

                    (x1 - x2) ** 2 +

                    (y1 - y2) ** 2

                )

                ################################################

                if distance > SOCIAL_DISTANCE:
                        pair = tuple(sorted([p1["id"], p2["id"]]))

                        if pair in self.group_history:
                            del self.group_history[pair]
                        continue

                ################################################

                pair = tuple(sorted([p1["id"], p2["id"]]))

                active_pairs.add(pair)

                if pair not in self.group_history:

                    self.group_history[pair] = current_time

                    continue

                duration = current_time - self.group_history[pair]

                if duration >= SOCIAL_TIME:

                    alerts.append({

                        "type": "Social Loitering",

                        "person1": p1["id"],

                        "person2": p2["id"],

                        "zone": p1["zone"],

                        "time": round(duration, 1),

                        "severity": "HIGH"

                    })

        ####################################################
        # Remove inactive pairs
        ####################################################

        old_pairs = list(self.group_history.keys())

        for pair in old_pairs:

            if pair not in active_pairs:

                del self.group_history[pair]

        return alerts