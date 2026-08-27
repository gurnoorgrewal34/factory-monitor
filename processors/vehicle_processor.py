import re

import cv2
import numpy as np

from huggingface_hub import (
    hf_hub_download,
)

from paddleocr import (
    PaddleOCR,
)

from ultralytics import (
    YOLO,
)


# ==========================================================
# LICENSE PLATE MODEL
#
# Preserved from original vehicle/ALPR implementation.
# ==========================================================

PLATE_REPO_ID = (
    "morsetechlab/"
    "yolov11-license-plate-detection"
)

VALID_PLATE_VARIANTS = {
    "n",
    "s",
    "m",
    "l",
    "x",
}


# ==========================================================
# COCO VEHICLE CLASSES
#
# 2 = car
# 3 = motorcycle
# 5 = bus
# 7 = truck
#
# Preserved from colleague's implementation.
# ==========================================================

VEHICLE_CLASSES = {

    2:
        "car",

    3:
        "motorcycle",

    5:
        "bus",

    7:
        "truck",
}


# ==========================================================
# DRAWING
# ==========================================================

BOX_COLOR = (
    60,
    200,
    60
)

PLATE_BOX_COLOR = (
    0,
    200,
    255
)

LABEL_BG_COLOR = (
    30,
    30,
    30
)

LABEL_TEXT_COLOR = (
    255,
    255,
    255
)


# ==========================================================
# LICENSE PLATE MODEL DOWNLOAD
# ==========================================================

def download_plate_weights(
    variant="n"
):

    if variant not in VALID_PLATE_VARIANTS:

        raise ValueError(
            "plate variant must be one of "
            f"{sorted(VALID_PLATE_VARIANTS)}, "
            f"got {variant!r}"
        )

    filename = (
        f"license-plate-finetune-"
        f"v1{variant}.pt"
    )

    print(
        "VEHICLE PROCESSOR -> "
        "Loading license plate model:",
        filename
    )

    return hf_hub_download(

        repo_id=
            PLATE_REPO_ID,

        filename=
            filename
    )


# ==========================================================
# CLEAN LICENSE PLATE TEXT
# ==========================================================

def clean_plate_text(
    raw
):

    text = (
        str(raw)
        .upper()
        .strip()
    )

    text = re.sub(
        r"[^A-Z0-9\- ]",
        "",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text


# ==========================================================
# PREPROCESS PLATE
#
# Preserves colleague's:
#
# - upscaling
# - LAB conversion
# - CLAHE contrast enhancement
# ==========================================================

def preprocess_plate_crop(
    crop,
    target_height=64
):

    if (
        crop is None
        or
        crop.size == 0
    ):

        return crop

    height, width = (
        crop.shape[:2]
    )

    if height < target_height:

        scale = (
            target_height
            /
            max(
                height,
                1
            )
        )

        new_width = max(
            int(
                width
                *
                scale
            ),
            1
        )

        crop = cv2.resize(

            crop,

            (
                new_width,
                target_height
            ),

            interpolation=
                cv2.INTER_CUBIC
        )

    lab = cv2.cvtColor(

        crop,

        cv2.COLOR_BGR2LAB
    )

    l_channel, a_channel, b_channel = (
        cv2.split(
            lab
        )
    )

    clahe = (
        cv2.createCLAHE(

            clipLimit=2.0,

            tileGridSize=(
                8,
                8
            )
        )
    )

    l_channel = (
        clahe.apply(
            l_channel
        )
    )

    crop = cv2.cvtColor(

        cv2.merge((

            l_channel,
            a_channel,
            b_channel

        )),

        cv2.COLOR_LAB2BGR
    )

    return crop


# ==========================================================
# OCR
# ==========================================================

def run_ocr(
    ocr,
    crop,
    min_score
):

    if (
        crop is None
        or
        crop.size == 0
    ):

        return (
            None,
            0.0
        )

    try:

        results = (
            ocr.predict(
                crop
            )
        )

    except Exception as exc:

        print(
            "VEHICLE OCR ERROR ->",
            repr(exc)
        )

        return (
            None,
            0.0
        )

    texts = []

    scores = []

    for result in results:

        rec_texts = (
            result.get(
                "rec_texts"
            )
            or
            []
        )

        rec_scores = (
            result.get(
                "rec_scores"
            )
            or
            []
        )

        for text, score in zip(
            rec_texts,
            rec_scores
        ):

            if (
                score >= min_score
                and
                str(text).strip()
            ):

                texts.append(
                    str(text)
                )

                scores.append(
                    float(score)
                )

    if not texts:

        return (
            None,
            0.0
        )

    combined = (
        clean_plate_text(
            " ".join(
                texts
            )
        )
    )

    if not combined:

        return (
            None,
            0.0
        )

    average_score = float(
        np.mean(
            scores
        )
    )

    return (
        combined,
        average_score
    )


# ==========================================================
# IOU
# ==========================================================

def iou(
    box_a,
    box_b
):

    ax1, ay1, ax2, ay2 = (
        box_a
    )

    bx1, by1, bx2, by2 = (
        box_b
    )

    ix1 = max(
        ax1,
        bx1
    )

    iy1 = max(
        ay1,
        by1
    )

    ix2 = min(
        ax2,
        bx2
    )

    iy2 = min(
        ay2,
        by2
    )

    intersection_width = max(
        0,
        ix2 - ix1
    )

    intersection_height = max(
        0,
        iy2 - iy1
    )

    intersection = (
        intersection_width
        *
        intersection_height
    )

    area_a = (
        max(
            0,
            ax2 - ax1
        )
        *
        max(
            0,
            ay2 - ay1
        )
    )

    area_b = (
        max(
            0,
            bx2 - bx1
        )
        *
        max(
            0,
            by2 - by1
        )
    )

    union = (
        area_a
        +
        area_b
        -
        intersection
    )

    if union <= 0:

        return 0.0

    return (
        intersection
        /
        union
    )


# ==========================================================
# TRACK
# ==========================================================

class VehicleTrack:

    __slots__ = (

        "id",
        "bbox",
        "cls_name",

        "plate_text",
        "plate_conf",
        "plate_bbox",

        "frames_since_ocr",
        "missed",
        
        "vehicle_alert_sent",
        "plate_alert_sent",
    )

    def __init__(
        self,
        track_id,
        bbox,
        cls_name
    ):

        self.id = (
            track_id
        )

        self.bbox = (
            bbox
        )

        self.cls_name = (
            cls_name
        )

        self.plate_text = (
            None
        )

        self.plate_conf = (
            0.0
        )

        self.plate_bbox = (
            None
        )

        # Force OCR on first sighting.
        self.frames_since_ocr = (
            10 ** 9
        )

        self.missed = (
            0
        )
        
        self.vehicle_alert_sent = False
        self.plate_alert_sent = False


# ==========================================================
# TRACKER
#
# Preserves colleague's lightweight IoU tracker.
# ==========================================================

class VehicleTracker:

    def __init__(
        self,
        iou_threshold=0.3,
        max_missed=15
    ):

        self.tracks = []

        self.next_id = 1

        self.iou_threshold = (
            iou_threshold
        )

        self.max_missed = (
            max_missed
        )
        
        
        

    def update(
        self,
        detections
    ):

        unmatched_tracks = set(
            range(
                len(
                    self.tracks
                )
            )
        )

        unmatched_detections = set(
            range(
                len(
                    detections
                )
            )
        )

        matches = []

        # --------------------------------------------------
        # Match existing tracks with current detections
        # --------------------------------------------------

        for track_index in list(
            unmatched_tracks
        ):

            best_detection_index = (
                None
            )

            best_iou = (
                self.iou_threshold
            )

            for detection_index in (
                unmatched_detections
            ):

                score = iou(

                    self.tracks[
                        track_index
                    ].bbox,

                    detections[
                        detection_index
                    ][0]
                )

                if score > best_iou:

                    best_iou = (
                        score
                    )

                    best_detection_index = (
                        detection_index
                    )

            if (
                best_detection_index
                is not None
            ):

                matches.append((

                    track_index,

                    best_detection_index

                ))

                unmatched_tracks.discard(
                    track_index
                )

                unmatched_detections.discard(
                    best_detection_index
                )

        # --------------------------------------------------
        # Update matched tracks
        # --------------------------------------------------

        for (
            track_index,
            detection_index
        ) in matches:

            self.tracks[
                track_index
            ].bbox = (
                detections[
                    detection_index
                ][0]
            )

            self.tracks[
                track_index
            ].cls_name = (
                detections[
                    detection_index
                ][1]
            )

            self.tracks[
                track_index
            ].missed = 0

        # --------------------------------------------------
        # Mark unmatched tracks
        # --------------------------------------------------

        for track_index in (
            unmatched_tracks
        ):

            self.tracks[
                track_index
            ].missed += 1

        # --------------------------------------------------
        # Create new tracks
        # --------------------------------------------------

        for detection_index in (
            unmatched_detections
        ):

            bbox, cls_name = (
                detections[
                    detection_index
                ]
            )

            self.tracks.append(

                VehicleTrack(

                    self.next_id,

                    bbox,

                    cls_name
                )
            )

            self.next_id += 1

        # --------------------------------------------------
        # Remove dead tracks
        # --------------------------------------------------

        self.tracks = [

            track

            for track
            in self.tracks

            if (
                track.missed
                <=
                self.max_missed
            )
        ]

        return (
            self.tracks
        )


# ==========================================================
# DRAW VEHICLE
# ==========================================================

def draw_vehicle_with_label(
    frame,
    box,
    label_text,
    box_color=BOX_COLOR
):

    x1, y1, x2, y2 = [

        int(value)

        for value
        in box
    ]

    cv2.rectangle(

        frame,

        (
            x1,
            y1
        ),

        (
            x2,
            y2
        ),

        box_color,

        2
    )

    font = (
        cv2.FONT_HERSHEY_SIMPLEX
    )

    font_scale = (
        0.7
    )

    thickness = (
        2
    )

    (
        text_width,
        text_height
    ), baseline = (

        cv2.getTextSize(

            label_text,

            font,

            font_scale,

            thickness
        )
    )

    padding = 6

    label_height = (
        text_height
        +
        baseline
        +
        padding * 2
    )

    label_width = (
        text_width
        +
        padding * 2
    )

    if (
        y1 - label_height
        >= 0
    ):

        label_y1 = (
            y1 - label_height
        )

        label_y2 = (
            y1
        )

    else:

        label_y1 = (
            y1
        )

        label_y2 = (
            y1 + label_height
        )

    label_x1 = (
        x1
    )

    label_x2 = (
        x1 + label_width
    )

    cv2.rectangle(

        frame,

        (
            label_x1,
            label_y1
        ),

        (
            label_x2,
            label_y2
        ),

        LABEL_BG_COLOR,

        -1
    )

    cv2.rectangle(

        frame,

        (
            label_x1,
            label_y1
        ),

        (
            label_x2,
            label_y2
        ),

        box_color,

        2
    )

    cv2.putText(

        frame,

        label_text,

        (
            label_x1 + padding,

            label_y2
            -
            baseline
            -
            padding // 2
        ),

        font,

        font_scale,

        LABEL_TEXT_COLOR,

        thickness,

        cv2.LINE_AA
    )


# ==========================================================
# DRAW PLATE
# ==========================================================

def draw_plate_box(
    frame,
    box
):

    x1, y1, x2, y2 = [

        int(value)

        for value
        in box
    ]

    cv2.rectangle(

        frame,

        (
            x1,
            y1
        ),

        (
            x2,
            y2
        ),

        PLATE_BOX_COLOR,

        2
    )


# ==========================================================
# VEHICLE PROCESSOR
#
# IMPORTANT:
#
# This class DOES NOT:
#
# - open camera
# - read VideoCapture
# - create its own while-loop
# - call imshow
# - create VideoWriter
#
# Your existing CameraRuntime owns all of that.
# ==========================================================

class VehicleProcessor:

    def __init__(
        self,
        vehicle_model_path,

        plate_variant="n",

        conf_vehicle=0.40,

        conf_plate=0.25,

        min_ocr_conf=0.50,

        image_size=640,

        ocr_language="en",

        rotated_plates=False,

        ocr_interval=10,

        track_iou=0.30,

        track_max_missed=15
    ):

        print(
            "========================================"
        )

        print(
            "VEHICLE PROCESSOR -> INITIALIZING"
        )

        # ==================================================
        # SETTINGS
        # ==================================================

        self.conf_vehicle = (
            conf_vehicle
        )

        self.conf_plate = (
            conf_plate
        )

        self.min_ocr_conf = (
            min_ocr_conf
        )

        self.image_size = (
            image_size
        )

        self.ocr_interval = max(
            int(
                ocr_interval
            ),
            1
            
        )

        # ==================================================
        # VEHICLE MODEL
        # ==================================================

        print(
            "VEHICLE PROCESSOR -> "
            "Loading vehicle model:",
            vehicle_model_path
        )

        self.vehicle_model = (
            YOLO(
                vehicle_model_path
            )
        )

        # ==================================================
        # LICENSE PLATE MODEL
        # ==================================================

        plate_weights = (
            download_plate_weights(
                plate_variant
            )
        )

        self.plate_model = (
            YOLO(
                plate_weights
            )
        )

        # ==================================================
        # OCR
        # ==================================================

        print(
            "VEHICLE PROCESSOR -> "
            "Loading PaddleOCR..."
        )

        self.ocr = (
            PaddleOCR(

                lang=
                    ocr_language,

                use_doc_orientation_classify=
                    False,

                use_doc_unwarping=
                    False,

                use_textline_orientation=
                    rotated_plates,

                # ==========================================
                # IMPORTANT:
                #
                # Disable MKL-DNN / oneDNN.
                #
                # Fixes Paddle CPU error:
                #
                # ConvertPirAttribute2RuntimeAttribute
                # not support ArrayAttribute<DoubleAttribute>
                # ==========================================

                enable_mkldnn=
                    False,

                device=
                    "cpu"
            )
        )

        # ==================================================
        # TRACKER
        # ==================================================

        self.tracker = (
            VehicleTracker(

                iou_threshold=
                    track_iou,

                max_missed=
                    track_max_missed
            )
        )

        print(
            "VEHICLE PROCESSOR -> READY"
        )

        print(
            "========================================"
        )

    # ======================================================
    # PROCESS ONE FRAME
    # ======================================================

    def process(
        self,
        frame
    ):

        if frame is None:

            return (
                frame,
                []
            )

        frame_height, frame_width = (
            frame.shape[:2]
        )

        # ==================================================
        # 1. VEHICLE DETECTION
        # ==================================================

        vehicle_results = (
            self.vehicle_model.predict(

                frame,

                classes=list(
                    VEHICLE_CLASSES.keys()
                ),

                conf=
                    self.conf_vehicle,

                imgsz=
                    self.image_size,

                verbose=
                    False
            )[0]
        )

        detections = []

        for box in (
            vehicle_results.boxes
        ):

            x1, y1, x2, y2 = (
                box.xyxy[
                    0
                ].tolist()
            )

            class_id = int(
                box.cls[
                    0
                ]
            )

            class_name = (
                VEHICLE_CLASSES.get(
                    class_id,
                    "vehicle"
                )
            )

            detections.append((

                (
                    x1,
                    y1,
                    x2,
                    y2
                ),

                class_name

            ))

        # ==================================================
        # 2. TRACK VEHICLES
        # ==================================================

        tracks = (
            self.tracker.update(
                detections
            )
        )

        events = []
        
        
        
        # ==================================================
        # VEHICLE DETECTION EVENTS
        #
        # Produce ONE event when a new tracked vehicle
        # becomes visible.
        #
        # OCR is NOT required for this.
        # ==================================================

        for track in tracks:

            if track.missed > 0:

                continue

            if not track.vehicle_alert_sent:

                events.append({

                    "type":
                        "vehicle_detected",

                    "title":
                        "VEHICLE DETECTED",

                    "message":
                        (
                            f"{track.cls_name.title()} "
                            f"detected"
                        ),

                    "vehicle_id":
                        track.id,

                    "vehicle_type":
                        track.cls_name,

                    "plate":
                        None,

                    "bbox": [

                        int(value)

                        for value
                        in track.bbox
                    ]
                })

                track.vehicle_alert_sent = True

        # ==================================================
        # 3. PLATE DETECTION + OCR
        # ==================================================

        for track in tracks:

            if track.missed > 0:

                continue

            track.frames_since_ocr += 1

            need_ocr = (

                track.plate_text
                is None

                or

                track.frames_since_ocr
                >=
                self.ocr_interval
            )

            if need_ocr:

                x1, y1, x2, y2 = [

                    int(value)

                    for value
                    in track.bbox
                ]

                padding = int(

                    0.05
                    *
                    max(
                        x2 - x1,
                        y2 - y1
                    )
                )

                vehicle_x1 = max(
                    0,
                    x1 - padding
                )

                vehicle_y1 = max(
                    0,
                    y1 - padding
                )

                vehicle_x2 = min(
                    frame_width,
                    x2 + padding
                )

                vehicle_y2 = min(
                    frame_height,
                    y2 + padding
                )

                vehicle_crop = frame[

                    vehicle_y1:
                    vehicle_y2,

                    vehicle_x1:
                    vehicle_x2
                ]

                if (
                    vehicle_crop.size
                    >
                    0
                ):

                    plate_results = (
                        self.plate_model.predict(

                            vehicle_crop,

                            conf=
                                self.conf_plate,

                            verbose=
                                False
                        )[0]
                    )

                    if (
                        len(
                            plate_results.boxes
                        )
                        >
                        0
                    ):

                        best_plate = max(

                            plate_results.boxes,

                            key=lambda box:
                                float(
                                    box.conf[
                                        0
                                    ]
                                )
                        )

                        (
                            plate_x1,
                            plate_y1,
                            plate_x2,
                            plate_y2
                        ) = (

                            best_plate
                            .xyxy[
                                0
                            ]
                            .tolist()
                        )

                        # ==================================
                        # Convert vehicle-crop coordinates
                        # back to full-frame coordinates
                        # ==================================

                        full_x1 = (
                            vehicle_x1
                            +
                            plate_x1
                        )

                        full_y1 = (
                            vehicle_y1
                            +
                            plate_y1
                        )

                        full_x2 = (
                            vehicle_x1
                            +
                            plate_x2
                        )

                        full_y2 = (
                            vehicle_y1
                            +
                            plate_y2
                        )

                        track.plate_bbox = (

                            full_x1,
                            full_y1,
                            full_x2,
                            full_y2
                        )

                        plate_padding = 4

                        crop_x1 = max(
                            0,
                            int(
                                full_x1
                            )
                            -
                            plate_padding
                        )

                        crop_y1 = max(
                            0,
                            int(
                                full_y1
                            )
                            -
                            plate_padding
                        )

                        crop_x2 = min(
                            frame_width,
                            int(
                                full_x2
                            )
                            +
                            plate_padding
                        )

                        crop_y2 = min(
                            frame_height,
                            int(
                                full_y2
                            )
                            +
                            plate_padding
                        )

                        plate_crop = frame[

                            crop_y1:
                            crop_y2,

                            crop_x1:
                            crop_x2
                        ]

                        plate_crop = (
                            preprocess_plate_crop(
                                plate_crop
                            )
                        )

                        text, score = (
                            run_ocr(

                                self.ocr,

                                plate_crop,

                                self.min_ocr_conf
                            )
                        )

                        if text:

                                # ==========================================
                                # SAVE RECOGNIZED NUMBER PLATE
                                # ==========================================

                                track.plate_text = (
                                    text
                                )

                                track.plate_conf = (
                                    score
                                )

                                # ==========================================
                                # NUMBER PLATE ALERT
                                #
                                # Send only ONCE for this tracked vehicle.
                                # ==========================================

                                if not track.plate_alert_sent:

                                    events.append({

                                        "type":
                                            "number_plate_detected",

                                        "title":
                                            "NUMBER PLATE DETECTED",

                                        "message":
                                            (
                                                f"{track.cls_name.title()} "
                                                f"plate detected: "
                                                f"{text}"
                                            ),

                                        "vehicle_id":
                                            track.id,

                                        "vehicle_type":
                                            track.cls_name,

                                        "plate":
                                            text,

                                        "plate_confidence":
                                            round(
                                                score,
                                                3
                                            ),

                                        "bbox": [

                                            int(value)

                                            for value
                                            in track.bbox
                                        ]
                                    })

                                    track.plate_alert_sent = True
                                

                track.frames_since_ocr = 0

        # ==================================================
        # 4. DRAW
        #
        # Preserve colleague's output appearance.
        # ==================================================

        for track in tracks:

            if track.missed > 0:

                continue

            if track.plate_text:

                label = (

                    f"{track.plate_text} "
                    f"({track.plate_conf:.2f})"
                )

            else:

                label = (
                    "reading plate..."
                )

            draw_vehicle_with_label(

                frame,

                track.bbox,

                (
                    f"#{track.id} "
                    f"{track.cls_name}: "
                    f"{label}"
                )
            )

            if (
                track.plate_bbox
                is not None
            ):

                draw_plate_box(

                    frame,

                    track.plate_bbox
                )

        # ==================================================
        # RETURN
        # ==================================================

        return (
            frame,
            events
        )