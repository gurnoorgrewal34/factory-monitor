import os

##################################################
# PROJECT ROOT
##################################################

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


##################################################
# MODELS
##################################################

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "yolo11n.pt"
)

POSE_MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "yolo11n-pose.pt"
)


##################################################
# INPUT SOURCE
#
# Supported:
#
# "video"  -> prerecorded video
# "webcam" -> local webcam
# "cctv"   -> CCTV / RTSP stream
#
##################################################

INPUT_SOURCE = "video"


##################################################
# VIDEO FILE
#
# Used only when:
#
# INPUT_SOURCE = "video"
#
##################################################

VIDEO_PATH = os.path.join(
    BASE_DIR,
    "datasets",
    "raw_videos",
    "run_test.mp4"
)


##################################################
# WEBCAM
#
# Used only when:
#
# INPUT_SOURCE = "webcam"
#
##################################################

WEBCAM_INDEX = 0


##################################################
# CCTV / RTSP
#
# Used only when:
#
# INPUT_SOURCE = "cctv"
#
# Example:
#
# rtsp://username:password@192.168.1.100:554/stream
#
##################################################

CCTV_URL = ""


##################################################
# YOLO SETTINGS
##################################################

CONFIDENCE = 0.40

SHOW_CONFIDENCE = True

SHOW_LABELS = True

WINDOW_NAME = "Factory Monitoring System"


##################################################
# LOITERING
##################################################

LOITERING_TIME = 10


##################################################
# SOCIAL LOITERING
##################################################

SOCIAL_DISTANCE = 120

SOCIAL_TIME = 30

SOCIAL_SPEED = 25


##################################################
# PHONE DETECTION
##################################################

PHONE_CLASS_ID = 67

PHONE_CONFIDENCE = 0.25

PHONE_DISTANCE_THRESHOLD = 120


##################################################
# MOVEMENT THRESHOLDS
##################################################

STANDING_SPEED = 5

SLOW_WORK_SPEED = 25

RUNNING_SPEED = 12


##################################################
# BEHAVIOUR TIMERS
##################################################

WAITING_TIME = 30

STANDING_WITHOUT_WORK_TIME = 20

IDLE_TIME = 200

LONG_IDLE_TIME = 600


##################################################
# RUNNING DETECTION
##################################################
RUNNING_MOTION_THRESHOLD = 0.18
RUNNING_FRAME_THRESHOLD = 8

RUNNING_ENABLED = True


##################################################
# FIRE / SMOKE DETECTION
##################################################

FIRE_CONFIDENCE = 0.20

FIRE_BEHAVIOUR_CONFIDENCE = 0.40

FIRE_FRAME_THRESHOLD = 3

SMOKE_CONFIDENCE = 0.40


##################################################
# GROUP STANDING
##################################################

GROUP_DISTANCE = 120

GROUP_TIME = 5

GROUP_SPEED = 8