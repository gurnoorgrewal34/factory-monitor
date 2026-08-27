from collections import deque
from threading import Lock


class AlertLogStore:

    def __init__(
        self,
        max_logs=500
    ):

        self.logs = deque(
            maxlen=max_logs
        )

        self._lock = Lock()

        # ------------------------------------------
        # In-memory incremental alert ID
        #
        # Resets after backend restart.
        # ------------------------------------------

        self._next_id = 1

    # ==============================================
    # GET NEXT ID
    # ==============================================

    def next_id(
        self
    ):

        with self._lock:

            alert_id = (
                self._next_id
            )

            self._next_id += 1

        return alert_id

    # ==============================================
    # ADD
    # ==============================================

    def add(
        self,
        log
    ):

        with self._lock:

            self.logs.append(
                log
            )

        return log

    # ==============================================
    # GET ALL
    # ==============================================

    def get_all(
        self,
        camera_id=None,
        alert_type=None,
        severity=None,
        limit=50
    ):

        with self._lock:

            logs = list(
                self.logs
            )

        if camera_id:

            logs = [

                log

                for log
                in logs

                if (
                    log.get(
                        "camera_id"
                    )
                    ==
                    camera_id
                )
            ]

        if alert_type:

            logs = [

                log

                for log
                in logs

                if (
                    log.get(
                        "alert_type"
                    )
                    ==
                    alert_type
                )
            ]

        if severity:

            logs = [

                log

                for log
                in logs

                if (
                    log.get(
                        "severity"
                    )
                    ==
                    severity
                )
            ]

        logs = logs[
            -limit:
        ]

        logs.reverse()

        return logs

    # ==============================================
    # CLEAR
    # ==============================================

    def clear(
        self
    ):

        with self._lock:

            self.logs.clear()