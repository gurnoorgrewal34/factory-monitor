import cv2
import time


class CameraSource:

    def __init__(
        self,
        source_type,
        video_path=None,
        webcam_index=0,
        cctv_url=None
    ):

        self.source_type = source_type

        self.video_path = video_path

        self.webcam_index = webcam_index

        self.cctv_url = cctv_url

        self.cap = None

        self._open()


    # ==================================================
    # OPEN SOURCE
    # ==================================================

    def _open(self):

        print("========================================")
        print("INPUT SOURCE")
        print(f"Type: {self.source_type}")
        print("========================================")


        # ------------------------------------------------
        # VIDEO FILE
        # ------------------------------------------------

        if self.source_type == "video":

            if not self.video_path:

                raise ValueError(
                    "VIDEO_PATH is not configured."
                )

            print(
                f"Opening video: {self.video_path}"
            )

            self.cap = cv2.VideoCapture(
                self.video_path
            )


        # ------------------------------------------------
        # WEBCAM
        # ------------------------------------------------

        elif self.source_type == "webcam":

            print(
                f"Opening webcam: {self.webcam_index}"
            )

            self.cap = cv2.VideoCapture(
                self.webcam_index
            )


        # ------------------------------------------------
        # CCTV / RTSP
        # ------------------------------------------------

        elif self.source_type == "cctv":

            if not self.cctv_url:

                raise ValueError(
                    "CCTV_URL is not configured."
                )

            print(
                "Opening CCTV / RTSP stream..."
            )

            self.cap = cv2.VideoCapture(
                self.cctv_url
            )


        # ------------------------------------------------
        # INVALID SOURCE
        # ------------------------------------------------

        else:

            raise ValueError(
                f"Unknown INPUT_SOURCE: "
                f"{self.source_type}"
            )


        # ------------------------------------------------
        # CHECK
        # ------------------------------------------------

        if not self.cap.isOpened():

            raise RuntimeError(
                f"Unable to open "
                f"{self.source_type} source."
            )


        print(
            "Input source opened successfully."
        )

        print("========================================")


    # ==================================================
    # READ FRAME
    # ==================================================

    def read(self):

        if self.cap is None:

            return False, None

        return self.cap.read()


    # ==================================================
    # GET FPS
    # ==================================================

    def get_fps(self):

        if self.cap is None:

            return 30.0

        fps = self.cap.get(
            cv2.CAP_PROP_FPS
        )

        if fps <= 0:

            fps = 30.0

        return fps


    # ==================================================
    # GET WIDTH
    # ==================================================

    def get_width(self):

        if self.cap is None:

            return 0

        return int(
            self.cap.get(
                cv2.CAP_PROP_FRAME_WIDTH
            )
        )


    # ==================================================
    # GET HEIGHT
    # ==================================================

    def get_height(self):

        if self.cap is None:

            return 0

        return int(
            self.cap.get(
                cv2.CAP_PROP_FRAME_HEIGHT
            )
        )


    # ==================================================
    # RELEASE
    # ==================================================

    def release(self):

        if self.cap is not None:

            self.cap.release()

            self.cap = None


    # ==================================================
    # RECONNECT CCTV
    # ==================================================

    def reconnect(self):

        if self.source_type != "cctv":

            return False


        print(
            "CCTV -> Attempting reconnect..."
        )


        self.release()

        time.sleep(2)


        try:

            self._open()

            return True

        except Exception as e:

            print(
                f"CCTV -> Reconnect failed: {e}"
            )

            return False