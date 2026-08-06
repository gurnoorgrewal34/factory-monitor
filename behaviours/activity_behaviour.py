from app.config import (
    STANDING_SPEED,
    SLOW_WORK_SPEED,
    RUNNING_SPEED,
    IDLE_TIME,
)


class ActivityBehaviour:

    def check(self, person):

        speed = person["avg_speed"]

        ####################################################
        # Standing
        ####################################################

        if speed <= STANDING_SPEED:

            person["status"] = "Standing"

            if person["total_time"] >= IDLE_TIME:

                person["status"] = "Idle"

        ####################################################
        # Slow Working
        ####################################################

        elif speed <= SLOW_WORK_SPEED:

            person["status"] = "Slow Working"

        ####################################################
        # Normal
        ####################################################

        elif speed < RUNNING_SPEED:

            person["status"] = "Working"

        ####################################################
        # Running
        ####################################################

        else:

            # RunningBehaviour already raises alerts.
            # Here we only update status.
            person["status"] = "Running"

        return None