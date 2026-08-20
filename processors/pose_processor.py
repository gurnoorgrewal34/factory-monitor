import math
import time

from app.config import DEBUG

class PoseProcessor:

    LEFT_SHOULDER = 5
    RIGHT_SHOULDER = 6
    
    LEFT_WRIST = 9
    RIGHT_WRIST = 10    

    LEFT_HIP = 11
    RIGHT_HIP = 12

    LEFT_KNEE = 13
    RIGHT_KNEE = 14

    LEFT_ANKLE = 15
    RIGHT_ANKLE = 16
    


    def process(self, people):

        for person in people.values():

            if person["pose"] is None:
                continue

            kp = person["pose"]
            print(
                "POSE SAMPLE ->",
                kp[9],
                kp[10]
            )
            
            ##################################################
            # Hand Movement
            ##################################################

            current_time = time.time()

            left_wrist = kp[self.LEFT_WRIST]
            right_wrist = kp[self.RIGHT_WRIST]

            # Default to no movement for this pose update
            person["left_hand_speed"] = 0.0
            person["right_hand_speed"] = 0.0

            if person["last_pose_time"] is not None:

                dt = current_time - person["last_pose_time"]

                if dt > 0:

                    if person["previous_left_wrist"] is not None:

                        dx = (
                            left_wrist[0]
                            - person["previous_left_wrist"][0]
                        )

                        dy = (
                            left_wrist[1]
                            - person["previous_left_wrist"][1]
                        )

                        person["left_hand_speed"] = (
                            math.hypot(dx, dy) / dt
                        )

                    if person["previous_right_wrist"] is not None:

                        dx = (
                            right_wrist[0]
                            - person["previous_right_wrist"][0]
                        )

                        dy = (
                            right_wrist[1]
                            - person["previous_right_wrist"][1]
                        )

                        person["right_hand_speed"] = (
                            math.hypot(dx, dy) / dt
                        )

            person["previous_left_wrist"] = left_wrist
            person["previous_right_wrist"] = right_wrist

            person["last_pose_time"] = current_time
            
            
            if DEBUG:
                
                print(
                        f"HAND DEBUG -> "
                        f"ID={person['id']} | "
                        f"Body={person['avg_speed']:.1f} | "
                        f"LHand={person['left_hand_speed']:.1f} | "
                        f"RHand={person['right_hand_speed']:.1f}"
                    )

            ##########################################
            # Torso Angle
            ##########################################

            ls = kp[self.LEFT_SHOULDER]
            rs = kp[self.RIGHT_SHOULDER]

            lh = kp[self.LEFT_HIP]
            rh = kp[self.RIGHT_HIP]

            shoulder = (
                (ls[0] + rs[0]) / 2,
                (ls[1] + rs[1]) / 2
            )

            hip = (
                (lh[0] + rh[0]) / 2,
                (lh[1] + rh[1]) / 2
            )

            torso_angle = self.calculate_vertical_angle(
                shoulder,
                hip
            )

            person["torso_angle"] = torso_angle

            ##########################################
            # Knee Angles
            ##########################################

            person["left_knee_angle"] = self.calculate_angle(

                lh,

                kp[self.LEFT_KNEE],

                kp[self.LEFT_ANKLE]

            )

            person["right_knee_angle"] = self.calculate_angle(

                rh,

                kp[self.RIGHT_KNEE],

                kp[self.RIGHT_ANKLE]

            )

            ##########################################
            # Motion
            ##########################################

            if person["avg_speed"] < 8:

                person["motion_state"] = "IDLE"

            elif person["avg_speed"] < 40:

                person["motion_state"] = "WALKING"

            else:

                person["motion_state"] = "RUNNING"

            ##########################################
            # Pose Classification
            ##########################################

            lk = person["left_knee_angle"]
            rk = person["right_knee_angle"]

            if torso_angle < 25:

                if lk > 150 and rk > 150:

                    person["pose_state"] = "Standing"

                elif lk < 120 and rk < 120:

                    person["pose_state"] = "Sitting"

                else:

                    person["pose_state"] = "Unknown"

            elif torso_angle < 60:

                person["pose_state"] = "Bending"

            else:

                person["pose_state"] = "Fallen"
                
                
                
        ########################################################
        # DEBUG
        ########################################################

            print(
                f"POSE CLASSIFIER -> "
                f"ID={person['id']} | "
                f"Torso={torso_angle:.1f} | "
                f"LK={lk:.1f} | "
                f"RK={rk:.1f} | "
                f"Result={person['pose_state']}"
            )


    ########################################################

    def calculate_vertical_angle(self, p1, p2):

        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]

        angle = abs(math.degrees(math.atan2(dx, dy)))

        return angle

    ########################################################

    def calculate_angle(self, a, b, c):

        ba = (a[0]-b[0], a[1]-b[1])
        bc = (c[0]-b[0], c[1]-b[1])

        dot = ba[0]*bc[0] + ba[1]*bc[1]

        mag1 = math.hypot(ba[0], ba[1])
        mag2 = math.hypot(bc[0], bc[1])

        if mag1 == 0 or mag2 == 0:
            return 180

        value = dot/(mag1*mag2)

        value = max(-1, min(1, value))

        return math.degrees(math.acos(value))