import cv2

from tracking.tracker import PersonTracker
from tracking.person_memory import PersonMemory
from processors.group_processor import GroupProcessor
from processors.frame_processor import FrameProcessor

from app.behaviour_engine import BehaviourEngine
from app.config import *

from zones.zone_engine import ZoneEngine
from zones.zone_drawer import ZoneDrawer

from alerts.alert_overlay import AlertOverlay

from processors.person_processor import PersonProcessor
from processors.drawing_processor import DrawingProcessor


tracker = PersonTracker()
memory = PersonMemory()

zone_engine = ZoneEngine("zones/zones.json")
zone_drawer = ZoneDrawer(zone_engine)
behaviour = BehaviourEngine(zone_engine)

alert_overlay = AlertOverlay()

person_processor = PersonProcessor(
    memory,
    zone_engine,
    behaviour
)

drawing_processor = DrawingProcessor()

group_processor = GroupProcessor(

    memory,

    behaviour

)

frame_processor = FrameProcessor(

    tracker,

    zone_drawer,

    person_processor,

    drawing_processor,

    group_processor,

    alert_overlay,
    behaviour

)

cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    print("Video not found.")
    exit()


while True:

    ret, frame = cap.read()

    if not ret:
        break

    annotated = frame_processor.process(frame)

    cv2.imshow(WINDOW_NAME, annotated)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
    
cap.release()
cv2.destroyAllWindows()