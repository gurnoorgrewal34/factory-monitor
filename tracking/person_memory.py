import math
import time
import statistics
from collections import deque


class PersonMemory:

    def __init__(self):

        self.people = {}

    # ==========================================================
    # CREATE PERSON
    # ==========================================================

    def _create_person(self, track_id, center, box, current_time):

        # Person height in pixels
        person_height = max(
            1.0,
            float(box[3] - box[1])
        )

        self.people[track_id] = {

            # --------------------------------------------------
            # Identity
            # --------------------------------------------------

            "id": track_id,
            "box": box,

            # --------------------------------------------------
            # Pose
            # --------------------------------------------------

            "pose": None,
            "activity_state": "Unknown",
            "pose_state": "UNKNOWN",
            "motion_state": "UNKNOWN",

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

            "pose_confidence": 0.0,

            # --------------------------------------------------
            # Hand movement
            # --------------------------------------------------

            "previous_left_wrist": None,
            "previous_right_wrist": None,

            "left_hand_speed": 0.0,
            "right_hand_speed": 0.0,

            "last_pose_time": None,

            # --------------------------------------------------
            # Time
            # --------------------------------------------------

            "first_seen": current_time,
            "last_seen": current_time,

            # --------------------------------------------------
            # Position
            # --------------------------------------------------

            "previous_center": center,
            "current_center": center,

            # --------------------------------------------------
            # Tracking statistics
            # --------------------------------------------------

            "frames": 1,
            "distance": 0.0,

            # Raw instantaneous speed.
            "speed": 0.0,

            # Stable speed used by existing code.
            "avg_speed": 0.0,

            # --------------------------------------------------
            # NEW: normalized motion
            # --------------------------------------------------

            "motion_speed": 0.0,
            "avg_motion_speed": 0.0,

            "person_height": person_height,

            # Recent normalized speeds.
            "speed_history": deque(maxlen=12),

            # Recent centers.
            "position_history": deque(
                [(center[0], center[1], current_time)],
                maxlen=12
            ),

            # --------------------------------------------------
            # Zone
            # --------------------------------------------------

            "zone": "Unknown",
            "zone_enter_time": current_time,
            "zone_time": 0.0,

            # --------------------------------------------------
            # Total time
            # --------------------------------------------------

            "total_time": 0.0,

            # --------------------------------------------------
            # Behaviour
            # --------------------------------------------------

            "status": "Normal",
            "activity": "Normal",

            # --------------------------------------------------
            # Idle
            # --------------------------------------------------

            "stationary_since": None,
            "idle_time": 0.0,
            "idle_alerted": False,
            "standing_alerted": False,

            # --------------------------------------------------
            # Loitering
            # --------------------------------------------------

            "loitering_alerted": False,

            # --------------------------------------------------
            # Phone
            # --------------------------------------------------

            "phone_frames": 0,
            "phone_alerted": False,
            "phone_detected": False,

            # --------------------------------------------------
            # Running
            # --------------------------------------------------

            "running_frames": 0,
            "running_alerted": False,

            # Extra running state
            "running_candidate": False,
            "running_candidate_frames": 0,
            
            
            "motion_speed": 0.0,
            "avg_motion_speed": 0.0,

            "speed_history": deque(maxlen=8),

            "position_history": deque(
                [(center[0], center[1], current_time)],
                maxlen=12
            ),

        }

    # ==========================================================
    # UPDATE POSITION
    # ==========================================================

    def update(self, track_id, center, box):

        current_time = time.time()

        # ------------------------------------------------------
        # New person
        # ------------------------------------------------------

        if track_id not in self.people:

            self._create_person(
                track_id,
                center,
                box,
                current_time
            )

            return

        # ------------------------------------------------------
        # Existing person
        # ------------------------------------------------------

        person = self.people[track_id]

        previous = person["current_center"]

        # ------------------------------------------------------
        # Time difference
        # ------------------------------------------------------

        dt = current_time - person["last_seen"]

        # Ignore impossible time intervals.
        if dt <= 0:
            dt = 1e-6

        # Protect against tracker stalls.
        dt = min(dt, 0.5)

        # ------------------------------------------------------
        # Pixel displacement
        # ------------------------------------------------------

        dx = center[0] - previous[0]
        dy = center[1] - previous[1]

        distance = math.sqrt(
            dx * dx +
            dy * dy
        )

        # ------------------------------------------------------
        # Person height
        # ------------------------------------------------------

        current_height = max(
            1.0,
            float(box[3] - box[1])
        )

        # Smooth the height slightly.
        old_height = person.get(
            "person_height",
            current_height
        )

        person_height = (
            0.8 * old_height +
            0.2 * current_height
        )

        person["person_height"] = person_height

        # ------------------------------------------------------
        # RAW SPEED
        #
        # Kept for compatibility with existing models.
        # DO NOT use this directly for Running.
        # ------------------------------------------------------

        raw_speed = distance / dt

        # ------------------------------------------------------
        # NORMALIZED SPEED
        #
        # Pixel movement / person height.
        #
        # This makes movement much less dependent on:
        # - camera resolution
        # - person distance from camera
        # - bounding-box size
        # ------------------------------------------------------

        normalized_speed = (
            distance / person_height
        ) / dt

        # ------------------------------------------------------
        # Reject obvious tracker jumps
        # ------------------------------------------------------

        # If a person suddenly moves more than 35% of their
        # body height in one tracking interval, it is likely
        # a tracker jump rather than actual running movement.

        max_reasonable_displacement = (
            person_height * 0.20
        )

        if distance > max_reasonable_displacement:

            # Do not feed this huge jump into running.
            motion_speed = 0.0

            print(
                f"SPEED REJECTED -> "
                f"ID={track_id} | "
                f"Distance={distance:.2f} | "
                f"Height={person_height:.2f}"
            )

        else:

            motion_speed = normalized_speed

        # ------------------------------------------------------
        # SPEED HISTORY
        # ------------------------------------------------------

        history = person["speed_history"]

        history.append(motion_speed)

        # Use median instead of a simple exponential average.
        #
        # Median is much harder for one noisy frame to corrupt.

        if len(history) >= 3:

            stable_speed = float(
                statistics.median(history)
            )

        else:

            stable_speed = motion_speed

        # ------------------------------------------------------
        # Update position history
        # ------------------------------------------------------

        person["position_history"].append(
            (
                center[0],
                center[1],
                current_time
            )
        )

        # ------------------------------------------------------
        # Existing values
        # ------------------------------------------------------

        person["distance"] += distance

        person["speed"] = raw_speed

        # IMPORTANT:
        #
        # Keep avg_speed conservative so other existing code
        # that uses avg_speed does not suddenly change wildly.

        old_avg = person.get("avg_speed", 0.0)

        person["avg_speed"] = (
            0.8 * old_avg +
            0.2 * raw_speed
        )

        # New normalized values.
        person["motion_speed"] = motion_speed

        old_motion_avg = person.get(
            "avg_motion_speed",
            0.0
        )

        person["avg_motion_speed"] = (
            0.8 * old_motion_avg +
            0.2 * stable_speed
        )

        # ------------------------------------------------------
        # Position
        # ------------------------------------------------------

        person["previous_center"] = previous
        person["current_center"] = center
        person["box"] = box

        # ------------------------------------------------------
        # Tracking
        # ------------------------------------------------------

        person["frames"] += 1
        person["last_seen"] = current_time

        person["total_time"] = (
            current_time -
            person["first_seen"]
        )

        # ------------------------------------------------------
        # DEBUG
        # ------------------------------------------------------

        print(
            f"SPEED CALC -> "
            f"ID={track_id} | "
            f"Center={center} | "
            f"Previous={previous} | "
            f"Distance={distance:.2f} | "
            f"Height={person_height:.1f} | "
            f"dt={dt:.4f} | "
            f"RawSpeed={raw_speed:.2f} | "
            f"Normalized={motion_speed:.3f} | "
            f"Stable={stable_speed:.3f}"
        )

    # ==========================================================
    # UPDATE ZONE
    # ==========================================================

    def update_zone(self, track_id, zone):

        if track_id not in self.people:
            return

        person = self.people[track_id]

        current_time = time.time()

        if person["zone"] != zone:

            person["zone"] = zone

            person["zone_enter_time"] = current_time

            person["zone_time"] = 0.0

            person["loitering_alerted"] = False

        else:

            person["zone_time"] = (
                current_time -
                person["zone_enter_time"]
            )

    # ==========================================================
    # UPDATE STATUS
    # ==========================================================

    def update_status(self, track_id, status):

        if track_id in self.people:

            self.people[track_id]["status"] = status

    # ==========================================================
    # GET PERSON
    # ==========================================================

    def get(self, track_id):

        return self.people.get(track_id)

    # ==========================================================
    # GET ALL
    # ==========================================================

    def all_people(self):

        return self.people

    # ==========================================================
    # DEBUG
    # ==========================================================

    def debug(self):

        print(
            "CURRENT MEMORY IDS:",
            list(self.people.keys())
        )