import math
import time


class PersonMemory:

    def __init__(self):

        self.people = {}

    # --------------------------------------------------
    # Update Person Position
    # --------------------------------------------------

    def update(self, track_id, center, box):

        current_time = time.time()

        # First appearance
        if track_id not in self.people:

            self.people[track_id] = {

                # Identity
                "id": track_id,

                "box": box,

                ##################################################
                # Pose Information
                ##################################################

                # Raw keypoints from YOLO
                "pose": None,
                "activity_state": "Unknown",

                ##################################################
                # Idle Behaviour
                ##################################################

                "stationary_since": None,
                "idle_time": 0.0,
                "idle_alerted": False,

                "standing_alerted": False,
                ##################################################
                # Pose
                ##################################################
                
                "pose_state": "UNKNOWN",

                # Motion state
                "motion_state": "UNKNOWN",

                # Angles
                "torso_angle": 0.0,
                "head_angle": 0.0,

                "left_arm_angle": 0.0,
                "right_arm_angle": 0.0,

                "left_knee_angle": 0.0,
                "right_knee_angle": 0.0,
                
                "left_hip_angle": 0.0,
                "right_hip_angle": 0.0,

                "left_elbow_angle": 0.0,
                "right_elbow_angle": 0.0,

                # Confidence
                "pose_confidence": 0.0,

                # Hand movement
                "previous_left_wrist": None,
                "previous_right_wrist": None,

                "left_hand_speed": 0.0,
                "right_hand_speed": 0.0,
                
                "last_pose_time": None,

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
                "activity": "Normal",

                # Behaviour Flags
                "loitering_alerted": False, 

                ##################################################
                # Phone Behaviour
                ##################################################

                "phone_frames": 0,
                "phone_alerted": False,
                "phone_detected": False,

                ##################################################
                # Running Behaviour
                ##################################################

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

        print(
            f"SPEED CALC -> "
            f"ID={track_id} | "
            f"Center={center} | "
            f"Previous={previous} | "
            f"Distance={distance:.2f} | "
            f"dt={dt:.4f} | "
            f"RawSpeed={speed:.2f}"
        )

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
    
    
    
    def debug(self):

        print("CURRENT MEMORY IDS:", list(self.people.keys()))