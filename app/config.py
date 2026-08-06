import os

# ===============================
# Project Root
# ===============================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ===============================
# Model
# ===============================

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "yolo11n.pt"
)

# ===============================
# Video
# ===============================

VIDEO_PATH = os.path.join(
    BASE_DIR,
    "datasets",
    "raw_videos",
    "fire3.mp4"
)

# ===============================
# YOLO Settings
# ===============================

CONFIDENCE = 0.40

SHOW_CONFIDENCE = True

SHOW_LABELS = True

WINDOW_NAME = "Factory Monitoring System"

# ===============================
# Behaviour Settings
# ===============================

LOITERING_TIME = 10        # 2 minutes

SOCIAL_DISTANCE = 120        # pixels

SOCIAL_TIME = 60            # 1 minute


# -----------------------------------------
# Social Loitering
# -----------------------------------------

SOCIAL_DISTANCE = 120      # pixels

SOCIAL_TIME = 20           # seconds

SOCIAL_SPEED = 25          # px/sec


##################################################
# Phone Detection
##################################################

PHONE_CLASS_ID = 67

PHONE_CONFIDENCE = 0.25

PHONE_DISTANCE_THRESHOLD = 120

##################################################
# Running Detection
##################################################

# Average speed (pixels/sec) above which a person is considered running
RUNNING_SPEED = 80

# Number of consecutive frames required
RUNNING_FRAME_THRESHOLD = 8


##################################################
# Activity Detection
##################################################

# Average speed (pixels/sec)
STANDING_SPEED = 5

SLOW_WORK_SPEED = 25

RUNNING_SPEED = 80

# Seconds before considering idle
IDLE_TIME = 20