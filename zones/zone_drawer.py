import cv2
import numpy as np
import random


class ZoneDrawer:

    def __init__(self, zone_engine):

        self.zone_engine = zone_engine

        self.colors = {}

    ####################################################

    def get_color(self, zone):

        """
        Uses color from zones.json.
        Falls back to random color if not present.
        """

        zone_id = zone["id"]

        if "color" in zone:

            return tuple(zone["color"])

        if zone_id not in self.colors:

            self.colors[zone_id] = (

                random.randint(40, 255),
                random.randint(40, 255),
                random.randint(40, 255)

            )

        return self.colors[zone_id]

    ####################################################

    def draw(self, frame):

        zones = self.zone_engine.get_all_zones()

        for zone in zones:

            pts = np.array(

                zone["points"],

                dtype=np.int32

            )

            color = self.get_color(zone)

            cv2.polylines(

                frame,

                [pts],

                True,

                color,

                3

            )

            x, y = pts[0]

            cv2.putText(

                frame,

                zone["name"],

                (int(x), int(y) - 10),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.7,

                color,

                2

            )

        return frame