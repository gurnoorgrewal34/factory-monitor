from ultralytics import YOLO
from app.config import BASE_DIR
import os


class FallDetector:

    def __init__(self):

        model_path = os.path.join(
            BASE_DIR,
            "models",
            "fall_detector.pt"
        )

        print()
        print("ORCHESTRATOR -> Loading FALL model")
        print("Fall model:", model_path)

        if not os.path.exists(model_path):

            raise FileNotFoundError(
                f"Fall model not found: {model_path}"
            )

        self.model = YOLO(
            model_path
        )

        print(
            "Fall model loaded successfully."
        )

        print(
            "Fall classes:",
            self.model.names
        )

    def detect(self, frame):

        results = self.model.predict(
            frame,
            conf=0.25,
            imgsz=640,
            verbose=False
        )

        return results