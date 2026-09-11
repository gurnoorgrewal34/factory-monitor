import os
import time
import asyncio
import json

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
from api.dashboard_routes import (
    router as dashboard_router,
)
from pydantic import (
    BaseModel,
    Field,
)
from zones.zone_engine import (
    ZoneEngine,
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

from api.user_routes import (
    router as user_router,
)

from api.auth_routes import (
    router as auth_router,
)

from services.organization_service import (
    OrganizationService,
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


from alerts.alert_log_store import (
    AlertLogStore,
)

from alerts.alert_formatter import (
    AlertFormatter,
)


from api.ai_profile_routes import (
    router as ai_profile_router,
)


from api.organization_routes import (
    router as organization_router,
)
from api.role_routes import (
    router as role_router,
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

# API ROUTES
app.include_router(
    user_router
)

app.include_router(
    auth_router
)
app.include_router(
    organization_router
)


organization_service = (
    OrganizationService()
)

app.include_router(
    dashboard_router
)


app.include_router(
    ai_profile_router
)


app.include_router(
    role_router
)
# ==================================================
# CORS
# ==================================================

app.add_middleware(
    CORSMiddleware,

    # Development setting.
    # Restrict this in production.
    # allow_origins=["http://192.168.1.2:8443"], 
    
        allow_origins=[
        "http://192.168.1.4:8443",
        "https://192.168.1.4:8443",
        "http://localhost:8443",
        "https://localhost:8443",
        "http://127.0.0.4:8443",
        "https://127.0.0.4:8443",
    ],


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

app.state.camera_manager = camera_manager

websocket_manager = (
    WebSocketManager()
)


# ==================================================
# ALERT QUEUE
# ==================================================

# ==================================================
# LIVE ALERT STREAM QUEUE
#
# Used by SSE /alerts/stream.
# ==================================================

alert_stream_queue = Queue()

# ==================================================
# ALERT LOG STORE
#
# Temporary in-memory history for frontend.
#
# Does NOT replace:
#
# - AlertManager
# - AlertOverlay
# - WebSocket
# ==================================================

alert_log_store = (
    AlertLogStore(
        max_logs=300
    )
)

# ==================================================
# REQUEST MODELS
# ==================================================

class ModuleUpdateRequest(BaseModel):

    modules: List[str]



# ===================================================
# FOR ZONE API
# ===================================================

class ZoneCreateRequest(
    BaseModel
):

    name: str = Field(
        min_length=1
    )

    points: List[List[int]]

    color: Optional[List[int]] = None

    # normal / restricted
    zone_type: str = "normal"


class ZoneUpdateRequest(
    BaseModel
):

    name: Optional[str] = None

    points: Optional[List[List[int]]] = None

    color: Optional[List[int]] = None

    # normal / restricted
    zone_type: str = "normal"
    
    

class CameraCreateRequest(
        BaseModel
    ):

        # ==================================================
        # CAMERA IDENTITY
        # ==================================================

        name: str = Field(
            min_length=1
        )

        brand: Optional[str] = None

        resolution: Optional[str] = None

        camera_model: Optional[str] = None


        # ==================================================
        # CCTV CONNECTION
        # ==================================================

        camera_ip: Optional[str] = None

        username: Optional[str] = None

        password: Optional[str] = None

        rtsp_port: int = 554

        channel: Optional[int] = Field(
            default=1,
            ge=1
        )

        stream_path: Optional[str] = None


        # ==================================================
        # DEPLOYMENT LOCATION
        # ==================================================

        # plant_id: Optional[int] = Field(
        #     default=None,
        #     gt=0
        # )

        # department_id: Optional[int] = Field(
        #     default=None,
        #     gt=0
        # )

        # workstation_id: Optional[int] = Field(
        #     default=None,
        #     gt=0
        # )
        
        company_id: int
        company_name: str

        plant_id: int
        plant_name: str

        department_id: int
        department_name: str

        workstation_id: int
        workstation_name: str


        # ==================================================
        # AI MODULES
        #
        # IMPORTANT:
        # Existing runtime architecture remains unchanged.
        # ==================================================

        modules: List[str] = [
            "all"
        ]


        # ==================================================
        # CAMERA STATUS
        # ==================================================

        enabled: bool = True

        status: str = "inactive"
        # ==================================================
        # NOTIFICATIONS
        # ==================================================

        notifications_enabled: bool = False


    

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
    
    status: Optional[str] = None

    # video_path: Optional[str] = None

    # webcam_index: Optional[int] = None

    zones_file: Optional[str] = None

    modules: Optional[List[str]] = None

    save_output: Optional[bool] = None
    
    
    
    resolution: Optional[str] = None

    camera_model: Optional[str] = None

    # plant_id: Optional[int] = Field(
    #     default=None,
    #     gt=0
    # )

    # department_id: Optional[int] = Field(
    #     default=None,
    #     gt=0
    # )

    # workstation_id: Optional[int] = Field(
    #     default=None,
    #     gt=0
    # )
    
    company: Optional[str] = None
    
    plant: Optional[str] = None

    department: Optional[str] = None

    workstation: Optional[str] = None

    notifications_enabled: Optional[bool] = None


# ==================================================
# CAMERA LOOKUP
# ==================================================

def get_camera_or_404(
    camera_id: str
):

    # Keep runtime synchronized with PostgreSQL.
    camera_manager.sync_with_repository()

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



def get_camera_zone_engine(
    camera_id
):

    camera = get_camera_or_404(
        camera_id
    )

    zones_file = (
        camera.config.get(
            "zones_file"
        )
        or
        (
            f"zones/data/"
            f"{camera_id}.json"
        )
    )

    if not os.path.isabs(
        zones_file
    ):

        zones_file = os.path.join(
            BASE_DIR,
            zones_file
        )

    return ZoneEngine(
        zones_file
    )
    
    
    

    
# ==================================================
# FRONTEND-SAFE CAMERA RESPONSE
#
# IMPORTANT:
# - Never return CCTV password
# - Never return raw unmasked RTSP credentials
# ==================================================
# ==================================================
# CAMERA DISPLAY STATUS
# ==================================================

def get_camera_display_status(
    camera
):

    configured_status = (
        str(
            camera.config.get(
                "status",
                "inactive"
            )
        )
        .strip()
        .lower()
    )

    if configured_status not in {
        "active",
        "inactive",
    }:
        return "inactive"

    return configured_status

def build_camera_response(
    camera
):

    status = camera.get_status()

    config = camera.config
    
    
    display_status = (
            get_camera_display_status(
                camera
            )
        )
    
    
    
    # ==============================================
    # KEEP DATABASE STATUS SYNCHRONIZED
    # ==============================================

    


    location = (
            organization_service
            .get_camera_location_details(

                plant_id=
                    config.get(
                        "plant_id"
                    ),

                department_id=
                    config.get(
                        "department_id"
                    ),

                workstation_id=
                    config.get(
                        "workstation_id"
                    )
            )
        )

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
            
        "status":
            display_status,

        "source_type":
            source_type,


        # ==========================================
        # CAMERA METADATA
        # ==========================================

        "resolution":
            config.get(
                "resolution"
            ),

        "camera_model":
            config.get(
                "camera_model"
            ),


        # ==========================================
        # DEPLOYMENT LOCATION
        # ==========================================

        # ==========================================
        # DEPLOYMENT LOCATION
        # ==========================================

        "company_id":
            location.get(
                "company_id"
            ),

        "company_name":
            location.get(
                "company_name"
            ),

        "plant_id":
            location.get(
                "plant_id"
            ),

        "plant_name":
            location.get(
                "plant_name"
            ),

        "department_id":
            location.get(
                "department_id"
            ),

        "department_name":
            location.get(
                "department_name"
            ),

        "workstation_id":
            location.get(
                "workstation_id"
            ),

        "workstation_name":
            location.get(
                "workstation_name"
            ),


        # ==========================================
        # NOTIFICATIONS
        # ==========================================

        "notifications_enabled":
            config.get(
                "notifications_enabled",
                False
            ),


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

        "username":
            config.get(
                "username"
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


def validate_camera_status(
    status
):

    if status is None:

        return None

    status = (
        str(status)
        .strip()
        .lower()
    )

    allowed_statuses = {
        "active",
        "inactive",
        
    }

    if status not in allowed_statuses:

        raise HTTPException(
            status_code=400,
            detail={
                "message":
                    "Invalid camera status",

                "allowed_statuses":
                    sorted(
                        allowed_statuses
                    )
            }
        )

    return status

# ==================================================
# CAMERA -> WEBSOCKET CALLBACK
# ==================================================

def camera_alert_callback(
    camera_id,
    alert
):

    # ==================================================
    # IGNORE EMPTY / INVALID ALERTS
    # ==================================================

    if alert is None:

        return


    if isinstance(
        alert,
        dict
    ):

        if not alert:

            return


        alert_type = (

            alert.get("type")
            or
            alert.get("alert_type")
        )


        if not alert_type:

            return


        normalized_type = (
            str(alert_type)
            .strip()
            .lower()
        )


        # ----------------------------------------------
        # These are NOT real alerts
        # ----------------------------------------------

        if normalized_type in (

            "",
            "none",
            "normal",
            "unknown",
            "no alert",
            "no_alert"

        ):

            return


    elif isinstance(
        alert,
        str
    ):

        alert = alert.strip()


        if not alert:

            return


        if alert.lower() in (

            "none",
            "normal",
            "unknown",
            "no alert",
            "no_alert"

        ):

            return


    else:

        return


    # ==================================================
    # GENERATE ALERT ID
    # ==================================================

    alert_id = (
        alert_log_store
        .next_id()
    )


    # ==================================================
    # STANDARDIZE ALERT
    # ==================================================

    message = (
        AlertFormatter
        .format(

            alert_id=
                alert_id,

            camera_id=
                camera_id,

            alert=
                alert
        )
    )


    # ==================================================
    # STORE REAL ALERT IN RECENT HISTORY
    # ==================================================

    alert_log_store.add(
        message
    )


    # ==================================================
    # PUSH REAL ALERT TO WEBSOCKET
    # ==================================================

    alert_stream_queue.put(
        message
    )


    print(
        "LIVE ALERT ->",
        message
    )
    
# ==================================================
# REGISTER EXISTING CAMERA CALLBACKS
# ==================================================

def register_camera_callbacks():

    for status_data in (
        camera_manager.get_status()
    ):

        camera = (
            camera_manager
            .get_camera(
                status_data[
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


# ==================================================
# STARTUP
# ==================================================

@app.on_event("startup")
async def startup_event():

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
# Main Camera Monitoring API
# ==================================================

# ==================================================
# GET ALL CAMERAS
#
# Main Camera Monitoring API
#
# Supports:
# - Plant filter
# - Department filter
# - Workstation filter
# - Search
# - Status filter
# - Online / Standby / Offline summary
# ==================================================

@app.get(
    "/cameras"
)
def cameras(
    plant_id: Optional[int] = None,
    department_id: Optional[int] = None,
    workstation_id: Optional[int] = None,
    search: Optional[str] = None,
    status: Optional[str] = None
):

    # ==============================================
    # 1. VALIDATE STATUS FILTER
    # ==============================================

    status_value = None

    if status:

        status_value = (
            status
            .strip()
            .lower()
        )

        allowed_statuses = {
            "active",
            
            "inactive",
        }

        if (
            status_value
            not in allowed_statuses
        ):

            raise HTTPException(
                status_code=400,
                detail={
                    "message":
                        "Invalid camera status",

                    "allowed_statuses":
                        sorted(
                            allowed_statuses
                        )
                }
            )


    # ==============================================
    # 2. NORMALIZE SEARCH
    # ==============================================

    search_value = None

    if search:

        search_value = (
            search
            .strip()
            .lower()
        )
        
        
    # ==============================================
    # SYNC CAMERA RUNTIME WITH POSTGRESQL
    #
    # PostgreSQL is the source of truth.
    # Removes cameras that were manually deleted
    # from the database.
    # ==============================================

    camera_manager.sync_with_repository()


    # ==============================================
    # 3. BUILD CAMERA LIST
    # ==============================================

    camera_objects = []

    for status_data in (
        camera_manager
        .get_status()
    ):

        camera = (
            camera_manager
            .get_camera(
                status_data[
                    "camera_id"
                ]
            )
        )

        if camera is None:
            continue


        config = (
            camera.config
        )


        # ==========================================
        # PLANT FILTER
        # ==========================================

        if (
            plant_id is not None
            and
            config.get(
                "plant_id"
            )
            !=
            plant_id
        ):
            continue


        # ==========================================
        # DEPARTMENT FILTER
        # ==========================================

        if (
            department_id is not None
            and
            config.get(
                "department_id"
            )
            !=
            department_id
        ):
            continue


        # ==========================================
        # WORKSTATION FILTER
        # ==========================================

        if (
            workstation_id is not None
            and
            config.get(
                "workstation_id"
            )
            !=
            workstation_id
        ):
            continue


        # ==========================================
        # FRONTEND-SAFE CAMERA RESPONSE
        #
        # This already contains:
        #
        # plant_id
        # plant_name
        # department_id
        # department_name
        # workstation_id
        # workstation_name
        # status
        # modules
        # stream_url
        # etc.
        # ==========================================

        camera_data = (
            build_camera_response(
                camera
            )
        )


        # ==========================================
        # STATUS FILTER
        # ==========================================

        if (
            status_value is not None
            and
            camera_data.get(
                "status"
            )
            !=
            status_value
        ):

            continue


        # ==========================================
        # SEARCH FILTER
        # ==========================================

        if search_value:

            searchable_values = [

                camera_data.get(
                    "camera_id"
                ),

                camera_data.get(
                    "name"
                ),

                camera_data.get(
                    "camera_ip"
                ),

                camera_data.get(
                    "company_name"
                ),

                camera_data.get(
                    "plant_name"
                ),

                camera_data.get(
                    "department_name"
                ),

                camera_data.get(
                    "workstation_name"
                ),

                camera_data.get(
                    "brand"
                ),

                camera_data.get(
                    "camera_model"
                ),
            ]

            searchable_text = " ".join(

                str(value)
                .lower()

                for value
                in searchable_values

                if value is not None
            )

            if (
                search_value
                not in searchable_text
            ):

                continue


        # ==========================================
        # ADD CAMERA
        # ==========================================

        camera_objects.append(
            camera_data
        )


    # ==============================================
    # 4. CAMERA STATUS COUNTS
    # ==============================================

    active_count = sum(

        1

        for camera
        in camera_objects

        if (
            camera.get(
                "status"
            )
            ==
            "active"
        )
    )


    # standby_count = sum(

    #     1

    #     for camera
    #     in camera_objects

    #     if (
    #         camera.get(
    #             "status"
    #         )
    #         ==
    #         "standby"
    #     )
    # )


    inactive_count = sum(

        1

        for camera
        in camera_objects

        if (
            camera.get(
                "status"
            )
            ==
            "inactive"
        )
    )


    total_cameras = (
        len(
            camera_objects
        )
    )


    # ==============================================
    # 5. RESPONSE
    # ==============================================

    return {

        "success":
            True,

        "message":
            "Camera list retrieved successfully",


        # ==========================================
        # FRONTEND SUMMARY CARDS
        # ==========================================

        "summary": {

            "total":
                total_cameras,

            "active":
                active_count,

            # "standby":
            #     standby_count,

            "inactive":
                inactive_count,
        },


        # ==========================================
        # CAMERA CARDS
        # ==========================================

        "cameras":
            camera_objects,


        # ==========================================
        # LIVE ALERT SOCKET
        # ==========================================

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
        # 1. VALIDATE AI MODULES
        #
        # Existing logic - unchanged
        # ==========================================

        modules = validate_modules(
            request.modules
        )


        camera_status = (
            validate_camera_status(
                request.status
            )
        )

        # ==========================================
        # VALIDATE DEPLOYMENT LOCATION BY ID
        # ==========================================

        organization_service.validate_camera_location(
            company_id=request.company_id,
            plant_id=request.plant_id,
            department_id=request.department_id,
            workstation_id=request.workstation_id,
        )

        plant_id = request.plant_id
        department_id = request.department_id
        workstation_id = request.workstation_id

        # ==========================================
        # 3. PYDANTIC -> DICT
        # ==========================================

        request_data = (
            request.model_dump()
        )
        
        request_data["status"] = (
            camera_status
        )
                
        request_data["plant_id"] = plant_id
        request_data["department_id"] = department_id
        request_data["workstation_id"] = workstation_id
        
        
        print("\n========== REQUEST DATA DEBUG ==========")
        print("plant_id:", request_data.get("plant_id"))
        print("department_id:", request_data.get("department_id"))
        print("workstation_id:", request_data.get("workstation_id"))
        print("========================================\n")
        
        
        request_data.pop(
            "company",
            None
        )
        request_data.pop("company_id", None)
        request_data.pop("company_name", None)

        request_data.pop("plant_name", None)
        request_data.pop("department_name", None)
        request_data.pop("workstation_name", None)


        # ==========================================
        # 4. KEEP EXISTING MODULE ARCHITECTURE
        # ==========================================

        request_data[
            "modules"
        ] = modules


        # ==========================================
        # 5. BUILD CAMERA CONFIG
        #
        # Existing CameraService / RTSP logic
        # remains unchanged.
        # ==========================================

        camera_config = (
            CameraService
            .build_camera_config(
                request_data
            )
        )


        # ==========================================
        # 6. SAVE TO POSTGRESQL
        # + CREATE CAMERA RUNTIME
        # ==========================================

        camera = (
            camera_manager
            .add_camera(
                camera_config
            )
        )


        # ==========================================
        # 7. ALERT CALLBACK
        # ==========================================

        camera.set_alert_callback(
            camera_alert_callback
        )


        # ==========================================
        # 8. RESPONSE
        # ==========================================

        return success_response(

            "Camera registered successfully",

            camera=camera
        )


    except HTTPException:

        raise


    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )


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

    # ==============================================
    # CAMERA MUST BE STOPPED BEFORE UPDATE
    # ==============================================

    if camera.running:

        raise HTTPException(
            status_code=409,
            detail=(
                "Stop the camera before "
                "updating configuration."
            )
        )


    # ==============================================
    # REQUEST -> UPDATE DICTIONARY
    # ==============================================

    updates = (
        request.model_dump(
            exclude_unset=True
        )
    )
    
    
    if "status" in updates:

        updates["status"] = (
            validate_camera_status(
                updates["status"]
            )
        )


    # ==============================================
    # UPDATE DEPLOYMENT LOCATION BY NAME
    #
    # Frontend sends:
    #
    # company
    # plant
    # department
    # workstation
    #
    # Backend resolves them to IDs.
    # ==============================================

    location_fields = {
        "company",
        "plant",
        "department",
        "workstation",
    }

    if any(
        field in updates
        for field in location_fields
    ):

        company_name = (
            updates.get(
                "company"
            )
        )

        plant_name = (
            updates.get(
                "plant"
            )
        )

        department_name = (
            updates.get(
                "department"
            )
        )

        workstation_name = (
            updates.get(
                "workstation"
            )
        )


        # ==========================================
        # REQUIRE COMPLETE LOCATION HIERARCHY
        # ==========================================

        if not all(
            [
                company_name,
                plant_name,
                department_name,
                workstation_name,
            ]
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "Company, plant, department "
                    "and workstation must all be "
                    "provided when changing "
                    "camera location."
                )
            )


        # ==========================================
        # RESOLVE NAMES -> IDs
        # ==========================================

        location = (
            organization_service
            .resolve_camera_location_by_name(

                company_name=
                    company_name,

                plant_name=
                    plant_name,

                department_name=
                    department_name,

                workstation_name=
                    workstation_name,
            )
        )
        
        
        print("\n========== CAMERA LOCATION DEBUG ==========")
        print("Resolved location:", location)
        print("===========================================\n")


        # ==========================================
        # STORE INTERNAL IDS
        # ==========================================

        updates[
            "plant_id"
        ] = location[
            "plant_id"
        ]

        updates[
            "department_id"
        ] = location[
            "department_id"
        ]

        updates[
            "workstation_id"
        ] = location[
            "workstation_id"
        ]


        # ==========================================
        # REMOVE FRONTEND-ONLY NAME FIELDS
        #
        # Camera config/database should continue
        # storing IDs internally.
        # ==========================================

        updates.pop(
            "company",
            None
        )

        updates.pop(
            "plant",
            None
        )

        updates.pop(
            "department",
            None
        )

        updates.pop(
            "workstation",
            None
        )


    # ==============================================
    # VALIDATE AI MODULES
    # ==============================================

    if (
        "modules" in updates
        and
        updates["modules"] is not None
    ):

        updates[
            "modules"
        ] = validate_modules(
            updates[
                "modules"
            ]
        )


    # ==============================================
    # SOURCE TYPE
    # ==============================================

    source_type = (
        updates.get(
            "source_type",
            camera.config.get(
                "source_type"
            )
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


    # ==============================================
    # CCTV CONNECTION FIELDS
    # ==============================================

    cctv_fields = {

        "brand",
        "camera_ip",
        "username",
        "password",
        "rtsp_port",
        "channel",
        "stream_path",
    }


    if (
        source_type == "cctv"
        and
        any(
            field in updates
            for field in cctv_fields
        )
    ):

        camera_ip = (
            updates.get(
                "camera_ip",
                camera.config.get(
                    "camera_ip"
                )
            )
        )

        rtsp_port = (
            updates.get(
                "rtsp_port",
                camera.config.get(
                    "rtsp_port",
                    554
                )
            )
        )

        brand = (
            updates.get(
                "brand",
                camera.config.get(
                    "brand",
                    "other"
                )
            )
        )

        channel = (
            updates.get(
                "channel",
                camera.config.get(
                    "channel",
                    1
                )
            )
        )

        stream_path = (
            updates.get(
                "stream_path",
                camera.config.get(
                    "stream_path"
                )
            )
        )


        # ==========================================
        # CREDENTIALS
        # ==========================================

        username = (
            updates.get(
                "username"
            )
        )

        password = (
            updates.get(
                "password"
            )
        )


        # ==========================================
        # IF CCTV CONNECTION IS BEING CHANGED,
        # REQUIRE BOTH USERNAME AND PASSWORD
        # ==========================================

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


        # ==========================================
        # BUILD RTSP URL
        # ==========================================

        updates[
            "cctv_url"
        ] = RTSPService.build_url(

            camera_ip=
                camera_ip,

            brand=
                brand,

            username=
                username,

            password=
                password,

            rtsp_port=
                rtsp_port,

            channel=
                channel,

            stream_path=
                stream_path
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


        # ==========================================
        # DO NOT STORE PLAIN PASSWORD FIELDS
        # ==========================================

        updates.pop(
            "username",
            None
        )

        updates.pop(
            "password",
            None
        )


    # ==============================================
    # UPDATE CAMERA
    # ==============================================

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
            detail=str(
                exc
            )
        )


    except RuntimeError as exc:

        raise HTTPException(
            status_code=409,
            detail=str(
                exc
            )
        )


    except Exception as exc:

        print(
            "CAMERA UPDATE ERROR ->",
            repr(
                exc
            )
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not update camera: "
                f"{exc}"
            )
        )


    # ==============================================
    # RESPONSE
    # ==============================================

    return success_response(

        "Camera updated successfully",

        camera=
            camera
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


    # ==============================================
    # ALREADY RUNNING
    # ==============================================

    if camera.running:

        return success_response(

            "Camera is already running",

            camera=camera,

            started=False
        )


    # ==============================================
    # TRY TO START CAMERA
    # ==============================================

    started = (
        camera.start()
    )


    # ==============================================
    # START FAILED
    # ==============================================

    if not started:

        error_message = (
            camera.last_error
            or
            "Camera could not be started."
        )

        raise HTTPException(
            status_code=503,
            detail={
                "message":
                    "Camera failed to start",

                "camera_id":
                    camera_id,

                "error":
                    error_message
            }
        )


    # ==============================================
    # STARTED SUCCESSFULLY
    # ==============================================

    return success_response(

        "Camera started successfully",

        camera=camera,

        started=True
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

# GET zones
@app.get(
    "/cameras/{camera_id}/zones"
)
def get_camera_zones(
    camera_id: str
):

    zone_engine = (
        get_camera_zone_engine(
            camera_id
        )
    )

    zones = (
        zone_engine
        .get_all_zones()
    )

    return {

        "success":
            True,

        "camera_id":
            camera_id,

        "total":
            len(zones),

        "zones":
            zones
    }
    
    
# Automatic zone id , frontend will not generate automatic id
    # post zones
    
@app.post(
    "/cameras/{camera_id}/zones",
    status_code=201
)
def create_camera_zone(
    camera_id: str,
    request: ZoneCreateRequest
):

    zone_engine = (
        get_camera_zone_engine(
            camera_id
        )
    )

    # ----------------------------------------------
    # Polygon needs at least 3 points
    # ----------------------------------------------

    if len(
        request.points
    ) < 3:

        raise HTTPException(
            status_code=400,
            detail=(
                "A zone requires at least "
                "3 points."
            )
        )

    existing_zones = (
        zone_engine
        .get_all_zones()
    )

    # ----------------------------------------------
    # Simple automatic zone ID
    # ----------------------------------------------

    existing_numbers = []

    for zone in existing_zones:

        zone_id = str(
            zone.get(
                "id",
                ""
            )
        )

        if zone_id.startswith(
            "zone_"
        ):

            try:

                existing_numbers.append(
                    int(
                        zone_id.split(
                            "_"
                        )[-1]
                    )
                )

            except ValueError:

                pass

    next_number = (
        max(
            existing_numbers,
            default=0
        )
        +
        1
    )

    zone_id = (
        f"zone_"
        f"{next_number:03d}"
    )

    # ----------------------------------------------
    # Defaults
    # ----------------------------------------------

    zone = {

        "id":
            zone_id,

        "name":
            request.name.strip(),

        "points":
            request.points,

        "color":
            (
                request.color
                or
                [0, 255, 0]
            ),

        "zone_type":
        (
            request.zone_type
            or
            "normal"
        )
        .lower()
        .strip()
    }

    zone_engine.add_zone(
        zone
    )

    return {

        "success":
            True,

        "message":
            "Zone created successfully",

        "camera_id":
            camera_id,

        "zone":
            zone
    }    

# PUT zone

@app.put(
    "/cameras/{camera_id}/zones/{zone_id}"
)
def update_camera_zone(
    camera_id: str,
    zone_id: str,
    request: ZoneUpdateRequest
):

    zone_engine = (
        get_camera_zone_engine(
            camera_id
        )
    )

    updates = (
        request.model_dump(
            exclude_unset=True
        )
    )

    if (
        "points" in updates
        and
        len(
            updates["points"]
        ) < 3
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "A zone requires at least "
                "3 points."
            )
        )

    try:

        zone = (
            zone_engine
            .update_zone(
                zone_id,
                updates
            )
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc)
        )

    return {

        "success":
            True,

        "message":
            "Zone updated successfully",

        "camera_id":
            camera_id,

        "zone":
            zone
    }
   
   
   
    # delete zones 
@app.delete(
    "/cameras/{camera_id}/zones/{zone_id}"
)
def delete_camera_zone(
    camera_id: str,
    zone_id: str
):

    zone_engine = (
        get_camera_zone_engine(
            camera_id
        )
    )

    try:

        deleted_zone = (
            zone_engine
            .delete_zone(
                zone_id
            )
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc)
        )

    return {

        "success":
            True,

        "message":
            "Zone deleted successfully",

        "camera_id":
            camera_id,

        "zone":
            deleted_zone
    }
    
    
    
        
# ===================================
# ADD MODULES
# ===================================

# ==================================================
# GET AVAILABLE AI MODULES
#
# Used by:
# - AI Profile feature dropdown
# - Camera module selection
#
# IMPORTANT:
# "modules" is kept for backward compatibility.
# "groups" is provided for grouped frontend display.
# ==================================================

@app.get(
    "/modules"
)
def get_modules():

    orchestrator = (
        Orchestrator()
    )

    available_modules = (
        orchestrator.available_modules
    )


    # ==============================================
    # FRONTEND MODULE GROUPS
    # ==============================================

    module_groups = [

        {
            "key":
                "worker_safety",

            "display_name":
                "Worker Safety",

            "modules": [

                {
                    "key":
                        "helmet",

                    "display_name":
                        "Helmet Detection"
                },

                {
                    "key":
                        "phone",

                    "display_name":
                        "Phone Detection"
                },

                {
                    "key":
                        "smoking",

                    "display_name":
                        "Smoking Detection"
                },

                {
                    "key":
                        "sleep",

                    "display_name":
                        "Sleep Detection"
                },

                {
                    "key":
                        "fall",

                    "display_name":
                        "Fall Detection"
                }
            ]
        },


        {
            "key":
                "fire_hazard",

            "display_name":
                "Fire & Hazard",

            "modules": [

                {
                    "key":
                        "fire",

                    "display_name":
                        "Fire Detection"
                },

                {
                    "key":
                        "smoke",

                    "display_name":
                        "Smoke Detection"
                }
            ]
        },


        {
            "key":
                "human_behaviour",

            "display_name":
                "Human Behaviour",

            "modules": [

                {
                    "key":
                        "pose",

                    "display_name":
                        "Pose Detection"
                },

                {
                    "key":
                        "running",

                    "display_name":
                        "Running Detection"
                },

                {
                    "key":
                        "idle",

                    "display_name":
                        "Idle Detection"
                },

                {
                    "key":
                        "activity",

                    "display_name":
                        "Activity Detection"
                },

                {
                    "key":
                        "group",

                    "display_name":
                        "Group Detection"
                },

                {
                    "key":
                        "loitering",

                    "display_name":
                        "Loitering Detection"
                }
            ]
        },


        {
            "key":
                "security",

            "display_name":
                "Security & Restricted Area",

            "modules": [

                {
                    "key":
                        "restricted",

                    "display_name":
                        "Restricted Area Detection"
                },

                {
                    "key":
                        "suspicious_theft",

                    "display_name":
                        "Suspicious Theft Detection"
                }
            ]
        },


        {
            "key":
                "operations",

            "display_name":
                "Operations",

            "modules": [

                {
                    "key":
                        "after_shift",

                    "display_name":
                        "After Shift Detection"
                },

                {
                    "key":
                        "vehicle",

                    "display_name":
                        "Vehicle Detection"
                }
            ]
        }
    ]


    # ==============================================
    # SAFETY FILTER
    #
    # Only expose modules that actually exist
    # inside Orchestrator.
    # ==============================================

    groups = []

    for group in module_groups:

        valid_modules = [

            module

            for module in group["modules"]

            if module["key"]
            in available_modules
        ]

        if valid_modules:

            groups.append({

                "key":
                    group["key"],

                "display_name":
                    group["display_name"],

                "modules":
                    valid_modules
            })


    # ==============================================
    # EXISTING FLAT LIST
    #
    # Keep this so old frontend/backend integration
    # does not break.
    # ==============================================

    modules = sorted(
        available_modules
    )


    return {

        "success":
            True,

        "message":
            "Available modules retrieved successfully",

        "total":
            len(modules),

        "modules":
            modules,

        "groups":
            groups
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

# ==================================================
# VIDEO STREAM GENERATOR
#
# IMPORTANT:
# The MJPEG stream must stop immediately when
# the camera runtime is stopped.
# ==================================================

def generate_camera_stream(
    camera
):

    while True:

        # ==========================================
        # CAMERA STOPPED
        #
        # Stop the HTTP stream immediately.
        # ==========================================

        if not camera.running:

            print(
                f"CAMERA STREAM STOPPED -> "
                f"{camera.camera_id}"
            )

            break


        # ==========================================
        # GET LATEST FRAME
        # ==========================================

        frame = (
            camera
            .get_latest_frame()
        )


        # ==========================================
        # FRAME NOT AVAILABLE YET
        # ==========================================

        if frame is None:

            time.sleep(
                0.05
            )

            continue


        # ==========================================
        # ENCODE FRAME
        # ==========================================

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


        # ==========================================
        # SEND FRAME
        # ==========================================

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
# GET ALERT LOGS
# ==================================================

@app.get(
    "/alerts"
)
def get_alerts(
    camera_id: str | None = None,
    alert_type: str | None = None,
    severity: str | None = None,
    limit: int = 50
):

    if limit < 1:

        raise HTTPException(
            status_code=400,
            detail="limit must be greater than 0."
        )

    if limit > 500:

        limit = 500

    logs = (
        alert_log_store
        .get_all(

            camera_id=
                camera_id,

            alert_type=
                alert_type,

            severity=
                severity,

            limit=
                limit
        )
    )

    return {

        "success":
            True,

        "count":
            len(
                logs
            ),

        "alerts":
            logs
    }
    
    
    
# ==================================================
# ALERT SSE STREAM
#
# Frontend calls this GET endpoint ONCE.
#
# Connection remains open and new alerts are pushed
# continuously as they occur.
# ==================================================

async def alert_event_stream(
    camera_id=None
):

    while True:

        try:

            message = (
                alert_stream_queue
                .get_nowait()
            )

        except Empty:

            # ------------------------------------------
            # SSE heartbeat.
            #
            # Prevent proxies/browser/network from
            # treating an idle stream as dead.
            # ------------------------------------------

            yield ": keep-alive\n\n"

            await asyncio.sleep(
                1.0
            )

            continue


        # ==============================================
        # CAMERA FILTER
        # ==============================================

        if (
            camera_id is not None
            and
            message.get(
                "camera_id"
            ) != camera_id
        ):

            continue


        # ==============================================
        # SSE MESSAGE
        # ==============================================

        yield (
            "data: "
            +
            json.dumps(
                message
            )
            +
            "\n\n"
        )
        
        
        
@app.get(
    "/alerts/stream"
)
async def stream_alerts(
    camera_id: str | None = None
):

    return StreamingResponse(

        alert_event_stream(
            camera_id=
                camera_id
        ),

        media_type=
            "text/event-stream",

        headers={

            "Cache-Control":
                "no-cache",

            "Connection":
                "keep-alive",

            "X-Accel-Buffering":
                "no"
        }
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

    print(
        "API SHUTDOWN -> Stopping cameras..."
    )

    try:

        camera_manager.stop_all()

    except Exception as exc:

        print(
            "CAMERA SHUTDOWN ERROR ->",
            repr(exc)
        )

    print(
        "API SHUTDOWN -> Complete"
    )