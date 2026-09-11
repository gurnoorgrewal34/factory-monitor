import math


class StablePersonResolver:

    def __init__(
        self,
        max_gap_seconds=3.0,
        max_center_distance=0.75,
        min_iou=0.05
    ):

        self.max_gap_seconds = (
            max_gap_seconds
        )

        self.max_center_distance = (
            max_center_distance
        )

        self.min_iou = (
            min_iou
        )

        self.next_stable_id = 1

        # Raw BoT-SORT ID -> Stable application ID
        self.raw_to_stable = {}

        # Stable ID -> recent tracking state
        self.tracks = {}

        # Raw IDs visible in current frame
        self.current_raw_ids = set()

        # Prevent two detections in same frame
        # getting the same stable ID.
        self.assigned_this_frame = set()


    # ==================================================
    # BEGIN FRAME
    # ==================================================

    def begin_frame(
        self,
        active_raw_ids
    ):

        self.current_raw_ids = set(
            int(x)
            for x in active_raw_ids
        )

        self.assigned_this_frame = set()


    # ==================================================
    # BOX HELPERS
    # ==================================================

    def _center(
        self,
        box
    ):

        x1, y1, x2, y2 = map(
            float,
            box
        )

        return (
            (x1 + x2) / 2.0,
            (y1 + y2) / 2.0
        )


    def _height(
        self,
        box
    ):

        return max(
            1.0,
            float(
                box[3] - box[1]
            )
        )


    def _iou(
        self,
        box_a,
        box_b
    ):

        ax1, ay1, ax2, ay2 = map(
            float,
            box_a
        )

        bx1, by1, bx2, by2 = map(
            float,
            box_b
        )

        ix1 = max(
            ax1,
            bx1
        )

        iy1 = max(
            ay1,
            by1
        )

        ix2 = min(
            ax2,
            bx2
        )

        iy2 = min(
            ay2,
            by2
        )

        iw = max(
            0.0,
            ix2 - ix1
        )

        ih = max(
            0.0,
            iy2 - iy1
        )

        intersection = (
            iw * ih
        )

        area_a = max(
            0.0,
            ax2 - ax1
        ) * max(
            0.0,
            ay2 - ay1
        )

        area_b = max(
            0.0,
            bx2 - bx1
        ) * max(
            0.0,
            by2 - by1
        )

        union = (
            area_a
            +
            area_b
            -
            intersection
        )

        if union <= 0:

            return 0.0

        return (
            intersection
            /
            union
        )


    # ==================================================
    # CREATE NEW STABLE PERSON
    # ==================================================

    def _create_new(
        self,
        raw_track_id,
        box,
        timestamp
    ):

        stable_id = (
            self.next_stable_id
        )

        self.next_stable_id += 1

        self.raw_to_stable[
            raw_track_id
        ] = stable_id

        self.tracks[
            stable_id
        ] = {

            "stable_id":
                stable_id,

            "last_raw_id":
                raw_track_id,

            "box":
                list(box),

            "center":
                self._center(
                    box
                ),

            "height":
                self._height(
                    box
                ),

            "last_seen":
                timestamp,
        }

        self.assigned_this_frame.add(
            stable_id
        )

        print(
            f"STABLE ID NEW -> "
            f"Raw={raw_track_id} "
            f"-> Stable={stable_id}"
        )

        return stable_id


    # ==================================================
    # RESOLVE RAW TRACK ID
    # ==================================================

    def resolve(
        self,
        raw_track_id,
        box,
        timestamp
    ):

        raw_track_id = int(
            raw_track_id
        )

        timestamp = float(
            timestamp
        )

        # ----------------------------------------------
        # Raw tracker still has same ID.
        # Keep existing stable ID.
        # ----------------------------------------------

        existing_stable_id = (
            self.raw_to_stable.get(
                raw_track_id
            )
        )

        if (
            existing_stable_id is not None
            and
            existing_stable_id
            not in self.assigned_this_frame
            and
            existing_stable_id
            in self.tracks
        ):

            self._update_track(
                stable_id=
                    existing_stable_id,

                raw_track_id=
                    raw_track_id,

                box=
                    box,

                timestamp=
                    timestamp
            )

            return existing_stable_id


        # ----------------------------------------------
        # New raw ID.
        #
        # Try to reconnect it with a recently lost
        # stable person.
        # ----------------------------------------------

        current_center = (
            self._center(
                box
            )
        )

        current_height = (
            self._height(
                box
            )
        )

        best_stable_id = None

        best_score = None


        for (
            stable_id,
            track
        ) in self.tracks.items():

            # One stable person cannot represent two
            # detections in same frame.
            if (
                stable_id
                in self.assigned_this_frame
            ):

                continue


            old_raw_id = track.get(
                "last_raw_id"
            )

            # If old BoT-SORT track is still visible in
            # this same frame, this is another person.
            if (
                old_raw_id
                in self.current_raw_ids
            ):

                continue


            gap = (
                timestamp
                -
                track["last_seen"]
            )

            if (
                gap < 0
                or
                gap > self.max_gap_seconds
            ):

                continue


            old_center = track[
                "center"
            ]

            dx = (
                current_center[0]
                -
                old_center[0]
            )

            dy = (
                current_center[1]
                -
                old_center[1]
            )

            center_distance = math.sqrt(
                dx * dx
                +
                dy * dy
            )

            reference_height = max(
                current_height,
                track.get(
                    "height",
                    current_height
                ),
                1.0
            )

            normalized_distance = (
                center_distance
                /
                reference_height
            )

            overlap = self._iou(
                box,
                track["box"]
            )


            # Size check prevents joining very differently
            # sized people.
            old_height = max(
                1.0,
                track.get(
                    "height",
                    current_height
                )
            )

            size_ratio = max(
                current_height
                /
                old_height,

                old_height
                /
                current_height
            )

            if size_ratio > 1.8:

                continue


            # Candidate must either still overlap or be
            # reasonably close to the previous location.
            if (
                overlap < self.min_iou
                and
                normalized_distance
                >
                self.max_center_distance
            ):

                continue


            # Smaller score = better match.
            score = (
                normalized_distance
                +
                (
                    gap
                    /
                    max(
                        self.max_gap_seconds,
                        0.001
                    )
                )
                * 0.25
                -
                (
                    overlap
                    * 0.50
                )
            )


            if (
                best_score is None
                or
                score < best_score
            ):

                best_score = score

                best_stable_id = (
                    stable_id
                )


        # ----------------------------------------------
        # Reconnect fragmented BoT-SORT track
        # ----------------------------------------------

        if best_stable_id is not None:

            old_raw_id = (
                self.tracks[
                    best_stable_id
                ][
                    "last_raw_id"
                ]
            )

            self.raw_to_stable[
                raw_track_id
            ] = (
                best_stable_id
            )

            self._update_track(
                stable_id=
                    best_stable_id,

                raw_track_id=
                    raw_track_id,

                box=
                    box,

                timestamp=
                    timestamp
            )

            print(
                "STABLE ID RECONNECTED -> "
                f"Raw {old_raw_id} "
                f"changed to Raw {raw_track_id} | "
                f"Stable Person "
                f"{best_stable_id}"
            )

            return best_stable_id


        # ----------------------------------------------
        # Truly new person
        # ----------------------------------------------

        return self._create_new(
            raw_track_id,
            box,
            timestamp
        )


    # ==================================================
    # UPDATE TRACK
    # ==================================================

    def _update_track(
        self,
        stable_id,
        raw_track_id,
        box,
        timestamp
    ):

        track = self.tracks[
            stable_id
        ]

        track[
            "last_raw_id"
        ] = raw_track_id

        track[
            "box"
        ] = list(
            box
        )

        track[
            "center"
        ] = self._center(
            box
        )

        track[
            "height"
        ] = self._height(
            box
        )

        track[
            "last_seen"
        ] = timestamp

        self.raw_to_stable[
            raw_track_id
        ] = stable_id

        self.assigned_this_frame.add(
            stable_id
        )


    # ==================================================
    # CLEANUP
    # ==================================================

    def cleanup(
        self,
        timestamp,
        max_age_seconds=10.0
    ):

        timestamp = float(
            timestamp
        )

        stale_stable_ids = []

        for (
            stable_id,
            track
        ) in self.tracks.items():

            age = (
                timestamp
                -
                track["last_seen"]
            )

            if age > max_age_seconds:

                stale_stable_ids.append(
                    stable_id
                )


        for stable_id in stale_stable_ids:

            self.tracks.pop(
                stable_id,
                None
            )


        stale_raw_ids = [

            raw_id

            for (
                raw_id,
                stable_id
            )
            in self.raw_to_stable.items()

            if stable_id
            not in self.tracks
        ]


        for raw_id in stale_raw_ids:

            self.raw_to_stable.pop(
                raw_id,
                None
            )