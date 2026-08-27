import cv2


class DrawingProcessor:

    def draw_person(self, frame, box, person):

        x1, y1, x2, y2 = map(int, box)

        ###################################################
        # Box Color
        ####################################################

        status = person["status"]

        if status == "Running":

            color = (0, 165, 255)      # Orange

        elif status == "Loitering":

            color = (0, 0, 255)        # Red

        elif status == "Standing Without Working":

            color = (255, 0, 255)      # Purple

        elif status == "Idle":

            color = (255, 255, 0)      # Cyan

        elif status == "Slow Working":

            color = (0, 255, 255)      # Yellow

        elif status == "Sitting":

            color = (255, 120, 0)      # Blue-Orange

        else:

            color = (0, 255, 0)        # Green

        ####################################################
        # Debug
        ####################################################

        print(
            f"Drawing -> "
            f"ID={person['id']} | "
            f"Status={person['status']} | "
            f"Object={id(person)}"
        )

        ####################################################
        # Bounding Box
        ####################################################

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            color,
            2
        )

        ####################################################
        # Person ID
        ####################################################

        cv2.putText(
            frame,
            f"ID : {person['id']}",
            (x1, y1 - 135),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.30,    # 0.55 for normal, 0.30 for cam5
            (255, 255, 255),
            1    # 2 for normal, 1 for cam5
        )

        ####################################################
        # Speed
        ####################################################

        cv2.putText(
            frame,
            f"Speed : {person['avg_speed']:.1f}",
            (x1, y1 - 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.30,   # 0.55 for normal, 0.30 for cam5
            (255, 255, 255),
            1        # change to 2
        )
        ####################################################
        # Idle Timer
        ####################################################

        if person["idle_time"] > 0:

            cv2.putText(

                frame,

                f"Idle : {person['idle_time']:.1f}s",

                (x1, y1 - 105),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.30,  # 0.55 for normal, 0.30 for cam5

                (255,255,255),

                1     # change to 2

            )
        ####################################################
        # Pose
        ####################################################

        # cv2.putText(
        #     frame,
        #     f"Pose : {person['pose_state']}",
        #     (x1, y1 - 85),
        #     cv2.FONT_HERSHEY_SIMPLEX,
        #     0.30,    # 0.55 for normal, 0.30 for cam5
        #     (255, 255, 0),
        #     1        # 2 for normal, 1 for cam5
        # )

        
        
        
        # changed after getting problem 25082026
        
        
        ####################################################
        # Pose
        ####################################################

        pose_state = person.get(
            "pose_state",
            "Unknown"
        )

        cv2.putText(
            frame,
            f"Pose : {pose_state}",
            (x1, y1 - 85),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 0),
            2,
            cv2.LINE_AA
        )

        ####################################################
        # Zone
        ####################################################

        cv2.putText(
            frame,
            f"Zone : {person['zone']}",
            (x1, y1 - 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,    # 0.55 for normal, 0.30 for cam5   
            (255, 255, 0),
            2        # 2 for normal, 1 for cam5
        )

        ####################################################
        # Status
        ####################################################

        cv2.putText(
            frame,
            person["status"],
            (x1, y1 - 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,    # 0.6 for normal, 0.35 for cam5
            color,
            2   # replace with 2 for normal
        )

        ####################################################
        # Idle Time
        ####################################################

        if status == "Idle":

            cv2.putText(
                frame,
                f"Idle : {person.get('idle_time', 0):.1f}s",
                (x1, y2 + 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,    # 0.7 for normal, 0.35 for cam5
                (255, 0, 255),
                2     # change to 2 for normal
            )

        ####################################################
        # Running Banner
        ####################################################

        elif status == "Running":

            cv2.putText(
                frame,
                "RUNNING",
                (x1, y2 + 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,    # 0.8 for normal, 0.35 for cam5
                (0, 165, 255),
                3     # change to 3 for normal
            )
            
            
            
            
         ####################################################
        # Status Banner
        ####################################################

        if person["status"] == "Standing Without Working":

            cv2.putText(

                frame,

                "STANDING WITHOUT WORKING",

                (x1, y2 + 25),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.65,    # 0.65 for normal, 0.35 for cam5

                (255,0,255),

                2        # 2 for normal, 1 for cam5

            )

        elif person["status"] == "Idle":

            cv2.putText(

                frame,

                "IDLE",

                (x1, y2 + 25),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.55,    # 0.75 for normal, 0.35 for cam5

                (255,255,0),

                2     # change to 2 for normal
            )

        elif person["status"] == "Slow Working":

            cv2.putText(

                frame,

                "SLOW WORKING",

                (x1, y2 + 25),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.75,    # 0.75 for normal, 0.35 for cam5

                (0,255,255),

                2     # change to 2 for normal
    )   

        ####################################################
        # Torso Debug
        ####################################################

        # cv2.putText(
        #     frame,
        #     f"Torso : {person['torso_angle']:.1f}",
        #     (x1, y2 + 50),
        #     cv2.FONT_HERSHEY_SIMPLEX,
        #     0.5,
        #     (255, 0, 255),
        #     1
        # )

        return frame