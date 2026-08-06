import json
import cv2
import numpy as np
import os


class ZoneEngine:

    def __init__(self, json_path):

        self.json_path = json_path

        self.site = {}

        self.zones = []

        self.load_zones()

    ####################################################

    def load_zones(self):

        if not os.path.exists(self.json_path):

            print("No zones.json found.")
            return

        with open(self.json_path, "r") as f:

            data = json.load(f)

        self.site = data.get("site", {})

        self.zones = data.get("zones", [])

    ####################################################

    def save_zones(self):

        data = {

            "site": self.site,

            "zones": self.zones

        }

        with open(self.json_path, "w") as f:

            json.dump(data, f, indent=4)

    ####################################################

    def get_zone(self, point):

        """
        Returns zone NAME.

        Example:
        'Production Floor'
        """

        zone = self.get_zone_info(point)

        if zone is None:

            return "Unknown"

        return zone["name"]

    ####################################################

    def get_zone_info(self, point):

        """
        Returns complete zone dictionary.

        Example:

        {
            "id": "...",
            "name": "...",
            "rules": {...},
            "monitor": {...}
        }
        """

        for zone in self.zones:

            polygon = np.array(

                zone["points"],

                dtype=np.int32

            )

            inside = cv2.pointPolygonTest(

                polygon,

                point,

                False

            )

            if inside >= 0:

                return zone

        return None

    ####################################################

    def get_zone_rules(self, point):

        zone = self.get_zone_info(point)

        if zone is None:

            return {}

        return zone.get("rules", {})

    ####################################################

    def get_monitoring_rules(self, point):

        zone = self.get_zone_info(point)

        if zone is None:

            return {}

        return zone.get("monitor", {})

    ####################################################

    def get_all_zones(self):

        return self.zones
    
    
    ####################################################

    def get_zone_by_name(self, zone_name):

        for zone in self.zones:

            if zone["name"] == zone_name:

                return zone

        return None