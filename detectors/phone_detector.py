from ultralytics import YOLO


class PhoneDetector:

    def __init__(self):

        self.model = YOLO("models/phone.pt")

    def detect(self, frame):

        return self.model.predict(

            frame,

            conf=0.37,

            verbose=False

        )