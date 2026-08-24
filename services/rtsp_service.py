from urllib.parse import (
    quote,
    urlsplit,
    urlunsplit,
)


# ==================================================
# RTSP SERVICE
# ==================================================

class RTSPService:

    # ==================================================
    # BRAND STREAM PATH TEMPLATES
    #
    # IMPORTANT:
    # These are common/default RTSP formats.
    # Exact paths can still differ by model/firmware.
    #
    # "other" uses a common Dahua-style fallback.
    #
    # "custom" is kept for backward compatibility.
    # ==================================================

    BRAND_STREAM_PATHS = {

        "hikvision":
            "Streaming/Channels/{channel}01",

        "dahua":
            "cam/realmonitor?channel={channel}&subtype=0",

        "cpplus":
            "cam/realmonitor?channel={channel}&subtype=0",

        "axis":
            "axis-media/media.amp",

        "uniview":
            "unicast/c{channel}/s0/live",

        # No truly universal RTSP path exists.
        # This is only a reasonable fallback.
        "other":
            "cam/realmonitor?channel={channel}&subtype=0",
    }


    # ==================================================
    # SUPPORTED BRANDS
    # ==================================================

    SUPPORTED_BRANDS = {

        *BRAND_STREAM_PATHS.keys(),

        # Kept so older configurations using
        # "custom" do not suddenly break.
        "custom",
    }


    # ==================================================
    # GET STREAM PATH
    # ==================================================

    @classmethod
    def get_stream_path(
        cls,
        brand,
        channel=1,
        stream_path=None
    ):

        brand = (
            brand
            or "other"
        )

        brand = (
            brand
            .lower()
            .strip()
        )


        # ----------------------------------------------
        # Validate brand
        # ----------------------------------------------

        if brand not in cls.SUPPORTED_BRANDS:

            raise ValueError(
                "Unsupported camera brand. "
                f"Supported: "
                f"{sorted(cls.SUPPORTED_BRANDS)}"
            )


        # ----------------------------------------------
        # Validate channel
        # ----------------------------------------------

        try:

            channel = int(
                channel
            )

        except (
            TypeError,
            ValueError
        ):

            raise ValueError(
                "channel must be an integer."
            )


        if channel < 1:

            raise ValueError(
                "channel must be greater "
                "than or equal to 1."
            )


        # ----------------------------------------------
        # CUSTOM CAMERA
        #
        # If an explicit path exists, use it.
        #
        # Otherwise use common fallback so frontend
        # does not have to know RTSP internals.
        # ----------------------------------------------

        if brand == "custom":

            if stream_path:

                return (
                    stream_path
                    .strip()
                    .lstrip("/")
                )

            template = (
                cls.BRAND_STREAM_PATHS[
                    "other"
                ]
            )

            return template.format(
                channel=channel
            )


        # ----------------------------------------------
        # OTHER / UNKNOWN CAMERA
        #
        # Allow explicit override if one exists.
        # Otherwise use common fallback.
        # ----------------------------------------------

        if brand == "other":

            if stream_path:

                return (
                    stream_path
                    .strip()
                    .lstrip("/")
                )


        # ----------------------------------------------
        # KNOWN BRAND
        # ----------------------------------------------

        template = (
            cls.BRAND_STREAM_PATHS[
                brand
            ]
        )


        return template.format(
            channel=channel
        )


    # ==================================================
    # BUILD RTSP URL
    # ==================================================

    @classmethod
    def build_url(
        cls,
        brand,
        camera_ip,
        username,
        password,
        rtsp_port=554,
        channel=1,
        stream_path=None
    ):

        # ----------------------------------------------
        # Normalize brand
        # ----------------------------------------------

        brand = (
            brand
            or "other"
        )

        brand = (
            brand
            .lower()
            .strip()
        )


        # ----------------------------------------------
        # Validate IP
        # ----------------------------------------------

        if not camera_ip:

            raise ValueError(
                "camera_ip is required."
            )


        camera_ip = (
            camera_ip
            .strip()
        )


        # ----------------------------------------------
        # Validate username
        # ----------------------------------------------

        if not username:

            raise ValueError(
                "username is required."
            )


        # ----------------------------------------------
        # Validate password
        # ----------------------------------------------

        if password is None:

            raise ValueError(
                "password is required."
            )


        # ----------------------------------------------
        # RTSP port
        # ----------------------------------------------

        try:

            rtsp_port = int(
                rtsp_port
            )

        except (
            TypeError,
            ValueError
        ):

            raise ValueError(
                "rtsp_port must be an integer."
            )


        if (
            rtsp_port < 1
            or
            rtsp_port > 65535
        ):

            raise ValueError(
                "Invalid RTSP port."
            )


        # ----------------------------------------------
        # Determine final stream path automatically
        # ----------------------------------------------

        final_stream_path = (
            cls.get_stream_path(

                brand=brand,

                channel=channel,

                stream_path=
                    stream_path
            )
        )


        final_stream_path = (
            final_stream_path
            .strip()
            .lstrip("/")
        )


        # ----------------------------------------------
        # Encode credentials safely
        #
        # Handles:
        # @
        # #
        # :
        # /
        # etc.
        # ----------------------------------------------

        safe_username = quote(
            str(username),
            safe=""
        )

        safe_password = quote(
            str(password),
            safe=""
        )


        # ----------------------------------------------
        # Final URL
        # ----------------------------------------------

        return (
            f"rtsp://"
            f"{safe_username}:"
            f"{safe_password}@"
            f"{camera_ip}:"
            f"{rtsp_port}/"
            f"{final_stream_path}"
        )


    # ==================================================
    # MASK URL FOR API RESPONSE
    #
    # Example:
    #
    # Actual:
    # rtsp://admin:secret@192.168.1.10:554/...
    #
    # API:
    # rtsp://admin:****@192.168.1.10:554/...
    # ==================================================

    @staticmethod
    def mask_url(
        rtsp_url
    ):

        if not rtsp_url:

            return None


        try:

            parsed = urlsplit(
                rtsp_url
            )


            hostname = (
                parsed.hostname
                or ""
            )


            port = (

                f":{parsed.port}"

                if parsed.port

                else ""
            )


            username = (
                parsed.username
                or ""
            )


            if username:

                safe_netloc = (
                    f"{username}:****@"
                    f"{hostname}"
                    f"{port}"
                )

            else:

                safe_netloc = (
                    f"{hostname}"
                    f"{port}"
                )


            return urlunsplit((

                parsed.scheme,

                safe_netloc,

                parsed.path,

                parsed.query,

                parsed.fragment
            ))


        except Exception:

            return "configured"