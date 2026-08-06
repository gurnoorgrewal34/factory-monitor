from ultralytics import YOLO


class FireDetector:

    def __init__(self):

        self.model = YOLO("models/fire_smoke.pt")

    ##################################################

    def detect(self, frame):

        return self.model(

            frame,

            verbose=False

        )