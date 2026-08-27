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
    "car_num6.mp4"
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

RUNNING_MOTION_THRESHOLD = 0.35   # 0.18

RUNNING_FRAME_THRESHOLD = 12     # 8

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


##################################################
# AFTER-SHIFT DETECTION
##################################################

# Base date used when converting prerecorded-video
# time into a simulated real-world datetime.
#
# Format:
# YYYY-MM-DD
#
# This is mainly useful for video testing.

AFTER_SHIFT_BASE_DATE = "2026-08-17"


# Shift end time.
# Change this to the actual site shift end time.

AFTER_SHIFT_SHIFT_END_TIME = "11:52:10"


# For prerecorded video only.
# This tells the system what clock time frame 0 represents.
#
# Example:
# "10:31:00" means the video starts at 10:31 AM.

AFTER_SHIFT_VIDEO_START_TIME = "11:52:00"


# How long a person must remain in an
# after-shift monitored zone before confirmation.

AFTER_SHIFT_CONFIRM_SECONDS = 1.0


# Tolerance for a brief tracking/detection disappearance.

AFTER_SHIFT_GRACE_SECONDS = 2.0

##################################################
# ALERT DISPLAY DURATIONS
##################################################

AFTER_SHIFT_ALERT_DISPLAY_SECONDS = 5.0

FALL_ALERT_DISPLAY_SECONDS = 8.0




DEBUG = False



##################################################
# PERFORMANCE / MODEL SCHEDULING
##################################################

# Core person tracking
TRACKER_FRAME_INTERVAL = 1

# PPE / behaviour detectors
HELMET_FRAME_INTERVAL = 2

PHONE_FRAME_INTERVAL = 2

# Expensive detectors
FIRE_SMOKE_FRAME_INTERVAL = 2

SMOKING_FRAME_INTERVAL = 2

# Safety detector
FALL_FRAME_INTERVAL = 2

# General pose detector
POSE_FRAME_INTERVAL = 2


##################################################
# VEHICLE + LICENSE PLATE DETECTION
##################################################

VEHICLE_CONFIDENCE = 0.40

VEHICLE_PLATE_CONFIDENCE = 0.25

VEHICLE_OCR_CONFIDENCE = 0.50

VEHICLE_IMAGE_SIZE = 640

VEHICLE_OCR_INTERVAL = 10

VEHICLE_TRACK_IOU = 0.30

VEHICLE_TRACK_MAX_MISSED = 15

VEHICLE_PLATE_VARIANT = "n"

VEHICLE_OCR_LANGUAGE = "en"

VEHICLE_ROTATED_PLATES = False


##################################################
# VEHICLE PROCESSING SCHEDULING
##################################################

VEHICLE_FRAME_INTERVAL = 2