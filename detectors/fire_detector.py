from ultralytics import YOLO
from app.config import FIRE_CONFIDENCE


class FireDetector:

    def __init__(self):

        self.model = YOLO(
            "models/3rd_model_fire_smoke.pt"
        )

        print(
            "========================================"
        )

        print(
            "FIRE/SMOKE MODEL LOADED"
        )

        print(
            "Model: models/3rd_model_fire_smoke.pt"
        )

        print(
            f"Inference confidence: {FIRE_CONFIDENCE}"
        )

        print(
            f"Model classes: {self.model.names}"
        )

        print(
            "========================================"
        )

    ##################################################

    def detect(self, frame):

        results = self.model(
            frame,
            conf=FIRE_CONFIDENCE,
            verbose=False
        )

        if not results:

            print(
                "FIRE DEBUG -> No results returned"
            )

            return results

        result = results[0]

        if (
            result.boxes is None
            or len(result.boxes) == 0
        ):

            print(
                "FIRE DEBUG -> No detections"
            )

            return results

        ##################################################
        # DEBUG
        ##################################################

        for det in result.boxes:

            cls = int(
                det.cls[0]
            )

            confidence = float(
                det.conf[0]
            )

            label = result.names[cls]

            print(
                f"FIRE DEBUG -> "
                f"ClassID={cls} | "
                f"Label={label} | "
                f"Confidence={confidence:.3f}"
            )

        return results