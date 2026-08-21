import os
import time
import asyncio

from queue import (
    Queue,
    Empty,
)

from typing import List

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

from fastapi.middleware.cors import CORSMiddleware

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
# FASTAPI APPLICATION
# ==================================================

app = FastAPI(

    title=(
        "Factory Monitoring API"
    ),

    version="1.0.0",

    description=(
        "Multi-camera factory behavioural "
        "monitoring API"
    )
)


# ==================================================
# CORS
#
# Development configuration.
#
# Allows frontend running on another port/machine
# to call this API.
#
# IMPORTANT:
# In production replace * with the actual frontend
# domain.
# ==================================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=[
        "*"
    ],

    allow_credentials=False,

    allow_methods=[
        "*"
    ],

    allow_headers=[
        "*"
    ],
)


# ==================================================
# CAMERA MANAGER
# ==================================================

camera_manager = (
    CameraManager(
        CAMERA_CONFIG,
        BASE_DIR
    )
)


# ==================================================
# WEBSOCKET MANAGER
# ==================================================

websocket_manager = (
    WebSocketManager()
)


# ==================================================
# THREAD-SAFE ALERT QUEUE
#
# CameraRuntime executes inside normal threads.
#
# FastAPI/WebSocket executes inside asyncio.
#
# This queue safely bridges those two worlds.
# ==================================================

alert_queue = Queue()


# ==================================================
# BACKGROUND TASK REFERENCE
# ==================================================

alert_broadcaster_task = None


# ==================================================
# REQUEST MODELS
# ==================================================

class ModuleUpdateRequest(
    BaseModel
):

    modules: List[str]


# ==================================================
# CAMERA HELPER
# ==================================================

def get_camera_or_404(
    camera_id: str
):

    camera = (
        camera_manager
        .get_camera(
            camera_id
        )
    )

    if camera is None:

        raise HTTPException(

            status_code=404,

            detail=(
                f"Camera "
                f"'{camera_id}' "
                f"not found"
            )
        )

    return camera


# ==================================================
# CAMERA -> WEBSOCKET CALLBACK
#
# IMPORTANT:
# This function runs from CameraRuntime thread.
#
# Therefore:
# DO NOT await here.
# DO NOT call WebSocket directly here.
#
# Just put the event in Queue.
# ==================================================

def camera_alert_callback(
    camera_id,
    alert
):

    message = {

        "camera_id":
            camera_id,

        "event":
            "alert",

        "timestamp":
            time.time(),

        "data":
            alert
    }

    alert_queue.put(
        message
    )


# ==================================================
# REGISTER CALLBACK ON EVERY CAMERA
# ==================================================

def register_camera_callbacks():

    camera_statuses = (
        camera_manager
        .get_status()
    )

    for status in camera_statuses:

        camera_id = status[
            "camera_id"
        ]

        camera = (
            camera_manager
            .get_camera(
                camera_id
            )
        )

        if camera is not None:

            camera.set_alert_callback(
                camera_alert_callback
            )


register_camera_callbacks()


# ==================================================
# WEBSOCKET BACKGROUND BROADCASTER
# ==================================================

async def alert_broadcaster():

    while True:

        try:

            ##################################################
            # Drain all currently waiting events.
            ##################################################

            while True:

                try:

                    message = (
                        alert_queue.get_nowait()
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

        ##################################################
        # Avoid busy-looping CPU.
        ##################################################

        await asyncio.sleep(
            0.05
        )


# ==================================================
# STARTUP
# ==================================================

@app.on_event(
    "startup"
)
async def startup_event():

    global alert_broadcaster_task

    print(
        "API STARTUP -> "
        "Starting alert broadcaster"
    )

    alert_broadcaster_task = (
        asyncio.create_task(
            alert_broadcaster()
        )
    )


# ==================================================
# ROOT
# ==================================================

@app.get("/")
def root():

    return {

        "service":
            "Factory Monitoring API",

        "version":
            "1.0.0",

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

    return {

        "status":
            "ok",

        "configured_cameras":
            len(
                camera_manager
                .get_status()
            )
    }


# ==================================================
# ALL CAMERAS
# ==================================================

@app.get("/cameras")
def cameras():

    return {

        "cameras":
            camera_manager
            .get_status()
    }


# ==================================================
# CAMERA STATUS
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

    return camera.get_status()


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

    return {

        "camera_id":
            camera_id,

        "started":
            started,

        "status":
            camera.get_status()
    }


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

    return {

        "camera_id":
            camera_id,

        "stopped":
            stopped,

        "status":
            camera.get_status()
    }


# ==================================================
# UPDATE CAMERA MODULES
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

    ##################################################
    # Camera must be stopped.
    ##################################################

    if camera.running:

        raise HTTPException(

            status_code=409,

            detail=(
                "Stop the camera before "
                "changing modules."
            )
        )

    requested_modules = [

        module.lower().strip()

        for module
        in request.modules

        if module.strip()
    ]

    if not requested_modules:

        raise HTTPException(

            status_code=400,

            detail=(
                "At least one module "
                "is required."
            )
        )

    ##################################################
    # ALL MODE
    ##################################################

    if "all" in requested_modules:

        requested_modules = [
            "all"
        ]

    else:

        validator = (
            Orchestrator()
        )

        invalid_modules = [

            module

            for module
            in requested_modules

            if module
            not in validator.available_modules
        ]

        if invalid_modules:

            raise HTTPException(

                status_code=400,

                detail={

                    "message":
                        "Invalid module names",

                    "invalid_modules":
                        invalid_modules,

                    "available_modules":
                        sorted(
                            validator
                            .available_modules
                        )
                }
            )

    ##################################################
    # Update in-memory camera configuration.
    #
    # Next POST /start rebuilds FrameProcessor with
    # the newly selected models.
    ##################################################

    camera.config[
        "modules"
    ] = requested_modules

    return {

        "camera_id":
            camera_id,

        "modules":
            requested_modules,

        "message":
            (
                "Modules updated. "
                "Start the camera to build "
                "the pipeline with this "
                "configuration."
            )
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

        ##################################################
        # Waiting for first frame
        ##################################################

        if frame is None:

            if not camera.running:

                break

            time.sleep(
                0.05
            )

            continue

        ##################################################
        # JPEG ENCODE
        ##################################################

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

        ##################################################
        # MJPEG RESPONSE
        ##################################################

        yield (

            b"--frame\r\n"

            b"Content-Type: "
            b"image/jpeg\r\n\r\n"

            +

            frame_bytes

            +

            b"\r\n"
        )

        ##################################################
        # Don't waste CPU refreshing browser faster than
        # useful.
        ##################################################

        time.sleep(
            0.03
        )


# ==================================================
# PROCESSED CAMERA STREAM
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

                f"Camera "
                f"'{camera_id}' "
                f"is not running. "

                f"Start it first using "
                f"POST /cameras/"
                f"{camera_id}/start"
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
# WEBSOCKET ALERTS
# ==================================================

@app.websocket(
    "/ws/alerts"
)
async def websocket_alerts(
    websocket: WebSocket
):

    await (
        websocket_manager
        .connect(
            websocket
        )
    )

    print(
        "WEBSOCKET -> "
        "Client connected"
    )

    try:

        ##################################################
        # Keep connection alive and detect disconnect.
        #
        # Frontend doesn't have to continuously send
        # anything. This simply waits for messages /
        # disconnect events.
        ##################################################

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
            "WEBSOCKET -> "
            "Client disconnected"
        )

    except Exception:

        websocket_manager.disconnect(
            websocket
        )


# ==================================================
# APPLICATION SHUTDOWN
# ==================================================

@app.on_event(
    "shutdown"
)
async def shutdown_event():

    global alert_broadcaster_task

    print(
        "API SHUTDOWN -> "
        "Stopping cameras..."
    )

    camera_manager.stop_all()

    ##################################################
    # Stop broadcaster
    ##################################################

    if alert_broadcaster_task is not None:

        alert_broadcaster_task.cancel()

        try:

            await alert_broadcaster_task

        except asyncio.CancelledError:

            pass

    print(
        "API SHUTDOWN -> "
        "Complete"
    )