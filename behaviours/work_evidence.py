import math


class WorkEvidence:

    def calculate(self, person):

        body_speed = float(
            person.get("avg_speed", 0.0)
        )

        left_hand = float(
            person.get("left_hand_speed", 0.0)
        )

        right_hand = float(
            person.get("right_hand_speed", 0.0)
        )

        hand_speed = max(
            left_hand,
            right_hand
        )

        evidence = 0.0

        # Body movement
        if body_speed >= 8:
            evidence += 0.5

        # Hand movement
        if hand_speed >= 8:
            evidence += 0.3

        # More substantial movement
        if body_speed >= 20:
            evidence += 0.2

        return min(
            evidence,
            1.0
        )