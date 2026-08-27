import os
import threading
import time

from datetime import datetime

import cv2

from inputs.camera_source import CameraSource

from app.orchestrator import Orchestrator
from app.behaviour_engine import BehaviourEngine

from tracking.tracker import PersonTracker
from tracking.person_memory import PersonMemory

from processors.group_processor import GroupProcessor
from processors.frame_processor import FrameProcessor
from processors.person_processor import PersonProcessor
from processors.drawing_processor import DrawingProcessor

from zones.zone_engine import ZoneEngine
from zones.zone_drawer import ZoneDrawer

from alerts.alert_overlay import AlertOverlay


class CameraRuntime:

    def __init__(
        self,
        camera_config,
        base_dir
    ):

        self.config = camera_config

        self.base_dir = base_dir

        self.camera_id = (
            camera_config["id"]
        )

        self.camera_name = (
            camera_config.get(
                "name",
                self.camera_id
            )
        )

        self.enabled = (
            camera_config.get(
                "enabled",
                False
            )
        )

        ##################################################
        # RUNTIME
        ##################################################

        self.running = False

        self.thread = None

        self.camera = None

        self.frame_processor = None

        self.alert_overlay = None

        ##################################################
        # OUTPUT FRAME
        ##################################################

        self.latest_frame = None

        self.latest_frame_lock = (
            threading.Lock()
        )

        ##################################################
        # STATUS
        ##################################################

        self.frames_processed = 0

        self.last_error = None

        self.started_at = None

        ##################################################
        # ALERT CALLBACK
        ##################################################

        self.alert_callback = None

        ##################################################
        # VIDEO OUTPUT
        ##################################################

        self.writer = None

        self.output_path = None

        self.fps = 30.0

    ######################################################
    # ALERT CALLBACK
    ######################################################

    def set_alert_callback(
        self,
        callback
    ):

        self.alert_callback = callback

    ######################################################
    # BUILD PIPELINE
    ######################################################

    def _build_pipeline(self):

        print()

        print(
            "========================================"
        )

        print(
            f"INITIALIZING CAMERA: "
            f"{self.camera_id}"
        )

        print(
            f"Name: "
            f"{self.camera_name}"
        )

        print(
            "========================================"
        )

        ##################################################
        # ORCHESTRATOR
        ##################################################

        orchestrator = (
            Orchestrator()
        )

        modules = self.config.get(
            "modules",
            ["all"]
        )

        print(
            "3. CAMERA RUNTIME MODULES ->",
            modules
        )

        orchestrator.set_modules(
            modules
        )
        
        

        ##################################################
        # SOURCE
        ##################################################

        source_type = self.config.get(
            "source_type",
            "video"
        )

        video_path = self.config.get(
            "video_path"
        )

        if (
            video_path
            and
            not os.path.isabs(
                video_path
            )
        ):

            video_path = os.path.join(
                self.base_dir,
                video_path
            )

        self.camera = CameraSource(

            source_type=
                source_type,

            video_path=
                video_path,

            webcam_index=
                self.config.get(
                    "webcam_index",
                    0
                ),

            cctv_url=
                self.config.get(
                    "cctv_url"
                )
        )

        ##################################################
        # FPS
        ##################################################

        self.fps = (
            self.camera.get_fps()
        )

        if self.fps <= 0:

            self.fps = 30.0

        ##################################################
        # ZONES
        ##################################################

        zones_file = self.config.get(

            "zones_file",

            "zones/zones.json"
        )

        if not os.path.isabs(
            zones_file
        ):

            zones_file = os.path.join(
                self.base_dir,
                zones_file
            )

        zone_engine = ZoneEngine(
            zones_file
        )

        zone_drawer = ZoneDrawer(
            zone_engine
        )

        ##################################################
        # CAMERA-SPECIFIC AI STATE
        ##################################################

        tracker = (
            PersonTracker()
        )

        memory = (
            PersonMemory()
        )

        behaviour = BehaviourEngine(
            zone_engine,
            orchestrator
        )

        ##################################################
        # IMPORTANT:
        #
        # Store AlertOverlay on self instead of as a local
        # variable. CameraRuntime needs access to its newly
        # created alerts after every processed frame.
        ##################################################

        self.alert_overlay = (
            AlertOverlay()
        )

        person_processor = (
            PersonProcessor(
                memory,
                zone_engine,
                behaviour
            )
        )

        drawing_processor = (
            DrawingProcessor()
        )

        group_processor = (
            GroupProcessor(
                memory,
                behaviour
            )
        )

        ##################################################
        # FRAME PROCESSOR
        ##################################################

        self.frame_processor = (
            FrameProcessor(

                tracker,

                zone_drawer,

                person_processor,

                drawing_processor,

                group_processor,

                self.alert_overlay,

                behaviour,

                orchestrator,

                fps=self.fps,
                
                source_type=source_type
            )
        )

        ##################################################
        # OUTPUT VIDEO PATH
        ##################################################

        self._prepare_output_path()

        print(
            f"CAMERA READY -> "
            f"{self.camera_id}"
        )

    ######################################################
    # PREPARE OUTPUT VIDEO
    ######################################################

    def _prepare_output_path(self):

        save_output = self.config.get(
            "save_output",
            False
        )

        if not save_output:

            self.output_path = None

            return

        output_dir = os.path.join(

            self.base_dir,

            "outputs",

            self.camera_id
        )

        os.makedirs(
            output_dir,
            exist_ok=True
        )

        timestamp = (
            datetime.now()
            .strftime(
                "%Y%m%d_%H%M%S"
            )
        )

        self.output_path = os.path.join(

            output_dir,

            (
                f"{self.camera_id}_"
                f"{timestamp}.mp4"
            )
        )

    ######################################################
    # CREATE VIDEO WRITER
    ######################################################

    def _ensure_writer(
        self,
        frame
    ):

        if self.output_path is None:

            return

        if self.writer is not None:

            return

        height, width = (
            frame.shape[:2]
        )

        fourcc = (
            cv2.VideoWriter_fourcc(
                *"mp4v"
            )
        )

        self.writer = (
            cv2.VideoWriter(

                self.output_path,

                fourcc,

                self.fps,

                (
                    width,
                    height
                )
            )
        )

        if not self.writer.isOpened():

            print(
                f"{self.camera_id} -> "
                "Could not create output writer."
            )

            self.writer.release()

            self.writer = None

            self.output_path = None

            return

        print(
            f"{self.camera_id} -> "
            f"Saving output: "
            f"{self.output_path}"
        )

    ######################################################
    # START
    ######################################################

    def start(self):

        if self.running:

            print(
                f"{self.camera_id} "
                f"already running."
            )

            return False

        try:

            ##################################################
            # Always build a fresh pipeline for a new session.
            #
            # This is especially important when modules were
            # changed using:
            #
            # PUT /cameras/{camera_id}/modules
            ##################################################

            if (
                self.camera is None
                or
                self.frame_processor is None
            ):

                self._build_pipeline()

            self.running = True

            self.last_error = None

            self.frames_processed = 0

            self.started_at = (
                time.time()
            )

            with self.latest_frame_lock:

                self.latest_frame = None

            self.thread = (
                threading.Thread(

                    target=self._run,

                    name=(
                        f"camera-"
                        f"{self.camera_id}"
                    ),

                    daemon=True
                )
            )

            self.thread.start()

            print(
                f"CAMERA STARTED -> "
                f"{self.camera_id}"
            )

            return True

        except Exception as exc:

            self.running = False

            self.last_error = (
                repr(exc)
            )

            print(
                "CAMERA START ERROR -> "
                f"{self.camera_id} -> "
                f"{exc}"
            )

            self._release_pipeline()

            return False

    ######################################################
    # PROCESSING LOOP
    ######################################################

    def _run(self):

        try:

            while self.running:

                ##################################################
                # READ FRAME
                ##################################################

                ret, frame = (
                    self.camera.read()
                )

                if not ret:

                    ##################################################
                    # CCTV RECONNECT
                    ##################################################

                    if (
                        self.config.get(
                            "source_type"
                        )
                        == "cctv"
                    ):

                        print(
                            f"{self.camera_id} -> "
                            "Frame read failed."
                        )

                        if (
                            self.camera.reconnect()
                        ):

                            print(
                                f"{self.camera_id} -> "
                                "Reconnected."
                            )

                            continue

                        time.sleep(
                            2
                        )

                        continue

                    ##################################################
                    # VIDEO / WEBCAM ENDED
                    ##################################################

                    print(
                        f"{self.camera_id} -> "
                        "Stream ended."
                    )

                    break

                ##################################################
                # AI PIPELINE
                ##################################################

                annotated = (
                    self.frame_processor
                    .process(
                        frame
                    )
                )

                ##################################################
                # SAVE LATEST PROCESSED FRAME
                ##################################################

                with self.latest_frame_lock:

                    self.latest_frame = (
                        annotated.copy()
                    )

                ##################################################
                # SAVE OUTPUT VIDEO
                ##################################################

                self._ensure_writer(
                    annotated
                )

                if self.writer is not None:

                    self.writer.write(
                        annotated
                    )

                ##################################################
                # FRAME COUNT
                ##################################################

                self.frames_processed += 1

                ##################################################
                # GET NEW ALERT EVENTS
                ##################################################

                if self.alert_overlay is not None:

                    new_alerts = (
                        self.alert_overlay
                        .pop_recent_alerts()
                    )

                    if (
                        new_alerts
                        and
                        self.alert_callback
                        is not None
                    ):

                        for alert in new_alerts:

                            try:

                                self.alert_callback(

                                    self.camera_id,

                                    alert
                                )

                            except Exception as exc:

                                print(
                                    f"{self.camera_id} -> "
                                    "Alert callback error: "
                                    f"{exc}"
                                )

        except Exception as exc:

            self.last_error = (
                repr(exc)
            )

            print(
                "CAMERA RUNTIME ERROR -> "
                f"{self.camera_id} -> "
                f"{exc}"
            )

        finally:

            self.running = False

            ##################################################
            # Important for prerecorded videos.
            #
            # Once EOF is reached, clean the pipeline so a
            # later POST /start can replay/rebuild it.
            ##################################################

            self._release_pipeline()

    ######################################################
    # LATEST FRAME
    ######################################################

    def get_latest_frame(self):

        with self.latest_frame_lock:

            if self.latest_frame is None:

                return None

            return (
                self.latest_frame.copy()
            )

    ######################################################
    # STATUS
    ######################################################

    def get_status(self):

        return {

            "camera_id":
                self.camera_id,

            "name":
                self.camera_name,

            "enabled":
                self.enabled,

            "running":
                self.running,

            "frames_processed":
                self.frames_processed,

            "modules":
                self.config.get(
                    "modules",
                    []
                ),

            "source_type":
                self.config.get(
                    "source_type"
                ),

            "save_output":
                self.config.get(
                    "save_output",
                    False
                ),

            "output_path":
                self.output_path,

            "last_error":
                self.last_error
        }

    ######################################################
    # RELEASE PIPELINE
    ######################################################

    def _release_pipeline(self):

        ##################################################
        # OUTPUT WRITER
        ##################################################

        if self.writer is not None:

            try:

                self.writer.release()

            except Exception:

                pass

            self.writer = None

        ##################################################
        # CAMERA
        ##################################################

        if self.camera is not None:

            try:

                self.camera.release()

            except Exception:

                pass

            self.camera = None

        ##################################################
        # FRAME PROCESSOR
        ##################################################

        if self.frame_processor is not None:

            try:

                self.frame_processor.finalize()

            except Exception as exc:

                print(
                    f"{self.camera_id} -> "
                    f"Finalize error: "
                    f"{exc}"
                )

            self.frame_processor = None

        self.alert_overlay = None

    ######################################################
    # STOP
    ######################################################

    def stop(self):

        self.running = False

        ##################################################
        # Wait for runtime thread
        ##################################################

        if (
            self.thread is not None
            and
            self.thread
            is not threading.current_thread()
        ):

            self.thread.join(
                timeout=5
            )

        self.thread = None

        ##################################################
        # Normally _run() finally already cleans up.
        #
        # This also safely handles a runtime that never
        # entered _run() completely.
        ##################################################

        self._release_pipeline()

        print(
            f"CAMERA STOPPED -> "
            f"{self.camera_id}"
        )

        return True