import cv2


class DrawingProcessor:

    def draw_person(self, frame, box, person):

        x1, y1, x2, y2 = box

        ####################################################
        # Box Color
        ####################################################

        if person["status"] == "Running":

            color = (0, 165, 255)      # Orange

        elif person["status"] == "Loitering":

            color = (0, 0, 255)        # Red

        else:

            color = (0, 255, 0)        # Green

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
        # Speed
        ####################################################

        cv2.putText(

            frame,

            f"Speed : {person['avg_speed']:.1f}",

            (x1, y1 - 60),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.6,

            (255,255,255),

            2

        )

        ####################################################
        # Zone
        ####################################################

        cv2.putText(

            frame,

            f"Zone : {person['zone']}",

            (x1, y1 - 35),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.6,

            (255,255,0),

            2

        )

        ####################################################
        # Status
        ####################################################

        cv2.putText(

            frame,

            f"Status : {person['status']}",

            (x1, y1 - 10),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.6,

            color,

            2

        )

        ####################################################
        # RUNNING Banner
        ####################################################

        if person["status"] == "Running":

            cv2.putText(

                frame,

                "RUNNING",

                (x1, y2 + 25),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.8,

                (0,165,255),

                3

            )

        return frame