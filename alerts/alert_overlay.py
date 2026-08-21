import cv2
import time


class AlertOverlay:

    def __init__(self):

        ##################################################
        # Alerts currently visible on video
        ##################################################

        self.active_alerts = []

        ##################################################
        # Newly generated alerts waiting to be consumed
        # by CameraRuntime / WebSocket.
        #
        # IMPORTANT:
        # We DO NOT clear this on every update() because
        # FrameProcessor may call update() several times
        # during the same frame.
        ##################################################

        self.recent_alerts = []

        ##################################################
        # Default UI settings
        ##################################################

        self.display_seconds = 5

        self.max_alerts = 6

    ######################################################
    # UPDATE ALERTS
    ######################################################

    def update(self, alerts):

        if not alerts:
            return

        now = time.time()

        for alert in alerts:

            alert_type = alert.get(
                "type",
                "Unknown"
            )

            person_id = alert.get(
                "person_id"
            )

            persistent = alert.get(
                "persistent",
                False
            )

            display_seconds = alert.get(
                "display_seconds",
                self.display_seconds
            )

            duplicate = False

            ##################################################
            # UPDATE EXISTING VISUAL ALERT
            ##################################################

            for existing in self.active_alerts:

                if (
                    existing.get("type") == alert_type
                    and
                    existing.get("person_id") == person_id
                ):

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

                    existing["display_seconds"] = (
                        display_seconds
                    )

                    ##################################################
                    # Copy latest metadata such as:
                    # zone
                    # speed
                    # duration
                    # confidence
                    ##################################################

                    for key, value in alert.items():

                        if key != "timestamp":

                            existing[key] = value

                    duplicate = True

                    break

            ##################################################
            # NEW ALERT
            ##################################################

            if not duplicate:

                new_alert = alert.copy()

                new_alert["timestamp"] = now

                new_alert["display_seconds"] = (
                    display_seconds
                )

                self.active_alerts.append(
                    new_alert
                )

                ##################################################
                # IMPORTANT:
                #
                # This is the event that CameraRuntime will
                # forward to WebSocket.
                #
                # Only genuinely new visual/event alerts are
                # emitted here. Refreshes of an existing alert
                # do not spam the frontend.
                ##################################################

                self.recent_alerts.append(
                    new_alert.copy()
                )

    ######################################################
    # GET NEW ALERT EVENTS
    ######################################################

    def pop_recent_alerts(self):

        """
        Return alerts generated since the previous call.

        CameraRuntime calls this once after processing
        each frame.
        """

        if not self.recent_alerts:
            return []

        alerts = self.recent_alerts.copy()

        self.recent_alerts.clear()

        return alerts

    ######################################################
    # DRAW ALERT OVERLAY
    ######################################################

    def draw(self, frame):

        now = time.time()

        ##################################################
        # REMOVE EXPIRED ALERTS
        ##################################################

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

            ##################################################
            # Persistent alert
            ##################################################

            if persistent:

                updated_alerts.append(
                    alert
                )

                continue

            ##################################################
            # Temporary alert
            ##################################################

            if age <= display_seconds:

                updated_alerts.append(
                    alert
                )

        self.active_alerts = (
            updated_alerts
        )

        ##################################################
        # NOTHING TO DRAW
        ##################################################

        if not self.active_alerts:

            return frame

        ##################################################
        # ALERT PRIORITY
        ##################################################

        priority = {

            "CRITICAL": 0,

            "HIGH": 1,

            "MEDIUM": 2,

            "WARNING": 2,

            "LOW": 3

        }

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

        sorted_alerts = (
            sorted_alerts[
                :self.max_alerts
            ]
        )

        ##################################################
        # BACKGROUND
        ##################################################

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

        ##################################################
        # TITLE
        ##################################################

        cv2.putText(

            frame,

            "ACTIVE ALERTS",

            (35, 50),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.8,

            (255, 255, 255),

            2
        )

        ##################################################
        # DRAW ALERTS
        ##################################################

        y = 85

        for alert in sorted_alerts:

            severity = alert.get(
                "severity",
                "LOW"
            )

            ##################################################
            # COLOR
            ##################################################

            if severity in (
                "CRITICAL",
                "HIGH"
            ):

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

            ##################################################
            # INDICATOR
            ##################################################

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

            ##################################################
            # TEXT
            ##################################################

            text = alert.get(
                "type",
                "Alert"
            )

            if "person_id" in alert:

                text += (
                    f" | Person "
                    f"{alert['person_id']}"
                )

            elif (
                "person1" in alert
                and
                "person2" in alert
            ):

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