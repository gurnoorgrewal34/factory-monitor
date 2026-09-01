from ultralytics import YOLO
from app.config import *


class PersonTracker:

    def __init__(self):

        self.model = YOLO(MODEL_PATH)
        
        
    print()
    print("========================================")
    print("PERSON TRACKER INITIALIZATION")
    print("MODEL_PATH ->", MODEL_PATH)
    print("CONFIDENCE ->", CONFIDENCE)
    print("========================================")    

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
    
    
    ##################################################
    # TEMPORARY RAW PERSON DETECTION DEBUG
    #
    # Used only to compare:
    # YOLO predict vs YOLO + BoT-SORT tracking.
    #
    # Remove after debugging.
    ##################################################

    def detect_debug(
        self,
        frame
    ):

        return self.model.predict(

            frame,

            conf=0.05,

            verbose=False,
            
            classes=[0]
        )