import cv2
import time


class AlertOverlay:

    def __init__(self):

        self.active_alerts = []

        self.display_seconds = 5

        self.max_alerts = 6

    ####################################################

    def update(self, alerts):

        now = time.time()

        for alert in alerts:

            duplicate = False

            for existing in self.active_alerts:

                if (

                    existing["type"] == alert["type"]

                    and existing.get("person_id") == alert.get("person_id")

                ):

                    existing["timestamp"] = now

                    duplicate = True

                    break

            if not duplicate:

                alert["timestamp"] = now

                self.active_alerts.append(alert)

    ####################################################

    def draw(self, frame):

        now = time.time()

        self.active_alerts = [

            alert

            for alert in self.active_alerts

            if now - alert["timestamp"] <= self.display_seconds

        ]

        if len(self.active_alerts) == 0:

            return frame

        ####################################################
        # Transparent Background
        ####################################################

        overlay = frame.copy()

        height = 50 + 35 * min(len(self.active_alerts), self.max_alerts)

        cv2.rectangle(

            overlay,

            (20, 20),

            (500, height),

            (30, 30, 30),

            -1

        )

        alpha = 0.55

        cv2.addWeighted(

            overlay,

            alpha,

            frame,

            1 - alpha,

            0,

            frame

        )

        ####################################################
        # Title
        ####################################################

        cv2.putText(

            frame,

            "ACTIVE ALERTS",

            (35, 50),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.8,

            (255, 255, 255),

            2

        )

        ####################################################
        # Draw Alerts
        ####################################################

        y = 85

        for alert in self.active_alerts[-self.max_alerts:]:

            severity = alert.get("severity", "LOW")

            if severity == "HIGH":

                color = (0, 0, 255)

            elif severity == "MEDIUM":

                color = (0, 165, 255)

            else:

                color = (0, 255, 255)

            cv2.circle(

                frame,

                (35, y - 5),

                6,

                color,

                -1

            )

            text = alert["type"]

            if "person_id" in alert:

                text += f" | Person {alert['person_id']}"

            elif "person1" in alert:

                text += f" | {alert['person1']} & {alert['person2']}"

            cv2.putText(

                frame,

                text,

                (50, y),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.6,

                (255, 255, 255),

                2

            )

            y += 30

        return frame