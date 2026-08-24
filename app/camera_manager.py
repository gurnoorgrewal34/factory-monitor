import json
import os
import threading

from app.camera_runtime import (
    CameraRuntime,
)


class CameraManager:

    def __init__(
        self,
        config_path,
        base_dir,
        repository=None
    ):

        self.config_path = (
            config_path
        )

        self.base_dir = (
            base_dir
        )

        self.repository = (
            repository
        )

        self.cameras = {}

        self._lock = (
            threading.Lock()
        )

        self._load_config()

    # ==================================================
    # LOAD
    # ==================================================

    def _load_config(self):

        camera_configs = []

        # ==============================================
        # DATABASE MODE
        # ==============================================

        if self.repository is not None:

            camera_configs = (
                self.repository
                .get_all()
            )

            # ------------------------------------------
            # First-run migration
            #
            # If PostgreSQL is empty but the old
            # cameras.json exists, import those cameras.
            # ------------------------------------------

            # if (
            #     not camera_configs
            #     and
            #     os.path.exists(
            #         self.config_path
            #     )
            # ):

            #     print(
            #         "CAMERA MANAGER -> "
            #         "Database empty. "
            #         "Importing cameras.json..."
            #     )

            #     with open(
            #         self.config_path,
            #         "r",
            #         encoding="utf-8"
            #     ) as file:

            #         old_config = (
            #             json.load(
            #                 file
            #             )
            #         )

            #     old_cameras = (
            #         old_config.get(
            #             "cameras",
            #             []
            #         )
            #     )

            #     for config in old_cameras:

            #         try:

            #             self.repository.create(
            #                 config
            #             )

            #         except Exception as exc:

            #             print(
            #                 "CAMERA IMPORT WARNING -> "
            #                 f"{config.get('id')} -> "
            #                 f"{exc}"
            #             )

            #     camera_configs = (
            #         self.repository
            #         .get_all()
            #     )

        # ==============================================
        # OLD JSON MODE / FALLBACK
        # ==============================================

        else:

            if not os.path.exists(
                self.config_path
            ):

                raise FileNotFoundError(
                    f"Camera config not found: "
                    f"{self.config_path}"
                )

            with open(
                self.config_path,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(
                    file
                )

            camera_configs = (
                data.get(
                    "cameras",
                    []
                )
            )

        # ==============================================
        # CREATE CAMERA RUNTIME OBJECTS
        # ==============================================

        for camera_config in camera_configs:

            camera_id = (
                camera_config[
                    "id"
                ]
            )

            if (
                camera_id
                in self.cameras
            ):

                raise ValueError(
                    f"Duplicate camera ID: "
                    f"{camera_id}"
                )

            self.cameras[
                camera_id
            ] = CameraRuntime(

                camera_config,

                self.base_dir
            )

        print()

        print(
            "========================================"
        )

        print(
            "CAMERA MANAGER READY"
        )

        print(
            f"Configured cameras: "
            f"{len(self.cameras)}"
        )

        print(
            "Persistence: "
            +
            (
                "PostgreSQL"
                if self.repository
                else "JSON"
            )
        )

        print(
            "========================================"
        )

    # ==================================================
    # JSON FALLBACK SAVE
    # ==================================================

    def _save_json_config(self):

        camera_configs = [

            camera.config.copy()

            for camera
            in self.cameras.values()
        ]

        data = {

            "cameras":
                camera_configs
        }

        temp_path = (
            self.config_path
            +
            ".tmp"
        )

        with open(
            temp_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=2
            )

        os.replace(
            temp_path,
            self.config_path
        )

    # ==================================================
    # GET CAMERA
    # ==================================================

    def get_camera(
        self,
        camera_id
    ):

        return self.cameras.get(
            camera_id
        )

    # ==================================================
    # ADD CAMERA
    #
    # In PostgreSQL mode:
    #
    # Repository creates the ID:
    #
    # CAM001
    # CAM002
    # CAM003
    #
    # In JSON fallback mode:
    #
    # camera_config must already contain an ID.
    # ==================================================

    def add_camera(
        self,
        camera_config
    ):

        with self._lock:

            # ==========================================
            # DATABASE MODE
            # ==========================================

            if self.repository:

                stored_config = (
                    self.repository
                    .create(
                        camera_config
                    )
                )

                camera_id = (
                    stored_config.get(
                        "id"
                    )
                )

                if not camera_id:

                    raise RuntimeError(
                        "Camera repository did not "
                        "return a generated camera ID."
                    )

            # ==========================================
            # JSON FALLBACK MODE
            # ==========================================

            else:

                camera_id = (
                    camera_config.get(
                        "id"
                    )
                )

                if not camera_id:

                    raise ValueError(
                        "Camera ID is required "
                        "when database repository "
                        "is not being used."
                    )

                if (
                    camera_id
                    in self.cameras
                ):

                    raise ValueError(
                        f"Camera already exists: "
                        f"{camera_id}"
                    )

                stored_config = (
                    camera_config.copy()
                )

            # ==========================================
            # DUPLICATE RUNTIME SAFETY CHECK
            # ==========================================

            if (
                camera_id
                in self.cameras
            ):

                if self.repository:

                    try:

                        self.repository.delete(
                            camera_id
                        )

                    except Exception:

                        pass

                raise ValueError(
                    f"Camera already exists: "
                    f"{camera_id}"
                )

            # ==========================================
            # CREATE CAMERA RUNTIME
            # ==========================================

            try:

                camera = CameraRuntime(

                    stored_config,

                    self.base_dir
                )

                self.cameras[
                    camera_id
                ] = camera

                # --------------------------------------
                # JSON persistence only
                # --------------------------------------

                if not self.repository:

                    self._save_json_config()

            except Exception:

                # --------------------------------------
                # Remove partially-created runtime
                # --------------------------------------

                self.cameras.pop(
                    camera_id,
                    None
                )

                # --------------------------------------
                # Repository.create() already committed
                # the row, so delete it if runtime
                # creation fails.
                # --------------------------------------

                if self.repository:

                    try:

                        self.repository.delete(
                            camera_id
                        )

                    except Exception as rollback_exc:

                        print(
                            "CAMERA MANAGER ROLLBACK "
                            "WARNING ->",
                            repr(
                                rollback_exc
                            )
                        )

                raise

            return camera

    # ==================================================
    # UPDATE CAMERA
    # ==================================================

    def update_camera(
        self,
        camera_id,
        updates
    ):

        with self._lock:

            camera = (
                self.get_camera(
                    camera_id
                )
            )

            if camera is None:

                raise ValueError(
                    f"Unknown camera: "
                    f"{camera_id}"
                )

            if camera.running:

                raise RuntimeError(
                    "Stop the camera before "
                    "updating its configuration."
                )

            # ------------------------------------------
            # Camera ID cannot be modified
            # ------------------------------------------

            if (
                "id" in updates
                and
                updates[
                    "id"
                ] != camera_id
            ):

                raise ValueError(
                    "Camera ID cannot "
                    "be changed."
                )

            # ==========================================
            # DATABASE MODE
            # ==========================================

            if self.repository:

                stored_config = (
                    self.repository
                    .update(
                        camera_id,
                        updates
                    )
                )

                camera.config.clear()

                camera.config.update(
                    stored_config
                )

            # ==========================================
            # JSON FALLBACK MODE
            # ==========================================

            else:

                original = (
                    camera.config.copy()
                )

                for key, value in (
                    updates.items()
                ):

                    camera.config[
                        key
                    ] = value

                try:

                    self._save_json_config()

                except Exception:

                    camera.config.clear()

                    camera.config.update(
                        original
                    )

                    raise

            # ------------------------------------------
            # Synchronize mirrored runtime attributes
            # ------------------------------------------

            camera.camera_name = (
                camera.config.get(
                    "name",
                    camera_id
                )
            )

            camera.enabled = (
                camera.config.get(
                    "enabled",
                    True
                )
            )

            return camera

    # ==================================================
    # DELETE CAMERA
    # ==================================================

    def delete_camera(
        self,
        camera_id
    ):

        with self._lock:

            camera = (
                self.get_camera(
                    camera_id
                )
            )

            if camera is None:

                raise ValueError(
                    f"Unknown camera: "
                    f"{camera_id}"
                )

            # ------------------------------------------
            # Stop first if currently running
            # ------------------------------------------

            if camera.running:

                camera.stop()

            # ------------------------------------------
            # Database delete
            # ------------------------------------------

            if self.repository:

                self.repository.delete(
                    camera_id
                )

            removed = (
                self.cameras.pop(
                    camera_id
                )
            )

            # ------------------------------------------
            # JSON fallback persistence
            # ------------------------------------------

            try:

                if not self.repository:

                    self._save_json_config()

            except Exception:

                self.cameras[
                    camera_id
                ] = removed

                raise

            return True

    # ==================================================
    # START CAMERA
    # ==================================================

    def start_camera(
        self,
        camera_id
    ):

        camera = (
            self.get_camera(
                camera_id
            )
        )

        if camera is None:

            raise ValueError(
                f"Unknown camera: "
                f"{camera_id}"
            )

        return camera.start()

    # ==================================================
    # STOP CAMERA
    # ==================================================

    def stop_camera(
        self,
        camera_id
    ):

        camera = (
            self.get_camera(
                camera_id
            )
        )

        if camera is None:

            raise ValueError(
                f"Unknown camera: "
                f"{camera_id}"
            )

        return camera.stop()

    # ==================================================
    # START ENABLED CAMERAS
    # ==================================================

    def start_enabled(self):

        for camera in (
            self.cameras.values()
        ):

            if camera.enabled:

                camera.start()

    # ==================================================
    # STOP ALL
    # ==================================================

    def stop_all(self):

        for camera in (
            self.cameras.values()
        ):

            if camera.running:

                camera.stop()

    # ==================================================
    # STATUS
    # ==================================================

    def get_status(self):

        return [

            camera.get_status()

            for camera
            in self.cameras.values()
        ]