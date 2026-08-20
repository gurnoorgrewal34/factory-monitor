import os
import cv2
import time

from inputs.camera_source import CameraSource

from app.orchestrator import Orchestrator

from tracking.tracker import PersonTracker
from tracking.person_memory import PersonMemory

from processors.group_processor import GroupProcessor
from processors.frame_processor import FrameProcessor
from processors.person_processor import PersonProcessor
from processors.drawing_processor import DrawingProcessor

from app.behaviour_engine import BehaviourEngine
from app.config import *

from zones.zone_engine import ZoneEngine
from zones.zone_drawer import ZoneDrawer

from alerts.alert_overlay import AlertOverlay


# ==================================================
# SYSTEM INITIALIZATION
# ==================================================

print()
print("========================================")
print("FACTORY MONITORING SYSTEM")
print("========================================")


orchestrator = Orchestrator()
orchestrator.set_modules([
    "smoking"
])


tracker = PersonTracker()


memory = PersonMemory()


zone_engine = ZoneEngine(
    "zones/zones.json"
)


zone_drawer = ZoneDrawer(
    zone_engine
)


behaviour = BehaviourEngine(
    zone_engine
)


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





# ==================================================
# INPUT SOURCE
# ==================================================

camera = CameraSource(

    source_type=INPUT_SOURCE,

    video_path=VIDEO_PATH,

    webcam_index=WEBCAM_INDEX,

    cctv_url=CCTV_URL

)


# ==================================================
# READ FIRST FRAME
#
# This gives us the actual frame dimensions.
# This is especially useful for CCTV streams.
# ==================================================

ret, first_frame = camera.read()


if not ret:

    print(
        "ERROR: Could not read first frame."
    )

    camera.release()

    exit()


height, width = first_frame.shape[:2]


# only for debugging
print()
print("========================================")
print("ACTUAL CAMERA FRAME")
print("========================================")
print(f"Width  : {width}")
print(f"Height : {height}")
print(f"Shape  : {first_frame.shape}")
print("========================================")
print()

#debug over


# ==================================================
# FPS
# ==================================================

fps = camera.get_fps()


if fps <= 0:

    fps = 30.0

frame_processor = FrameProcessor(
    tracker,
    zone_drawer,
    person_processor,
    drawing_processor,
    group_processor,
    alert_overlay,
    behaviour,
    orchestrator,
    fps=fps
)


# ==================================================
# OUTPUT DIRECTORY
# ==================================================

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "outputs"
)


os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# ==================================================
# OUTPUT VIDEO PATH
# ==================================================

OUTPUT_PATH = os.path.join(
    OUTPUT_DIR,
    "check3.mp4"
)


# ==================================================
# VIDEO WRITER
# ==================================================

fourcc = cv2.VideoWriter_fourcc(
    *"mp4v"
)


writer = cv2.VideoWriter(

    OUTPUT_PATH,

    fourcc,

    fps,

    (width, height)

)


if not writer.isOpened():

    print(
        "ERROR: Could not create output video."
    )

    camera.release()

    exit()


# ==================================================
# INFORMATION
# ==================================================

print()
print("========================================")
print("INPUT CONFIGURATION")
print("========================================")

print(
    f"Source Type : {INPUT_SOURCE}"
)

if INPUT_SOURCE == "video":

    print(
        f"Video Path  : {VIDEO_PATH}"
    )

elif INPUT_SOURCE == "webcam":

    print(
        f"Webcam      : {WEBCAM_INDEX}"
    )

elif INPUT_SOURCE == "cctv":

    print(
        "CCTV / RTSP  : CONFIGURED"
    )


print("----------------------------------------")

print(
    f"Resolution  : {width} x {height}"
)

print(
    f"FPS         : {fps}"
)

print("----------------------------------------")

print(
    "Output Video:"
)

print(
    OUTPUT_PATH
)

print("========================================")
print()


# ==================================================
# PROCESS FIRST FRAME
#
# We already read this frame while determining
# the dimensions, so process it normally.
# ==================================================

annotated = frame_processor.process(
    first_frame
)


writer.write(
    annotated
)

# comment this display when not using cctv

# display_frame = cv2.resize(
#     annotated,
#     None,
#     fx=3,
#     fy=3,
#     interpolation=cv2.INTER_LINEAR
# )
# and change the display_frame to annotated in the cv2.imshow() below if not using cctv
cv2.imshow(
    WINDOW_NAME,
    annotated
)


if cv2.waitKey(1) & 0xFF == ord("q"):

    camera.release()

    writer.release()

    cv2.destroyAllWindows()

    exit()


# ==================================================
# PROCESS REMAINING FRAMES
# ==================================================

while True:

    ret, frame = camera.read()


    # ------------------------------------------------
    # FRAME READ FAILED
    # ------------------------------------------------

    if not ret:

        # --------------------------------------------
        # CCTV
        #
        # Try reconnecting instead of immediately
        # shutting down the monitoring system.
        # --------------------------------------------

        if INPUT_SOURCE == "cctv":

            print(
                "CCTV -> Frame read failed."
            )

            print(
                "CCTV -> Trying to reconnect..."
            )


            if camera.reconnect():

                print(
                    "CCTV -> Reconnected successfully."
                )

                continue


            else:

                print(
                    "CCTV -> Reconnect failed."
                )

                time.sleep(2)

                continue


        # --------------------------------------------
        # VIDEO / WEBCAM
        # --------------------------------------------

        break


    # ==================================================
    # RUN COMPLETE PIPELINE
    # ==================================================

    annotated = frame_processor.process(
        frame
    )


    # ==================================================
    # SAVE PROCESSED FRAME
    # ==================================================

    writer.write(
        annotated
    )


    # ==================================================
    # OPTIONAL LIVE DISPLAY
    # ==================================================
    
    # comment this display when not using cctv
    # display_frame = cv2.resize(
    #     annotated,
    #     None,
    #     fx=3,
    #     fy=3,
    #     interpolation=cv2.INTER_LINEAR
    # )
    # and change the display_frame to annotated in the cv2.imshow() below if not using cctv
    cv2.imshow(
        WINDOW_NAME,
        annotated
    )


    if cv2.waitKey(1) & 0xFF == ord("q"):

        break


# ==================================================
# CLEANUP
# ==================================================

camera.release()

writer.release()

cv2.destroyAllWindows()


# ==================================================
# COMPLETE
# ==================================================

print()

print(
    "========================================"
)

print(
    "MONITORING SESSION COMPLETE"
)

print(
    "OUTPUT VIDEO CREATED"
)

print(
    OUTPUT_PATH
)

print(
    "========================================"
)