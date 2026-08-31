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
    # LOAD ZONES
    ####################################################

    def load_zones(self):

        if not os.path.exists(
            self.json_path
        ):

            self.site = {}

            self.zones = []

            print(
                f"No zones configured: "
                f"{self.json_path}"
            )

            return

        with open(
            self.json_path,
            "r"
        ) as f:

            data = json.load(
                f
            )

        self.site = data.get(
            "site",
            {}
        )

        self.zones = data.get(
            "zones",
            []
        )

    ####################################################
    # SAVE ZONES
    ####################################################

    def save_zones(self):

        directory = (
            os.path.dirname(
                self.json_path
            )
        )

        if directory:

            os.makedirs(
                directory,
                exist_ok=True
            )

        data = {

            "site":
                self.site,

            "zones":
                self.zones
        }

        with open(
            self.json_path,
            "w"
        ) as f:

            json.dump(
                data,
                f,
                indent=4
            )

    ####################################################
    # GET ZONE NAME FROM POINT
    ####################################################

    def get_zone(
        self,
        point
    ):

        """
        Returns zone NAME.

        Example:
        'Production Floor'
        """

        zone = (
            self.get_zone_info(
                point
            )
        )

        if zone is None:

            return "Unknown"

        return zone[
            "name"
        ]

    ####################################################
    # GET COMPLETE ZONE FROM POINT
    ####################################################

    def get_zone_info(
        self,
        point
    ):

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

            points = (
                zone.get(
                    "points"
                )
                or
                []
            )

            if len(
                points
            ) < 3:

                continue

            polygon = (
                np.array(
                    points,
                    dtype=np.int32
                )
            )

            inside = (
                cv2.pointPolygonTest(
                    polygon,
                    point,
                    False
                )
            )

            if inside >= 0:

                return zone

        return None

    
    ####################################################
    # GET RESTRICTED ZONE FOR PERSON BOX
    #
    # Used ONLY by restricted-area detection.
    #
    # This does not change normal zone lookup.
    # Other modules remain unaffected.
    ####################################################

    def get_restricted_zone_for_box(
        self,
        box
    ):

        if box is None:
            return None

        x1, y1, x2, y2 = map(
            float,
            box
        )

        width = (
            x2 - x1
        )

        height = (
            y2 - y1
        )

        if (
            width <= 0
            or
            height <= 0
        ):
            return None


        cx = (
            x1 + x2
        ) / 2.0


        ####################################################
        # MULTIPLE PERSON ANCHOR POINTS
        #
        # This supports:
        # - floor zones
        # - doorway zones
        # - vertical restricted areas
        # - room-sized polygons
        ####################################################

        test_points = [

            # person center
            (
                cx,
                y1 + height * 0.50
            ),

            # lower torso / hip area
            (
                cx,
                y1 + height * 0.72
            ),

            # lower-left body
            (
                x1 + width * 0.30,
                y1 + height * 0.80
            ),

            # lower-right body
            (
                x1 + width * 0.70,
                y1 + height * 0.80
            ),

            # bottom-center / feet
            (
                cx,
                y2
            )
        ]


        ####################################################
        # CHECK ONLY RESTRICTED ZONES
        ####################################################

        for zone in self.zones:

            zone_type = (
                str(
                    zone.get(
                        "zone_type",
                        "normal"
                    )
                )
                .lower()
                .strip()
            )

            if zone_type != "restricted":
                continue


            points = (
                zone.get(
                    "points"
                )
                or
                []
            )

            if len(points) < 3:
                continue


            polygon = np.array(
                points,
                dtype=np.int32
            )


            ################################################
            # If ANY representative body point lies inside
            # the restricted polygon, the person counts as
            # being inside that restricted zone.
            ################################################

            for point in test_points:

                inside = (
                    cv2.pointPolygonTest(
                        polygon,
                        point,
                        False
                    )
                )

                if inside >= 0:
                    return zone


        return None
    
    
    
    ####################################################
    # GET ZONE RULES
    ####################################################

    def get_zone_rules(
        self,
        point
    ):

        zone = (
            self.get_zone_info(
                point
            )
        )

        if zone is None:

            return {}

        return zone.get(
            "rules",
            {}
        )

    ####################################################
    # GET MONITORING RULES
    ####################################################

    def get_monitoring_rules(
        self,
        point
    ):

        zone = (
            self.get_zone_info(
                point
            )
        )

        if zone is None:

            return {}

        return zone.get(
            "monitor",
            {}
        )

    ####################################################
    # GET ALL ZONES
    ####################################################

    def get_all_zones(
        self
    ):

        return self.zones

    ####################################################
    # GET ZONE BY NAME
    ####################################################

    def get_zone_by_name(
        self,
        zone_name
    ):

        for zone in self.zones:

            if (
                zone.get(
                    "name"
                )
                ==
                zone_name
            ):

                return zone

        return None

    ####################################################
    # GET ZONE BY ID
    ####################################################

    def get_zone_by_id(
        self,
        zone_id
    ):

        for zone in self.zones:

            if (
                zone.get(
                    "id"
                )
                ==
                zone_id
            ):

                return zone

        return None

    ####################################################
    # ADD ZONE
    ####################################################

    def add_zone(
        self,
        zone
    ):

        zone_id = (
            zone.get(
                "id"
            )
        )

        if not zone_id:

            raise ValueError(
                "Zone id is required."
            )

        if (
            self.get_zone_by_id(
                zone_id
            )
            is not None
        ):

            raise ValueError(
                f"Zone already exists: "
                f"{zone_id}"
            )

        points = (
            zone.get(
                "points"
            )
            or
            []
        )

        if len(
            points
        ) < 3:

            raise ValueError(
                "A zone requires at least "
                "3 points."
            )

        
        
        
        ####################################################
        # ZONE TYPE
        ####################################################

        zone_type = (
            zone.get(
                "zone_type",
                "normal"
            )
        )

        zone_type = (
            str(zone_type)
            .lower()
            .strip()
        )

        if zone_type not in (
            "normal",
            "restricted"
        ):

            raise ValueError(
                "zone_type must be "
                "'normal' or 'restricted'."
            )

        zone[
            "zone_type"
        ] = zone_type
        
        
        self.zones.append(
            zone
        )

        self.save_zones()

        return zone

    ####################################################
    # UPDATE ZONE
    ####################################################

    def update_zone(
            self,
            zone_id,
            updates
        ):

            zone = (
                self.get_zone_by_id(
                    zone_id
                )
            )

            if zone is None:

                raise ValueError(
                    f"Unknown zone: "
                    f"{zone_id}"
                )

            allowed_fields = (

                "name",
                "points",
                "color",
                "zone_type"
            )

            for key in allowed_fields:

                if key not in updates:
                    continue

                value = updates[key]

                # ==============================================
                # VALIDATE POINTS
                # ==============================================

                if key == "points":

                    if (
                        value is None
                        or
                        len(value) < 3
                    ):

                        raise ValueError(
                            "A zone requires at least "
                            "3 points."
                        )

                # ==============================================
                # NORMALIZE ZONE TYPE
                # ==============================================

                if (
                    key == "zone_type"
                    and
                    value is not None
                ):

                    value = (
                        str(value)
                        .lower()
                        .strip()
                    )

                    if value not in (
                        "normal",
                        "restricted"
                    ):

                        raise ValueError(
                            "zone_type must be "
                            "'normal' or 'restricted'."
                        )

                # ==============================================
                # UPDATE
                # ==============================================

                zone[key] = value

            self.save_zones()

            return zone
        
        
        
    ####################################################
    # DELETE ZONE
    ####################################################

    def delete_zone(
        self,
        zone_id
    ):

        zone = (
            self.get_zone_by_id(
                zone_id
            )
        )

        if zone is None:

            raise ValueError(
                f"Unknown zone: "
                f"{zone_id}"
            )

        self.zones.remove(
            zone
        )

        self.save_zones()

        return zone