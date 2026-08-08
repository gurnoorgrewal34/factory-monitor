import math
from app.config import STANDING_SPEED

class PoseBehaviour:

    ##################################################
    # Calculate angle between 2 points
    ##################################################

    def angle(self, p1, p2):

        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]

        return math.degrees(
            math.atan2(dy, dx)
        )

    ##################################################
    # Angle made by 3 joints
    ##################################################

    def joint_angle(self, a, b, c):

        ba = (a[0] - b[0], a[1] - b[1])
        bc = (c[0] - b[0], c[1] - b[1])

        dot = ba[0] * bc[0] + ba[1] * bc[1]

        mag1 = math.sqrt(ba[0] ** 2 + ba[1] ** 2)
        mag2 = math.sqrt(bc[0] ** 2 + bc[1] ** 2)

        if mag1 == 0 or mag2 == 0:
            return 180

        value = max(
            -1,
            min(1, dot / (mag1 * mag2))
        )

        return math.degrees(math.acos(value))

    ##################################################

    def check(self, person):

        if "pose" not in person:
            return

        pose = person["pose"]

        if pose is None:
            return

        if len(pose) < 17:
            return

        ##################################################
        # Keypoints
        ##################################################

        nose = pose[0]

        left_shoulder = pose[5]
        right_shoulder = pose[6]

        left_elbow = pose[7]
        right_elbow = pose[8]

        left_wrist = pose[9]
        right_wrist = pose[10]

        left_hip = pose[11]
        right_hip = pose[12]

        left_knee = pose[13]
        right_knee = pose[14]

        left_ankle = pose[15]
        right_ankle = pose[16]

        ##################################################
        # Midpoints
        ##################################################

        shoulder_center = (

            (left_shoulder[0] + right_shoulder[0]) / 2,

            (left_shoulder[1] + right_shoulder[1]) / 2

        )

        hip_center = (

            (left_hip[0] + right_hip[0]) / 2,

            (left_hip[1] + right_hip[1]) / 2

        )

        ##################################################
        # Body Angles
        ##################################################

        person["torso_angle"] = self.angle(
            shoulder_center,
            hip_center
        )

        person["head_angle"] = self.angle(
            nose,
            shoulder_center
        )

        person["left_arm_angle"] = self.angle(
            left_shoulder,
            left_wrist
        )

        person["right_arm_angle"] = self.angle(
            right_shoulder,
            right_wrist
        )

        person["left_leg_angle"] = self.angle(
            left_hip,
            left_ankle
        )

        person["right_leg_angle"] = self.angle(
            right_hip,
            right_ankle
        )

        ##################################################
        # Wrist Movement Speed
        ##################################################

        if person["previous_left_wrist"] is not None:

            dx = left_wrist[0] - person["previous_left_wrist"][0]
            dy = left_wrist[1] - person["previous_left_wrist"][1]

            person["left_hand_speed"] = math.sqrt(
                dx * dx + dy * dy
            )

        else:

            person["left_hand_speed"] = 0.0

        if person["previous_right_wrist"] is not None:

            dx = right_wrist[0] - person["previous_right_wrist"][0]
            dy = right_wrist[1] - person["previous_right_wrist"][1]

            person["right_hand_speed"] = math.sqrt(
                dx * dx + dy * dy
            )

        else:

            person["right_hand_speed"] = 0.0

        ##################################################
        # Save Wrist Position
        ##################################################

        person["previous_left_wrist"] = left_wrist
        person["previous_right_wrist"] = right_wrist

        ##################################################
        # Knee Angles
        ##################################################

        left_knee_angle = self.joint_angle(

            left_hip,

            left_knee,

            left_ankle

        )

        right_knee_angle = self.joint_angle(

            right_hip,

            right_knee,

            right_ankle

        )
        
        
        
        ##################################################
        # Hip Angles
        ##################################################

        left_hip_angle = self.joint_angle(
            left_shoulder,
            left_hip,
            left_knee
        )

        right_hip_angle = self.joint_angle(
            right_shoulder,
            right_hip,
            right_knee
        )

        ##################################################
        # Elbow Angles
        ##################################################

        left_elbow_angle = self.joint_angle(
            left_shoulder,
            left_elbow,
            left_wrist
        )

        right_elbow_angle = self.joint_angle(
            right_shoulder,
            right_elbow,
            right_wrist
        )
        
        
        person["left_knee_angle"] = left_knee_angle
        person["right_knee_angle"] = right_knee_angle

        person["left_hip_angle"] = left_hip_angle
        person["right_hip_angle"] = right_hip_angle

        person["left_elbow_angle"] = left_elbow_angle
        person["right_elbow_angle"] = right_elbow_angle

        ##################################################
        # Pose Classification
        ##################################################

        average_knee = (
            left_knee_angle +
            right_knee_angle
        ) / 2

        average_hip = (
            left_hip_angle +
            right_hip_angle
        ) / 2

        ##################################################
        # Sitting
        ##################################################

        if average_knee < 120 and average_hip < 120:

            pose = "Sitting"

        ##################################################
        # Bending
        ##################################################

        elif average_hip < 145:

            pose = "Bending"

        ##################################################
        # Standing
        ##################################################

        elif average_knee > 145 and average_hip > 145:

            pose = "Standing"

        ##################################################
        # Near Standing
        ##################################################

        elif average_knee > 135 and average_hip > 155:

            pose = "Standing"

        ##################################################
        # Fallback
        ##################################################

        else:

            pose = person.get("pose_state", "Standing")

        person["pose_state"] = pose
       
            
            
        print(
            f"POSE -> "
            f"ID={person['id']} | "
            f"Pose={person['pose_state']} | "
            f"Knee={average_knee:.1f} | "
            f"Hip={average_hip:.1f} | "
            f"Speed={person['avg_speed']:.1f}"
        )