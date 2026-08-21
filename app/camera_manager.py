import json
import os

from app.camera_runtime import CameraRuntime


class CameraManager:

    def __init__(
        self,
        config_path,
        base_dir
    ):

        self.config_path = config_path
        self.base_dir = base_dir

        self.cameras = {}

        self._load_config()

    # ==================================================
    # LOAD CONFIGURATION
    # ==================================================

    def _load_config(self):

        with open(
            self.config_path,
            "r",
            encoding="utf-8"
        ) as file:

            config = json.load(file)

        camera_configs = config.get(
            "cameras",
            []
        )

        for camera_config in camera_configs:

            camera_id = camera_config["id"]

            if camera_id in self.cameras:

                raise ValueError(
                    f"Duplicate camera ID: "
                    f"{camera_id}"
                )

            self.cameras[camera_id] = (
                CameraRuntime(
                    camera_config,
                    self.base_dir
                )
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
            "========================================"
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
    # START CAMERA
    # ==================================================

    def start_camera(
        self,
        camera_id
    ):

        camera = self.get_camera(
            camera_id
        )

        if camera is None:

            raise ValueError(
                f"Unknown camera: {camera_id}"
            )

        return camera.start()

    # ==================================================
    # STOP CAMERA
    # ==================================================

    def stop_camera(
        self,
        camera_id
    ):

        camera = self.get_camera(
            camera_id
        )

        if camera is None:

            raise ValueError(
                f"Unknown camera: {camera_id}"
            )

        return camera.stop()

    # ==================================================
    # START ENABLED CAMERAS
    # ==================================================

    def start_enabled(self):

        for camera in self.cameras.values():

            if camera.enabled:

                camera.start()

    # ==================================================
    # STOP ALL
    # ==================================================

    def stop_all(self):

        for camera in self.cameras.values():

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