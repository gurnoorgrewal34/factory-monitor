from ultralytics import YOLO


class HelmetDetector:

    def __init__(self):

        self.model = YOLO("models/helmet.pt")

    def detect(self, frame):

        return self.model.predict(

            frame,

            conf=0.35,

            verbose=False

        )