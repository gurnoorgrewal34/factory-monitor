from sqlalchemy import func

from database.database import (
    SessionLocal,
)

from database.models import (
    Camera,
)


class CameraRepository:

    # ==================================================
    # ORM MODEL -> RUNTIME CONFIG
    # ==================================================

    @staticmethod
    def to_config(
        camera
    ):

        return {

            # ------------------------------------------
            # PUBLIC CAMERA ID
            # ------------------------------------------

            "id":
                camera.id,

            "name":
                camera.name,

            "enabled":
                camera.enabled,

            # ------------------------------------------
            # SOURCE
            # ------------------------------------------

            "source_type":
                camera.source_type,

            # ------------------------------------------
            # CCTV
            # ------------------------------------------

            "brand":
                camera.brand,

            "camera_ip":
                camera.camera_ip,

            "username":
                camera.username,

            "password":
                camera.password,

            "rtsp_port":
                camera.rtsp_port,

            "channel":
                camera.channel,

            "stream_path":
                camera.stream_path,

            "cctv_url":
                camera.rtsp_url,

            # ------------------------------------------
            # VIDEO / WEBCAM
            # ------------------------------------------

            "video_path":
                camera.video_path,

            "webcam_index":
                camera.webcam_index,

            # ------------------------------------------
            # AI MODULES
            # ------------------------------------------

            "modules":
                camera.modules
                or
                ["all"],

            # ------------------------------------------
            # OUTPUT
            # ------------------------------------------

            "save_output":
                camera.save_output,

            # ------------------------------------------
            # ZONES
            # ------------------------------------------

            "zones_file":
                (
                    f"zones/data/"
                    f"{camera.id}.json"
                ),
        }

    # ==================================================
    # LIST
    # ==================================================

    def get_all(
        self
    ):

        with SessionLocal() as db:

            cameras = (

                db.query(
                    Camera
                )

                .order_by(
                    Camera.db_id.asc()
                )

                .all()
            )

            return [

                self.to_config(
                    camera
                )

                for camera
                in cameras
            ]

    # ==================================================
    # GET BY ID
    #
    # NOTE:
    # camera_id is now the user-entered camera name.
    #
    # Example:
    #
    # camera_id = "Main Gate"
    # ==================================================

    def get_by_id(
        self,
        camera_id
    ):

        with SessionLocal() as db:

            camera = (

                db.query(
                    Camera
                )

                .filter(
                    Camera.id
                    ==
                    camera_id
                )

                .first()
            )

            if camera is None:

                return None

            return self.to_config(
                camera
            )

    # ==================================================
    # CREATE
    #
    # User-entered camera name becomes the
    # PUBLIC CAMERA ID.
    #
    # Example:
    #
    # Frontend:
    # name = "Main Gate"
    #
    # Database:
    #
    # db_id = 1          <- PostgreSQL
    # id    = Main Gate  <- Public ID
    # name  = Main Gate
    #
    # No CAM001 / CAM002 generation anymore.
    # ==================================================

    def create(
        self,
        config
    ):

        with SessionLocal() as db:

            # ==========================================
            # GET CAMERA NAME
            # ==========================================

            raw_camera_name = (
                config.get(
                    "name"
                )
                or
                ""
            )

            # ==========================================
            # NORMALIZE WHITESPACE ONLY
            #
            # "  Main   Gate  "
            #
            # becomes:
            #
            # "Main Gate"
            #
            # Capitalization is preserved.
            # ==========================================

            camera_id = (
                " ".join(
                    raw_camera_name
                    .strip()
                    .split()
                )
            )

            if not camera_id:

                raise ValueError(
                    "Camera name is required."
                )

            # ==========================================
            # DUPLICATE CHECK
            #
            # Case-insensitive comparison.
            #
            # These are considered duplicates:
            #
            # Main Gate
            # main gate
            # MAIN GATE
            #
            # But original capitalization is stored.
            # ==========================================

            existing = (

                db.query(
                    Camera
                )

                .filter(
                    func.lower(
                        Camera.id
                    )
                    ==
                    camera_id.lower()
                )

                .first()
            )

            if existing:

                raise ValueError(
                    f"Camera already exists: "
                    f"{camera_id}"
                )

            # ==========================================
            # CREATE CAMERA
            #
            # IMPORTANT:
            #
            # db_id is NOT manually provided.
            #
            # PostgreSQL automatically generates it.
            # ==========================================

            camera = Camera(

                # --------------------------------------
                # PUBLIC CAMERA ID
                # --------------------------------------

                id=
                    camera_id,

                # --------------------------------------
                # CAMERA NAME
                #
                # Keep same value for compatibility
                # with existing code.
                # --------------------------------------

                name=
                    camera_id,

                # --------------------------------------
                # SOURCE
                # --------------------------------------

                source_type=
                    config.get(
                        "source_type",
                        "cctv"
                    ),

                # --------------------------------------
                # CCTV
                # --------------------------------------

                brand=
                    config.get(
                        "brand"
                    ),

                camera_ip=
                    config.get(
                        "camera_ip"
                    ),

                username=
                    config.get(
                        "username"
                    ),

                password=
                    config.get(
                        "password"
                    ),

                rtsp_port=
                    config.get(
                        "rtsp_port",
                        554
                    ),

                channel=
                    config.get(
                        "channel",
                        1
                    ),

                stream_path=
                    config.get(
                        "stream_path"
                    ),

                rtsp_url=
                    config.get(
                        "cctv_url"
                    ),

                # --------------------------------------
                # VIDEO / WEBCAM
                # --------------------------------------

                video_path=
                    config.get(
                        "video_path"
                    ),

                webcam_index=
                    config.get(
                        "webcam_index"
                    ),

                # --------------------------------------
                # AI MODULES
                # --------------------------------------

                modules=
                    config.get(
                        "modules",
                        ["all"]
                    ),

                # --------------------------------------
                # SETTINGS
                # --------------------------------------

                enabled=
                    config.get(
                        "enabled",
                        True
                    ),

                save_output=
                    config.get(
                        "save_output",
                        False
                    ),
            )

            db.add(
                camera
            )

            db.commit()

            db.refresh(
                camera
            )

            return self.to_config(
                camera
            )

    # ==================================================
    # UPDATE
    # ==================================================

    def update(
        self,
        camera_id,
        updates
    ):

        with SessionLocal() as db:

            camera = (

                db.query(
                    Camera
                )

                .filter(
                    Camera.id
                    ==
                    camera_id
                )

                .first()
            )

            if camera is None:

                raise ValueError(
                    f"Unknown camera: "
                    f"{camera_id}"
                )

            # ==========================================
            # FIELD MAPPING
            # ==========================================

            field_map = {

                "name":
                    "name",

                "enabled":
                    "enabled",

                "source_type":
                    "source_type",

                "brand":
                    "brand",

                "camera_ip":
                    "camera_ip",

                "username":
                    "username",

                "password":
                    "password",

                "rtsp_port":
                    "rtsp_port",

                "channel":
                    "channel",

                "stream_path":
                    "stream_path",

                "cctv_url":
                    "rtsp_url",

                "video_path":
                    "video_path",

                "webcam_index":
                    "webcam_index",

                "modules":
                    "modules",

                "save_output":
                    "save_output",
            }

            for (
                config_key,
                model_key
            ) in field_map.items():

                if (
                    config_key
                    not in updates
                ):

                    continue

                value = (
                    updates[
                        config_key
                    ]
                )

                setattr(
                    camera,
                    model_key,
                    value
                )

            db.commit()

            db.refresh(
                camera
            )

            return self.to_config(
                camera
            )

    # ==================================================
    # DELETE
    # ==================================================

    def delete(
        self,
        camera_id
    ):

        with SessionLocal() as db:

            camera = (

                db.query(
                    Camera
                )

                .filter(
                    Camera.id
                    ==
                    camera_id
                )

                .first()
            )

            if camera is None:

                raise ValueError(
                    f"Unknown camera: "
                    f"{camera_id}"
                )

            db.delete(
                camera
            )

            db.commit()

            return True