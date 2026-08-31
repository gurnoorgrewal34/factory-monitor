from utils.geometry import calculate_iou


class PoseMatcher:

    IOU_THRESHOLD = 0.30

    def match(
        self,
        people,
        pose_result
    ):

        if pose_result is None:
            return

        if pose_result.boxes is None:
            return

        if pose_result.keypoints is None:
            return

        pose_boxes = (
            pose_result
            .boxes
            .xyxy
            .cpu()
            .tolist()
        )

        pose_keypoints = (
            pose_result
            .keypoints
            .xy
            .cpu()
            .tolist()
        )

        # ==================================================
        # KEYPOINT CONFIDENCE
        # ==================================================

        if (
            pose_result.keypoints.conf
            is not None
        ):

            pose_confidences = (
                pose_result
                .keypoints
                .conf
                .cpu()
                .tolist()
            )

        else:

            pose_confidences = [

                [1.0] * len(keypoints)

                for keypoints
                in pose_keypoints
            ]


        # ==================================================
        # RESET CURRENT POSE MATCH
        #
        # Important:
        # Do not accidentally reuse old pose keypoints
        # if matching fails on the current frame.
        # ==================================================

        for person in people.values():

            person["pose"] = None
            person["pose_conf"] = None


        # ==================================================
        # MATCH POSE DETECTION -> EXISTING PERSON TRACK
        # ==================================================

        for (
            pose_box,
            keypoints,
            confidences
        ) in zip(
            pose_boxes,
            pose_keypoints,
            pose_confidences
        ):

            best_person = None
            best_iou = 0.0

            for person in people.values():

                person_box = person.get(
                    "box"
                )

                if person_box is None:
                    continue

                iou = calculate_iou(
                    person_box,
                    pose_box
                )

                if iou > best_iou:

                    best_iou = iou
                    best_person = person


            if best_person is None:
                continue

            if (
                best_iou
                <
                self.IOU_THRESHOLD
            ):
                continue


            # ==============================================
            # STORE BOTH XY + CONFIDENCE
            # ==============================================

            best_person["pose"] = (
                keypoints
            )

            best_person["pose_conf"] = (
                confidences
            )

            best_person[
                "pose_match_iou"
            ] = best_iou