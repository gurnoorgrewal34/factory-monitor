from ultralytics import YOLO
import os


class SmokingDetector:

    def __init__(self):

        model_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "models",
            "smoking.pt"
        )

        self.model = YOLO(model_path)

    ##################################################

    def detect(self, frame):

        return self.model(

            frame,

            verbose=False,

            conf=0.25

        )