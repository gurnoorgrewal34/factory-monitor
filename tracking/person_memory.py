import math
import time


class PersonMemory:

    def __init__(self):

        self.people = {}

    # --------------------------------------------------
    # Update Person Position
    # --------------------------------------------------

    def update(self, track_id, center,box):

        current_time = time.time()

        # First appearance
        if track_id not in self.people:

            self.people[track_id] = {

                # Identity
                "id": track_id,
                
                "box": box,

                # Time
                "first_seen": current_time,
                "last_seen": current_time,

                # Position
                "previous_center": center,
                "current_center": center,

                # Tracking statistics
                "frames": 1,
                "distance": 0.0,
                "speed": 0.0,

                # Zone Information
                "zone": "Unknown",
                "zone_enter_time": current_time,
                "zone_time": 0.0,

                # Total time in video
                "total_time": 0.0,

                # Behaviour
                "status": "Normal",

                # Behaviour Flags
                "loitering_alerted": False,
                
                # Phone Behaviour
                "phone_frames": 0,
                "phone_alerted": False,
                "phone_detected": False,
                
                
                
                # Running Behaviour
                "avg_speed": 0.0,
                "running_frames": 0,
                "running_alerted": False

            }

            return

        # Existing Person
        person = self.people[track_id]

        previous = person["current_center"]

        distance = math.sqrt(

            (center[0] - previous[0]) ** 2 +

            (center[1] - previous[1]) ** 2

        )

        dt = current_time - person["last_seen"]

        if dt > 0:

            speed = distance / dt

        else:

            speed = 0

        person["distance"] += distance

        person["speed"] = speed

        # Moving average (reduces noisy speed spikes)
        person["avg_speed"] = (
            0.7 * person["avg_speed"]
            + 0.3 * speed
        )

        person["previous_center"] = previous

        person["current_center"] = center
        
        person["box"] = box

        person["frames"] += 1

        person["last_seen"] = current_time

        person["total_time"] = current_time - person["first_seen"]

    # --------------------------------------------------
    # Update Zone
    # --------------------------------------------------

    def update_zone(self, track_id, zone):

        if track_id not in self.people:
            return

        person = self.people[track_id]

        current_time = time.time()

        # Person entered a NEW zone
        if person["zone"] != zone:

            person["zone"] = zone

            person["zone_enter_time"] = current_time

            person["zone_time"] = 0.0

            # Reset loitering for new zone
            person["loitering_alerted"] = False

        else:

            # Still inside same zone
            person["zone_time"] = current_time - person["zone_enter_time"]

    # --------------------------------------------------
    # Update Behaviour Status
    # --------------------------------------------------

    def update_status(self, track_id, status):

        if track_id in self.people:

            self.people[track_id]["status"] = status

    # --------------------------------------------------
    # Get Single Person
    # --------------------------------------------------

    def get(self, track_id):

        return self.people.get(track_id)

    # --------------------------------------------------
    # Get All People
    # --------------------------------------------------

    def all_people(self):

        return self.people