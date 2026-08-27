
from services.rtsp_service import (
    RTSPService,
)


class CameraService:

    # ==================================================
    # CREATE CAMERA CONFIG
    #
    # API camera registration is currently CCTV-only.
    #
    # Video/webcam testing remains outside this API
    # for now.
    # ==================================================

    @staticmethod
    def build_camera_config(
        data
    ):

        # ==================================================
        # SOURCE TYPE
        #
        # Frontend does not need to send this.
        # ==================================================

        source_type = "cctv"


        # ==================================================
        # CAMERA ID
        #
        # Generated automatically.
        # ==================================================

        # camera_id = (
        #     "cam_"
        #     +
        #     uuid.uuid4().hex[:8]
        # )


        # ==================================================
        # NAME
        # ==================================================

        name = (
            data.get(
                "name"
            )
            or ""
        ).strip()


        if not name:

            raise ValueError(
                "Camera name is required."
            )

        # ==================================================
        # CAMERA ID
        #
        # Camera name itself is now the public camera ID.
        #
        # Example:
        # name = "Main Gate"
        # id   = "Main Gate"
        # ==================================================

        camera_id = name
        
        
        # ==================================================
        # MODULES
        #
        # Keep internally as list.
        #
        # ["helmet"]
        # ["helmet", "fire"]
        # ["all"]
        # ==================================================

        modules = data.get(
            "modules"
        )

        if not modules:

            raise ValueError(
                "At least one AI module is required."
            )
            
            
        print(
        "CAMERA SERVICE MODULES ->",
        modules
    )    


        # ==================================================
        # CCTV BRAND
        #
        # Default:
        # other / unknown
        # ==================================================

        brand = (
            data.get(
                "brand"
            )
            or
            "other"
        )


        brand = (
            brand
            .lower()
            .strip()
        )


        # ==================================================
        # CCTV CONNECTION DETAILS
        # ==================================================

        camera_ip = (
            data.get(
                "camera_ip"
            )
        )


        username = (
            data.get(
                "username"
            )
        )


        password = (
            data.get(
                "password"
            )
        )


        rtsp_port = (
            data.get(
                "rtsp_port"
            )
            or
            554
        )


        # ==================================================
        # CHANNEL
        #
        # Useful when multiple cameras are connected
        # through the same NVR/DVR.
        #
        # Default channel = 1
        # ==================================================

        channel = (
            data.get(
                "channel"
            )
            or
            1
        )


        # ==================================================
        # OPTIONAL STREAM PATH
        #
        # Kept internally for compatibility.
        #
        # Known brands do not need it.
        #
        # For "other" / legacy custom configuration,
        # RTSPService may use it when supplied.
        # ==================================================

        stream_path = (
            data.get(
                "stream_path"
            )
        )


        # ==================================================
        # GET FINAL STREAM PATH
        #
        # Example:
        #
        # Hikvision + channel 2
        #
        # Streaming/Channels/201
        #
        # CP Plus + channel 2
        #
        # cam/realmonitor?channel=2&subtype=0
        # ==================================================

        final_stream_path = (
            RTSPService
            .get_stream_path(

                brand=brand,

                channel=channel,

                stream_path=
                    stream_path
            )
        )


        # ==================================================
        # BUILD RTSP URL
        #
        # User/frontend does NOT need to create RTSP URL.
        #
        # Backend generates it.
        # ==================================================

        rtsp_url = (
            RTSPService
            .build_url(

                brand=brand,

                camera_ip=
                    camera_ip,

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
        )


        # ==================================================
        # NORMALIZED RUNTIME CONFIG
        #
        # Compatible with:
        #
        # CameraManager
        # CameraRepository
        # CameraRuntime
        # Orchestrator
        # ==================================================

        config = {

            # ----------------------------------------------
            # IDENTITY
            # ----------------------------------------------

            "id":
                camera_id,

            "name":
                name,

            "enabled":
                data.get(
                    "enabled",
                    True
                ),


            # ----------------------------------------------
            # SOURCE
            # ----------------------------------------------

            "source_type":
                source_type,


            # ----------------------------------------------
            # CCTV
            # ----------------------------------------------

            "brand":
                brand,

            "camera_ip":
                camera_ip,

            "username":
                username,

            "password":
                password,

            "rtsp_port":
                rtsp_port,

            "channel":
                channel,

            "stream_path":
                final_stream_path,

            "cctv_url":
                rtsp_url,


            # ----------------------------------------------
            # VIDEO / WEBCAM
            #
            # Kept internally so existing runtime structure
            # is not disturbed.
            # ----------------------------------------------

            "video_path":
                None,

            "webcam_index":
                None,


            # ----------------------------------------------
            # AI MODULES
            # ----------------------------------------------

            "modules":
                modules,


            # ----------------------------------------------
            # OUTPUT
            # ----------------------------------------------

            "save_output":
                data.get(
                    "save_output",
                    False
                ),


            # ----------------------------------------------
            # ZONES
            #
            # Temporary until zones move to database/API.
            # ----------------------------------------------

            # Final per-camera zones_file is assigned
            # by CameraRepository after camera ID generation.

            "zones_file":
                None,
        }


        return config