import time


class AlertFormatter:

    DEFAULT_SEVERITY = "warning"

    @classmethod
    def format(
        cls,
        alert_id,
        camera_id,
        alert
    ):

        # ------------------------------------------
        # Alert may be dict OR string
        # ------------------------------------------

        if isinstance(
            alert,
            dict
        ):

            alert_type = (
                alert.get("type")
                or
                alert.get("alert_type")
                or
                alert.get("event")
                or
                "alert"
            )

            message = (
                alert.get("message")
                or
                alert.get("text")
                or
                str(alert)
            )

            severity = (
                alert.get("severity")
                or
                cls.DEFAULT_SEVERITY
            )

            title = (
                alert.get("title")
                or
                str(alert_type)
                .replace("_", " ")
                .upper()
            )

            extra_data = (
                alert.copy()
            )

        else:

            alert_type = (
                "alert"
            )

            message = str(
                alert
            )

            severity = (
                cls.DEFAULT_SEVERITY
            )

            title = (
                "ALERT"
            )

            extra_data = {
                "raw":
                    alert
            }

        # ------------------------------------------
        # Remove duplicate standardized fields
        # from extra data
        # ------------------------------------------

        for key in (
            "type",
            "alert_type",
            "event",
            "message",
            "text",
            "severity",
            "title"
        ):

            extra_data.pop(
                key,
                None
            )

        return {

            "id":
                alert_id,

            "camera_id":
                camera_id,

            "event":
                "alert",

            "alert_type":
                str(
                    alert_type
                ),

            "severity":
                str(
                    severity
                ).lower(),

            "title":
                str(
                    title
                ),

            "message":
                str(
                    message
                ),

            "timestamp":
                time.time(),

            "data":
                extra_data
        }