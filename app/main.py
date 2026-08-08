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


# ==================================================
# SYSTEM INITIALIZATION
# ==================================================

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


# ==================================================
# VIDEO INPUT
# ==================================================


if USE_WEBCAM:

    print("Starting live webcam...")

    cap = cv2.VideoCapture(WEBCAM_INDEX)

else:

    print("Starting video...")

    cap = cv2.VideoCapture(VIDEO_PATH)


if not cap.isOpened():

    print("Unable to open input source.")

    exit()

# ==================================================
# VIDEO OUTPUT
# ==================================================

fps = cap.get(cv2.CAP_PROP_FPS)

if fps <= 0:
    fps = 30.0

width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

OUTPUT_PATH = "output_social.mp4"

fourcc = cv2.VideoWriter_fourcc(*"mp4v")

writer = cv2.VideoWriter(
    OUTPUT_PATH,
    fourcc,
    fps,
    (width, height)
)

if not writer.isOpened():
    print("ERROR: Could not create output video.")
    cap.release()
    exit()


print("========================================")
print("INPUT VIDEO")
print(VIDEO_PATH)
print("----------------------------------------")
print("OUTPUT VIDEO")
print(OUTPUT_PATH)
print("----------------------------------------")
print(f"Resolution : {width} x {height}")
print(f"FPS        : {fps}")
print("========================================")


# ==================================================
# PROCESS VIDEO
# ==================================================

while True:

    ret, frame = cap.read()

    if not ret:
        break

    # Run complete pipeline
    annotated = frame_processor.process(frame)

    # Save processed frame
    writer.write(annotated)

    # Optional live display
    cv2.imshow(WINDOW_NAME, annotated)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


# ==================================================
# CLEANUP
# ==================================================

cap.release()
writer.release()
cv2.destroyAllWindows()

print()
print("========================================")
print("OUTPUT VIDEO CREATED")
print(OUTPUT_PATH)
print("========================================")