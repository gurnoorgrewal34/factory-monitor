from utils.geometry import calculate_iou


class PoseMatcher:

    def match(self, people, pose_result):

        if pose_result.boxes is None:
            return

        if pose_result.keypoints is None:
            return

        pose_boxes = pose_result.boxes.xyxy.cpu().tolist()
        pose_keypoints = pose_result.keypoints.xy.cpu().tolist()

        ####################################################
        # Match every pose to a tracked person
        ####################################################

        for pose_box, keypoints in zip(pose_boxes, pose_keypoints):

            best_person = None
            best_iou = 0.0

            for person in people.values():

                iou = calculate_iou(

                    person["box"],

                    pose_box

                )

                if iou > best_iou:

                    best_iou = iou
                    best_person = person

            ################################################

            if best_person is None:

                continue

            if best_iou < 0.30:

                continue

            ################################################
            # Store pose
            ################################################

            best_person["pose"] = keypoints
            
            