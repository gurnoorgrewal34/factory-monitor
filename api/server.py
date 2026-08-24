import os
import time
import asyncio

from queue import (
    Queue,
    Empty,
)

from typing import (
    List,
    Optional,
)

import cv2

from fastapi import (
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)

from fastapi.responses import (
    StreamingResponse,
)

from fastapi.middleware.cors import (
    CORSMiddleware,
)

from pydantic import (
    BaseModel,
    Field,
)

from app.camera_manager import (
    CameraManager,
)

from app.orchestrator import (
    Orchestrator,
)

from api.websocket_manager import (
    WebSocketManager,
)

from database.camera_repository import (
    CameraRepository,
)

from services.camera_service import (
    CameraService,
)

from services.rtsp_service import (
    RTSPService,
)
# ==================================================
# PROJECT PATHS
# ==================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

CAMERA_CONFIG = os.path.join(
    BASE_DIR,
    "config",
    "cameras.json"
)


# ==================================================
# FASTAPI APP
# ==================================================

app = FastAPI(
    title="Factory Monitoring API",
    version="1.2.0",
    description=(
        "Multi-camera factory behavioural "
        "monitoring API"
    )
)


# ==================================================
# CORS
# ==================================================

app.add_middleware(
    CORSMiddleware,

    # Development setting.
    # Restrict this in production.
    allow_origins=["http://192.168.1.8:5173"],

    allow_credentials=False,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ==================================================
# MANAGERS
# ==================================================

camera_repository = (
    CameraRepository()
)


camera_manager = CameraManager(

    CAMERA_CONFIG,

    BASE_DIR,

    repository=
        camera_repository
)

websocket_manager = (
    WebSocketManager()
)


# ==================================================
# ALERT QUEUE
# ==================================================

alert_queue = Queue()

alert_broadcaster_task = None



# ==================================================
# REQUEST MODELS
# ==================================================

class ModuleUpdateRequest(BaseModel):

    modules: List[str]


class CameraCreateRequest(
    BaseModel
):

    name: str = Field(
        min_length=1
    )

    # cctv / video / webcam
    # source_type: str = "cctv"

    # ----------------------------------------------
    # CCTV
    # ----------------------------------------------

    brand: Optional[str] = None

    camera_ip: Optional[str] = None

    username: Optional[str] = None

    password: Optional[str] = None

    rtsp_port: int = 554

    # ----------------------------------------------
    # CAMERA / NVR CHANNEL
    #
    # Optional.
    #
    # If not supplied, channel 1 is used.
    #
    # Useful when multiple CCTV feeds share:
    #
    # same IP
    # same username
    # same password
    #
    # but use different NVR/DVR channels.
    # ----------------------------------------------

    channel: Optional[int] = Field(
        default=1,
        ge=1
    )

    # Used only when:
    # brand = custom
    #
    # Keeping this for now internally.
    # Later frontend does not need to show it
    # for known camera brands.
    stream_path: Optional[str] = None

    # ----------------------------------------------
    # VIDEO
    # ----------------------------------------------

    # video_path: Optional[str] = None

    # ----------------------------------------------
    # WEBCAM
    # ----------------------------------------------

    # webcam_index: int = 0

    # ----------------------------------------------
    # AI
    # ----------------------------------------------

    # Multiple modules supported.
    #
    # Examples:
    #
    # ["helmet"]
    #
    # ["helmet", "fire", "smoke"]
    #
    # ["all"]

    modules: List[str] = [
        "all"
    ]
    


    # enabled: bool = True

    # save_output: bool = False

class CameraUpdateRequest(
    BaseModel
):

    name: Optional[str] = None

    enabled: Optional[bool] = None

    source_type: Optional[str] = None

    brand: Optional[str] = None

    camera_ip: Optional[str] = None

    username: Optional[str] = None

    password: Optional[str] = None

    rtsp_port: Optional[int] = None

    channel: Optional[int] = Field(
        default=None,
        ge=1
    )

    stream_path: Optional[str] = None

    # video_path: Optional[str] = None

    # webcam_index: Optional[int] = None

    zones_file: Optional[str] = None

    modules: Optional[List[str]] = None

    save_output: Optional[bool] = None


# ==================================================
# CAMERA LOOKUP
# ==================================================

def get_camera_or_404(
    camera_id: str
):

    camera = camera_manager.get_camera(
        camera_id
    )

    if camera is None:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Camera '{camera_id}' "
                f"not found"
            )
        )

    return camera



# ==================================================
# FRONTEND-SAFE CAMERA RESPONSE
#
# IMPORTANT:
# - Never return CCTV password
# - Never return raw unmasked RTSP credentials
# ==================================================

def build_camera_response(
    camera
):

    status = camera.get_status()

    config = camera.config

    camera_id = status.get(
        "camera_id"
    )

    source_type = status.get(
        "source_type"
    )

    return {

        # ==========================================
        # CAMERA
        # ==========================================

        "camera_id":
            camera_id,

        "name":
            status.get(
                "name"
            ),

        "enabled":
            status.get(
                "enabled"
            ),

        "running":
            status.get(
                "running"
            ),

        "source_type":
            source_type,

        # ==========================================
        # CCTV
        # ==========================================

        "brand":
            config.get(
                "brand"
            ),

        "camera_ip":
            config.get(
                "camera_ip"
            ),

        "rtsp_port":
            config.get(
                "rtsp_port"
            ),
            
        "channel":
            config.get(
                "channel",
                1
            ),    

        "stream_path":
            config.get(
                "stream_path"
            ),

        "rtsp_configured":
            bool(
                config.get(
                    "cctv_url"
                )
            ),

        "rtsp_url":
            RTSPService.mask_url(
                config.get(
                    "cctv_url"
                )
            ),

        # ==========================================
        # VIDEO
        # ==========================================

        "video_path":
            config.get(
                "video_path"
            ),

        # ==========================================
        # WEBCAM
        # ==========================================

        "webcam_index":
            config.get(
                "webcam_index"
            ),

        # ==========================================
        # AI
        # ==========================================

        "modules":
            status.get(
                "modules",
                []
            ),

        # ==========================================
        # PROCESSING STATUS
        # ==========================================

        "frames_processed":
            status.get(
                "frames_processed",
                0
            ),

        "save_output":
            status.get(
                "save_output",
                False
            ),

        "output_path":
            status.get(
                "output_path"
            ),

        "last_error":
            status.get(
                "last_error"
            ),

        # ==========================================
        # FRONTEND ENDPOINTS
        # ==========================================

        "stream_url":
            (
                f"/cameras/"
                f"{camera_id}/stream"
            ),

        "start_url":
            (
                f"/cameras/"
                f"{camera_id}/start"
            ),

        "stop_url":
            (
                f"/cameras/"
                f"{camera_id}/stop"
            ),

        "modules_url":
            (
                f"/cameras/"
                f"{camera_id}/modules"
            ),

        "websocket_url":
            "/ws/alerts"
    }

# ==================================================
# STANDARD SUCCESS RESPONSE
# ==================================================

def success_response(
    message,
    camera=None,
    **extra
):

    response = {

        "success":
            True,

        "message":
            message
    }

    if camera is not None:

        response[
            "camera"
        ] = build_camera_response(
            camera
        )

    response.update(
        extra
    )

    return response


# ==================================================
# MODULE VALIDATION
# ==================================================

def validate_modules(
    modules
):

    if not modules:

        raise HTTPException(
            status_code=400,
            detail=(
                "At least one module "
                "is required."
            )
        )

    modules = [

        module.lower().strip()

        for module in modules

        if module.strip()
    ]

    if not modules:

        raise HTTPException(
            status_code=400,
            detail=(
                "At least one valid module "
                "is required."
            )
        )

    if "all" in modules:

        return [
            "all"
        ]

    validator = (
        Orchestrator()
    )

    invalid = [

        module

        for module in modules

        if module
        not in validator.available_modules
    ]

    if invalid:

        raise HTTPException(
            status_code=400,
            detail={
                "message":
                    "Invalid module names",

                "invalid_modules":
                    invalid,

                "available_modules":
                    sorted(
                        validator
                        .available_modules
                    )
            }
        )

    return modules




# ==================================================
# CAMERA -> WEBSOCKET CALLBACK
# ==================================================

def camera_alert_callback(
    camera_id,
    alert
):

    alert_queue.put({

        "camera_id":
            camera_id,

        "event":
            "alert",

        "timestamp":
            time.time(),

        "data":
            alert
    })


# ==================================================
# REGISTER EXISTING CAMERA CALLBACKS
# ==================================================

def register_camera_callbacks():

    for status in (
        camera_manager.get_status()
    ):

        camera = (
            camera_manager
            .get_camera(
                status[
                    "camera_id"
                ]
            )
        )

        if camera is not None:

            camera.set_alert_callback(
                camera_alert_callback
            )


register_camera_callbacks()


# ==================================================
# WEBSOCKET BROADCASTER
# ==================================================

async def alert_broadcaster():

    while True:

        try:

            while True:

                try:

                    message = (
                        alert_queue
                        .get_nowait()
                    )

                except Empty:

                    break

                await (
                    websocket_manager
                    .broadcast(
                        message
                    )
                )

        except asyncio.CancelledError:

            break

        except Exception as exc:

            print(
                "WEBSOCKET BROADCAST ERROR ->",
                repr(exc)
            )

        await asyncio.sleep(
            0.05
        )


# ==================================================
# STARTUP
# ==================================================

@app.on_event("startup")
async def startup_event():

    global alert_broadcaster_task

    alert_broadcaster_task = (
        asyncio.create_task(
            alert_broadcaster()
        )
    )

    print(
        "API STARTUP -> READY"
    )


# ==================================================
# ROOT
# ==================================================

@app.get("/")
def root():

    return {

        "success":
            True,

        "service":
            "Factory Monitoring API",

        "version":
            "1.2.0",

        "status":
            "running",

        "docs":
            "/docs",

        "websocket":
            "/ws/alerts"
    }


# ==================================================
# HEALTH
# ==================================================

@app.get("/health")
def health():

    statuses = (
        camera_manager.get_status()
    )

    running = sum(

        1

        for camera
        in statuses

        if camera.get(
            "running"
        )
    )

    return {

        "success":
            True,

        "status":
            "ok",

        "configured_cameras":
            len(statuses),

        "running_cameras":
            running
    }


# ==================================================
# GET ALL CAMERAS
#
# Frontend receives everything it needs.
# ==================================================

@app.get("/cameras")
def cameras():

    camera_objects = []

    for status in (
        camera_manager
        .get_status()
    ):

        camera = (
            camera_manager
            .get_camera(
                status[
                    "camera_id"
                ]
            )
        )

        if camera is not None:

            camera_objects.append(
                build_camera_response(
                    camera
                )
            )

    running_count = sum(

        1

        for camera
        in camera_objects

        if camera[
            "running"
        ]
    )

    return {

        "success":
            True,

        "message":
            "Camera list retrieved successfully",

        "total_cameras":
            len(
                camera_objects
            ),

        "running_cameras":
            running_count,

        "cameras":
            camera_objects,

        "websocket_url":
            "/ws/alerts"
    }


# ============================
# ADD CAMERA
#
# FOR REAL SCENARIO
# =============================

@app.post(
    "/cameras",
    status_code=201
)
def create_camera(
    request: CameraCreateRequest
):

    try:

        # ==========================================
        # 1. VALIDATE REQUESTED AI MODULES
        # ==========================================

        modules = validate_modules(
            request.modules
        )

        # ==========================================
        # 2. CONVERT PYDANTIC REQUEST -> DICT
        # ==========================================

        request_data = (
            request.model_dump()
        )
        print(
            "SERVER REQUEST MODULES ->",
            request.modules
        )

        # ==========================================
        # KEEP INTERNAL MODULE ARCHITECTURE
        # AS A LIST
        #
        # Examples:
        #
        # ["helmet"]
        #
        # ["helmet", "fire"]
        #
        # ["all"]
        # ==========================================

        request_data[
            "modules"
        ] = modules

        # ==========================================
        # 3. BUILD NORMALIZED CAMERA CONFIG
        #
        # CameraService handles:
        #
        # - automatic camera ID
        # - CCTV configuration
        # - camera brand
        # - camera / NVR channel
        # - RTSP URL generation
        # ==========================================

        camera_config = (
            CameraService
            .build_camera_config(
                request_data
            )
        )

        # ==========================================
        # 4. SAVE TO POSTGRESQL
        #    + CREATE CAMERA RUNTIME
        # ==========================================

        camera = (
            camera_manager
            .add_camera(
                camera_config
            )
        )

        # ==========================================
        # 5. REGISTER WEBSOCKET CALLBACK
        # ==========================================

        camera.set_alert_callback(
            camera_alert_callback
        )

        # ==========================================
        # 6. SUCCESS RESPONSE
        # ==========================================

        return success_response(

            "Camera registered successfully",

            camera=camera
        )

    # ==============================================
    # FASTAPI / MODULE VALIDATION ERRORS
    # ==============================================

    except HTTPException:

        raise

    # ==============================================
    # BAD CAMERA CONFIGURATION
    # ==============================================

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    # ==============================================
    # UNEXPECTED ERROR
    # ==============================================

    except Exception as exc:

        print(
            "CAMERA REGISTRATION ERROR ->",
            repr(exc)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Camera registration failed: "
                f"{exc}"
            )
        )

# ==================================================
# GET CAMERA
# ==================================================

@app.get(
    "/cameras/{camera_id}"
)
def camera_status(
    camera_id: str
):

    camera = get_camera_or_404(
        camera_id
    )

    return success_response(

        "Camera status retrieved successfully",

        camera=camera
    )


# ==================================================
# UPDATE CAMERA CONFIG
# ==================================================

@app.put(
    "/cameras/{camera_id}"
)
def update_camera(
    camera_id: str,
    request: CameraUpdateRequest
):

    camera = get_camera_or_404(
        camera_id
    )

    if camera.running:

        raise HTTPException(
            status_code=409,
            detail=(
                "Stop the camera before "
                "updating configuration."
            )
        )

    updates = (
        request.model_dump(
            exclude_unset=True
        )
    )

    # ----------------------------------------------
    # Validate modules
    # ----------------------------------------------

    if (
        "modules" in updates
        and
        updates[
            "modules"
        ] is not None
    ):

        updates[
            "modules"
        ] = validate_modules(
            updates[
                "modules"
            ]
        )

    # ----------------------------------------------
    # Source type
    # ----------------------------------------------

    source_type = updates.get(

        "source_type",

        camera.config.get(
            "source_type"
        )
    )

    if source_type:

        source_type = (
            source_type
            .lower()
            .strip()
        )

        updates[
            "source_type"
        ] = source_type

    # ----------------------------------------------
    # CCTV connection changes
    # ----------------------------------------------

    cctv_fields = {

        "brand",
        "camera_ip",
        "username",
        "password",
        "rtsp_port",
        "channel",
        "stream_path"
    }

    if (
        source_type == "cctv"
        and
        any(
            field in updates
            for field in cctv_fields
        )
    ):

        camera_ip = updates.get(

            "camera_ip",

            camera.config.get(
                "camera_ip"
            )
        )

        rtsp_port = updates.get(

            "rtsp_port",

            camera.config.get(
                "rtsp_port",
                554
            )
        )
        
        brand = updates.get(

            "brand",

            camera.config.get(
                "brand",
                "other"
            )
        )


        channel = updates.get(

        "channel",

        camera.config.get(
            "channel",
            1
        )
    )

        stream_path = updates.get(

            "stream_path",

            camera.config.get(
                "stream_path"
            )
        )

        username = updates.get(
            "username"
        )

        password = updates.get(
            "password"
        )

        if (
            username is None
            or
            password is None
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "When updating CCTV "
                    "connection details, provide "
                    "both username and password."
                )
            )

        updates[
            "cctv_url"
        ] = RTSPService.build_url(

            camera_ip=camera_ip,

            username=username,

            password=password,

            rtsp_port=rtsp_port,
            
            channel=channel,

            stream_path=stream_path
        )

        updates[
            "camera_ip"
        ] = camera_ip

        updates[
            "rtsp_port"
        ] = rtsp_port
        
        
        updates[
            "brand"
        ] = brand


        updates[
            "channel"
        ] = channel
        
        updates[
            "stream_path"
        ] = stream_path

        # Never persist duplicate plain-text
        # username/password fields.
        updates.pop(
            "username",
            None
        )

        updates.pop(
            "password",
            None
        )

    try:

        camera = (
            camera_manager
            .update_camera(
                camera_id,
                updates
            )
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    except RuntimeError as exc:

        raise HTTPException(
            status_code=409,
            detail=str(exc)
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Could not update camera: "
                f"{exc}"
            )
        )

    return success_response(

        "Camera updated successfully",

        camera=camera
    )


# ==================================================
# DELETE CAMERA
# ==================================================

@app.delete(
    "/cameras/{camera_id}"
)
def delete_camera(
    camera_id: str
):

    camera = get_camera_or_404(
        camera_id
    )

    # Capture safe information before delete.
    deleted_camera = (
        build_camera_response(
            camera
        )
    )

    try:

        camera_manager.delete_camera(
            camera_id
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Could not delete camera: "
                f"{exc}"
            )
        )

    return {

        "success":
            True,

        "message":
            "Camera deleted successfully",

        "camera":
            deleted_camera
    }


# ==================================================
# START CAMERA
# ==================================================

@app.post(
    "/cameras/{camera_id}/start"
)
def start_camera(
    camera_id: str
):

    camera = get_camera_or_404(
        camera_id
    )

    started = camera.start()

    return success_response(

        (
            "Camera started successfully"
            if started
            else
            "Camera was already running"
        ),

        camera=camera,

        started=started
    )


# ==================================================
# STOP CAMERA
# ==================================================

@app.post(
    "/cameras/{camera_id}/stop"
)
def stop_camera(
    camera_id: str
):

    camera = get_camera_or_404(
        camera_id
    )

    stopped = camera.stop()

    return success_response(

        "Camera stopped successfully",

        camera=camera,

        stopped=stopped
    )


# ===================================
# ADD MODULES
# ===================================

@app.get(
    "/modules"
)
def get_modules():

    orchestrator = (
        Orchestrator()
    )

    modules = sorted(
        orchestrator.available_modules
    )

    return {

        "success":
            True,

        "message":
            "Available modules retrieved successfully",

        "total":
            len(modules),

        "modules":
            modules
    }
# ==================================================
# UPDATE MODULES
# ==================================================

@app.put(
    "/cameras/{camera_id}/modules"
)
def update_camera_modules(
    camera_id: str,
    request: ModuleUpdateRequest
):

    camera = get_camera_or_404(
        camera_id
    )

    if camera.running:

        raise HTTPException(
            status_code=409,
            detail=(
                "Stop the camera before "
                "changing modules."
            )
        )

    modules = validate_modules(
        request.modules
    )

    try:

        camera = (
            camera_manager
            .update_camera(
                camera_id,
                {
                    "modules":
                        modules
                }
            )
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Could not update modules: "
                f"{exc}"
            )
        )

    return success_response(

        "Camera modules updated successfully",

        camera=camera
    )

# ==================================================
# GET CAMERA BRANDS
#
# Frontend will call this API to create
# the CCTV brand dropdown.
#
# Example:
#
# Hikvision
# Dahua
# CP Plus
# Axis
# Uniview
# Other / Unknown
# ==================================================

@app.get(
    "/camera-brands"
)
def get_camera_brands():

    brands = [

        {
            "key":
                "hikvision",

            "display_name":
                "Hikvision"
        },

        {
            "key":
                "dahua",

            "display_name":
                "Dahua"
        },

        {
            "key":
                "cpplus",

            "display_name":
                "CP Plus"
        },

        {
            "key":
                "axis",

            "display_name":
                "Axis"
        },

        {
            "key":
                "uniview",

            "display_name":
                "Uniview"
        },

        {
            "key":
                "other",

            "display_name":
                "Other / Unknown"
        }
    ]

    return {

        "success":
            True,

        "message":
            "Available camera brands "
            "retrieved successfully",

        "total":
            len(
                brands
            ),

        "brands":
            brands
    }
    
    
# ==================================================
# VIDEO STREAM GENERATOR
# ==================================================

def generate_camera_stream(
    camera
):

    while True:

        frame = (
            camera
            .get_latest_frame()
        )

        if frame is None:

            if not camera.running:

                break

            time.sleep(
                0.05
            )

            continue

        success, encoded_frame = (
            cv2.imencode(

                ".jpg",

                frame,

                [
                    cv2.IMWRITE_JPEG_QUALITY,
                    80
                ]
            )
        )

        if not success:

            time.sleep(
                0.02
            )

            continue

        frame_bytes = (
            encoded_frame
            .tobytes()
        )

        yield (

            b"--frame\r\n"

            b"Content-Type: "
            b"image/jpeg\r\n\r\n"

            +

            frame_bytes

            +

            b"\r\n"
        )

        time.sleep(
            0.03
        )


# ==================================================
# CAMERA STREAM
# ==================================================

@app.get(
    "/cameras/{camera_id}/stream"
)
def stream_camera(
    camera_id: str
):

    camera = get_camera_or_404(
        camera_id
    )

    if not camera.running:

        raise HTTPException(
            status_code=409,
            detail=(
                f"Camera '{camera_id}' "
                f"is not running."
            )
        )

    return StreamingResponse(

        generate_camera_stream(
            camera
        ),

        media_type=(
            "multipart/x-mixed-replace;"
            "boundary=frame"
        )
    )


# ==================================================
# WEBSOCKET
# ==================================================

@app.websocket(
    "/ws/alerts"
)
async def websocket_alerts(
    websocket: WebSocket
):

    await websocket_manager.connect(
        websocket
    )

    print(
        "WEBSOCKET -> Client connected"
    )

    try:

        while True:

            await (
                websocket
                .receive_text()
            )

    except WebSocketDisconnect:

        websocket_manager.disconnect(
            websocket
        )

        print(
            "WEBSOCKET -> Client disconnected"
        )

    except Exception:

        websocket_manager.disconnect(
            websocket
        )


# ==================================================
# SHUTDOWN
# ==================================================

@app.on_event("shutdown")
async def shutdown_event():

    global alert_broadcaster_task

    print(
        "API SHUTDOWN -> "
        "Stopping cameras..."
    )

    camera_manager.stop_all()

    if alert_broadcaster_task is not None:

        alert_broadcaster_task.cancel()

        try:

            await alert_broadcaster_task

        except asyncio.CancelledError:

            pass

    print(
        "API SHUTDOWN -> Complete"
    )