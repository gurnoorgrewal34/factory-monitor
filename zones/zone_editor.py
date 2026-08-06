import cv2
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import VIDEO_PATH


points = []
zones = {}

drawing = False

window_name = "Zone Editor"

current_name = ""


# ----------------------------
# Mouse
# ----------------------------

def mouse(event, x, y, flags, param):

    global image

    if event == cv2.EVENT_LBUTTONDOWN:

        points.append((x, y))

        cv2.circle(image, (x, y), 5, (0, 0, 255), -1)

        if len(points) > 1:

            cv2.line(
                image,
                points[-2],
                points[-1],
                (255,0,0),
                2
            )


# ----------------------------
# Load First Frame
# ----------------------------

cap = cv2.VideoCapture(VIDEO_PATH)

ret, frame = cap.read()

cap.release()

if not ret:

    print("Cannot load first frame.")

    exit()

clone = frame.copy()

image = frame.copy()

cv2.namedWindow(window_name)

cv2.setMouseCallback(window_name, mouse)

print("----------------------------------")
print("Left Click : Add Point")
print("C : Close Polygon")
print("R : Reset Current")
print("S : Save")
print("ESC : Exit")
print("----------------------------------")


while True:

    display = image.copy()

    cv2.putText(
        display,
        "Press C after drawing polygon",
        (20,30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0,255,255),
        2
    )

    cv2.imshow(window_name, display)

    key = cv2.waitKey(1) & 0xFF


    # Close Polygon
    if key == ord('c'):

        if len(points) < 3:

            print("Need minimum 3 points.")

            continue

        cv2.line(
            image,
            points[-1],
            points[0],
            (255,0,0),
            2
        )

        cv2.imshow(window_name, image)

        cv2.waitKey(300)

        print("\nEnter Zone Name")
        zone_name = input("> ")

        zones[zone_name] = points.copy()

        print("Saved :", zone_name)

        points.clear()


    # Reset current polygon
    elif key == ord('r'):

        image = clone.copy()

        points.clear()

        print("Reset.")


    # Save JSON
    elif key == ord('s'):

        with open("zones/zones.json","w") as f:

            json.dump(zones,f,indent=4)

        print("zones.json saved")


    elif key == 27:

        break


cv2.destroyAllWindows()