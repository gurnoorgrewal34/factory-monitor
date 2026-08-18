from datetime import datetime, time

from alerts.alert_manager import AlertManager

from app.config import (
    AFTER_SHIFT_SHIFT_END_TIME,
    AFTER_SHIFT_CONFIRM_SECONDS,
    AFTER_SHIFT_GRACE_SECONDS,
)


class AfterShiftBehaviour:

    def __init__(self):

        self.alert_manager = AlertManager()

        # --------------------------------------------------
        # Shift configuration
        # --------------------------------------------------

        self.shift_end_time = datetime.strptime(
            AFTER_SHIFT_SHIFT_END_TIME,
            "%H:%M:%S"
        ).time()

        self.confirm_seconds = (
            AFTER_SHIFT_CONFIRM_SECONDS
        )

        self.grace_seconds = (
            AFTER_SHIFT_GRACE_SECONDS
        )

        # --------------------------------------------------
        # Per-person state
        #
        # person_id ->
        # {
        #     "start_time": datetime,
        #     "last_seen": datetime,
        #     "confirmed": bool
        # }
        # --------------------------------------------------

        self.person_states = {}

        # IDs currently confirmed as working after shift.
        self.active_person_ids = set()

    # ======================================================
    # CHECK WHETHER SHIFT HAS ENDED
    # ======================================================

    def is_after_shift(self, frame_time):

        return (
            frame_time.time()
            >= self.shift_end_time
        )

    # ======================================================
    # CHECK WHETHER ZONE IS MONITORED
    # ======================================================

    def _is_monitored_zone(self, person):

        zone_info = person.get(
            "zone_info"
        )

        if not zone_info:

            return False

        monitor = zone_info.get(
            "monitor",
            {}
        )

        return bool(
            monitor.get(
                "after_shift",
                False
            )
        )

    # ======================================================
    # CLEAR ONE PERSON
    # ======================================================

    def _clear_person(self, person_id):

        self.person_states.pop(
            person_id,
            None
        )

        self.active_person_ids.discard(
            person_id
        )

        self.alert_manager.clear(
            person_id,
            "After Shift"
        )

    # ======================================================
    # MAIN PROCESS
    # ======================================================

    def process(
        self,
        current_people,
        frame_time
    ):

        alerts = []

        # --------------------------------------------------
        # BEFORE SHIFT ENDS
        # --------------------------------------------------

        if not self.is_after_shift(
            frame_time
        ):

            for person_id in list(
                self.person_states.keys()
            ):

                self._clear_person(
                    person_id
                )

            return alerts

        # --------------------------------------------------
        # Track currently visible IDs
        # --------------------------------------------------

        visible_ids = set()

        # ==================================================
        # PROCESS CURRENT PEOPLE
        # ==================================================

        for person in current_people:

            person_id = person.get(
                "id"
            )

            if person_id is None:
                continue

            visible_ids.add(
                person_id
            )

            # ----------------------------------------------
            # Person is NOT inside an after-shift zone.
            #
            # Clear any previous after-shift state.
            # ----------------------------------------------

            if not self._is_monitored_zone(
                person
            ):

                person["after_shift"] = False

                self._clear_person(
                    person_id
                )

                continue

            # ----------------------------------------------
            # Person IS inside monitored zone.
            # ----------------------------------------------

            person["after_shift"] = False

            state = self.person_states.get(
                person_id
            )

            if state is None:

                state = {

                    "start_time": frame_time,

                    "last_seen": frame_time,

                    "confirmed": False

                }

                self.person_states[
                    person_id
                ] = state

            else:

                state["last_seen"] = frame_time

            # ----------------------------------------------
            # Time continuously present after shift
            # ----------------------------------------------

            duration = (
                frame_time
                - state["start_time"]
            ).total_seconds()

            # ----------------------------------------------
            # Confirm after configured duration
            # ----------------------------------------------

            if (
                duration
                >= self.confirm_seconds
            ):

                state["confirmed"] = True

                self.active_person_ids.add(
                    person_id
                )

                person["after_shift"] = True

                # ------------------------------------------
                # Generate alert only once
                # ------------------------------------------

                if self.alert_manager.should_alert(
                    person_id,
                    "After Shift"
                ):

                    zone_name = person.get(
                        "zone",
                        "Unknown"
                    )

                    print(
                        f"[ALERT] [AFTER-SHIFT] "
                        f"Person ID={person_id} | "
                        f"Zone={zone_name} | "
                        f"Duration={duration:.1f}s"
                    )

                    alerts.append({

                        "type": "After Shift",

                        "severity": "WARNING",

                        "person_id": person_id,

                        "zone": zone_name,

                        "duration_seconds": (
                            round(duration, 2)
                        ),

                        "persistent": True

                    })

        # ==================================================
        # HANDLE PEOPLE WHO DISAPPEARED FROM CURRENT FRAME
        #
        # We don't immediately clear them because one
        # missed detection should not terminate the state.
        # ==================================================

        for person_id, state in list(
            self.person_states.items()
        ):

            if person_id in visible_ids:

                continue

            gap = (
                frame_time
                - state["last_seen"]
            ).total_seconds()

            if gap > self.grace_seconds:

                print(
                    f"AFTER-SHIFT CLEARED -> "
                    f"Person ID={person_id} "
                    f"not seen for {gap:.1f}s"
                )

                self._clear_person(
                    person_id
                )

        return alerts

    # ======================================================
    # ACTIVE CHECK
    # ======================================================

    def is_active(self, person_id):

        return (
            person_id
            in self.active_person_ids
        )

    # ======================================================
    # FINALIZE
    # ======================================================

    def finalize(self):

        for person_id in list(
            self.person_states.keys()
        ):

            self._clear_person(
                person_id
            )

        return []