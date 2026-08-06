from ultralytics import YOLO
from app.config import *


class PersonTracker:

    def __init__(self):

        self.model = YOLO(MODEL_PATH)

    ##################################################

    def track(self, frame):

        results = self.model.track(

            frame,

            persist=True,

            tracker="botsort.yaml",

            conf=CONFIDENCE,

            verbose=False,

            classes=[0]

        )

        return results