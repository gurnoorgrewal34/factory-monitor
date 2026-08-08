import os

##################################################
# Project Root
##################################################

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

##################################################
# Models
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
# Video
##################################################

VIDEO_PATH = os.path.join(
    BASE_DIR,
    "datasets",
    "raw_videos",
    "testing_video.mp4"
)

##################################################
# Input Source
##################################################

USE_WEBCAM = False

WEBCAM_INDEX = 0

##################################################
# YOLO Settings
##################################################

CONFIDENCE = 0.40

SHOW_CONFIDENCE = True

SHOW_LABELS = True

WINDOW_NAME = "Factory Monitoring System"

##################################################
# Loitering
##################################################

LOITERING_TIME = 10          # Testing (Production: 20-30 sec)

##################################################
# Social Loitering
##################################################

SOCIAL_DISTANCE = 120        # pixels

SOCIAL_TIME = 20             # seconds

SOCIAL_SPEED = 25            # pixels/sec

##################################################
# Phone Detection
##################################################

PHONE_CLASS_ID = 67

PHONE_CONFIDENCE = 0.25

PHONE_DISTANCE_THRESHOLD = 120

##################################################
# Movement Thresholds (pixels/frame)
##################################################

STANDING_SPEED = 5

SLOW_WORK_SPEED = 25

RUNNING_SPEED = 12

##################################################
# Behaviour Timers
##################################################

# Used for future attendance logic
WAITING_TIME = 30

# Standing without doing any work
STANDING_WITHOUT_WORK_TIME = 8      # Testing (Production: 15-20)

# Completely idle
IDLE_TIME = 20                      # Testing (Change to 300 for production)

# Long idle
LONG_IDLE_TIME = 600                # 10 minutes

##################################################
# Running Detection
##################################################

RUNNING_FRAME_THRESHOLD = 8