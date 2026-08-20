import cv2
import time


class AlertOverlay:

    def __init__(self):

        self.active_alerts = []

        # Default duration used when an alert does not
        # provide its own display_seconds value.
        self.display_seconds = 5

        self.max_alerts = 6

    ####################################################
    # Update Alerts
    ####################################################

    def update(self, alerts):

        now = time.time()

        for alert in alerts:

            alert_type = alert["type"]

            person_id = alert.get(
                "person_id"
            )

            persistent = alert.get(
                "persistent",
                False
            )

            # Allow individual alerts to specify
            # their own display duration.
            display_seconds = alert.get(
                "display_seconds",
                self.display_seconds
            )

            duplicate = False

            ################################################
            # Find existing alert
            ################################################

            for existing in self.active_alerts:

                if (

                    existing["type"] == alert_type

                    and

                    existing.get("person_id")
                    == person_id

                ):

                    # Refresh the alert timestamp.
                    existing["timestamp"] = now

                    existing["severity"] = alert.get(

                        "severity",

                        existing.get(
                            "severity",
                            "LOW"
                        )

                    )

                    existing["persistent"] = (
                        persistent
                    )

                    # IMPORTANT:
                    # Preserve/update custom alert lifetime.
                    existing["display_seconds"] = (
                        display_seconds
                    )

                    # Keep latest additional information,
                    # such as zone or duration.
                    for key, value in alert.items():

                        if key not in (
                            "timestamp",
                        ):

                            existing[key] = value

                    duplicate = True

                    break

            ################################################
            # New alert
            ################################################

            if not duplicate:

                new_alert = (
                    alert.copy()
                )

                new_alert["timestamp"] = now

                new_alert["display_seconds"] = (
                    display_seconds
                )

                self.active_alerts.append(
                    new_alert
                )

    ####################################################
    # Draw
    ####################################################

    def draw(self, frame):

        now = time.time()

        ################################################
        # Remove expired alerts
        #
        # Persistent alerts remain indefinitely.
        #
        # Non-persistent alerts use:
        #
        #     alert["display_seconds"]
        #
        # when provided.
        #
        # Otherwise they use the default:
        #
        #     self.display_seconds
        ################################################

        updated_alerts = []

        for alert in self.active_alerts:

            persistent = alert.get(
                "persistent",
                False
            )

            display_seconds = alert.get(

                "display_seconds",

                self.display_seconds

            )

            timestamp = alert.get(
                "timestamp",
                now
            )

            age = (
                now
                -
                timestamp
            )

            ################################################
            # Keep persistent alerts
            ################################################

            if persistent:

                updated_alerts.append(
                    alert
                )

                continue

            ################################################
            # Keep temporary alert while still valid
            ################################################

            if age <= display_seconds:

                updated_alerts.append(
                    alert
                )

        self.active_alerts = (
            updated_alerts
        )

        ################################################
        # Nothing to draw
        ################################################

        if len(
            self.active_alerts
        ) == 0:

            return frame

        ################################################
        # Priority
        ################################################

        priority = {

            "CRITICAL": 0,

            "HIGH": 1,

            "MEDIUM": 2,

            "WARNING": 2,

            "LOW": 3

        }

        ################################################
        # Sort highest priority first
        ################################################

        sorted_alerts = sorted(

            self.active_alerts,

            key=lambda alert:

            priority.get(

                alert.get(
                    "severity",
                    "LOW"
                ),

                3

            )

        )

        ################################################
        # Limit alerts
        ################################################

        sorted_alerts = (
            sorted_alerts[
                :self.max_alerts
            ]
        )

        ################################################
        # Background
        ################################################

        overlay = frame.copy()

        height = (
            50
            +
            35 * len(
                sorted_alerts
            )
        )

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

        ################################################
        # Title
        ################################################

        cv2.putText(

            frame,

            "ACTIVE ALERTS",

            (35, 50),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.8,

            (255, 255, 255),

            2

        )

        ################################################
        # Alerts
        ################################################

        y = 85

        for alert in sorted_alerts:

            severity = alert.get(

                "severity",

                "LOW"

            )

            ################################################
            # Alert color
            ################################################

            if severity == "CRITICAL":

                color = (
                    0,
                    0,
                    255
                )

            elif severity == "HIGH":

                color = (
                    0,
                    0,
                    255
                )

            elif severity in (
                "MEDIUM",
                "WARNING"
            ):

                color = (
                    0,
                    165,
                    255
                )

            else:

                color = (
                    0,
                    255,
                    255
                )

            ################################################
            # Indicator
            ################################################

            cv2.circle(

                frame,

                (
                    35,
                    y - 5
                ),

                6,

                color,

                -1

            )

            ################################################
            # Text
            ################################################

            text = alert[
                "type"
            ]

            if "person_id" in alert:

                text += (
                    f" | Person "
                    f"{alert['person_id']}"
                )

            elif "person1" in alert:

                text += (

                    f" | "
                    f"{alert['person1']}"

                    f" & "
                    f"{alert['person2']}"

                )

            cv2.putText(

                frame,

                text,

                (
                    50,
                    y
                ),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.6,

                (255, 255, 255),

                2

            )

            y += 30

        return frame