import os
import cv2
import time

from app.camera_manager import CameraManager


BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

CONFIG_PATH = os.path.join(
    BASE_DIR,
    "config",
    "cameras.json"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "outputs"
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)

OUTPUT_PATH = os.path.join(
    OUTPUT_DIR,
    "multi_camera_test_cam01.mp4"
)


manager = CameraManager(
    CONFIG_PATH,
    BASE_DIR
)

writer = None


try:

    manager.start_enabled()

    while True:

        camera = manager.get_camera(
            "cam_01"
        )

        if camera is None:
            break

        frame = camera.get_latest_frame()

        if frame is not None:

            if writer is None:

                height, width = (
                    frame.shape[:2]
                )

                fourcc = (
                    cv2.VideoWriter_fourcc(
                        *"mp4v"
                    )
                )

                writer = cv2.VideoWriter(
                    OUTPUT_PATH,
                    fourcc,
                    20.0,
                    (width, height)
                )

            writer.write(
                frame
            )

            cv2.imshow(
                "CAM-01",
                frame
            )

        if (
            cv2.waitKey(1)
            & 0xFF
            == ord("q")
        ):

            break

        time.sleep(
            0.01
        )


finally:

    manager.stop_all()

    if writer is not None:
        writer.release()

    cv2.destroyAllWindows()

    print(
        f"Output saved to: "
        f"{OUTPUT_PATH}"
    )