from ultralytics import YOLO
from app.config import BASE_DIR
import os


class PoseDetector:

    def __init__(self):

        model_path = os.path.join(
            BASE_DIR,
            "models",
            "yolo11n-pose.pt"
        )

        self.model = YOLO(model_path)

    def detect(self, frame):

        results = self.model(
            frame,
            verbose=False
        )

        return results