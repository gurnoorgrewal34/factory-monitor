from alerts.alert_manager import AlertManager


class PhoneBehaviour:

    def __init__(self):

        self.alert_manager = AlertManager()

        # Number of consecutive frames required
        self.FRAME_THRESHOLD = 20

        # Minimum confidence required from the phone detector
        self.PHONE_CONFIDENCE = 0.35

        # Expand person bounding box slightly when matching phone
        # This helps when the phone is near the hand/body boundary.
        self.PERSON_BOX_EXPANSION = 0.15

        # Maximum normalized distance allowed when phone is
        # just outside the person's bounding box.
        self.MAX_CENTER_DISTANCE = 0.35

    # --------------------------------------------------
    # Check Phone Behaviour
    # --------------------------------------------------

    def check(self, people, phone_results):

        alerts = []

        # ----------------------------------------------
        # Reset current-frame phone detection
        # ----------------------------------------------

        for person in people.values():

            person["phone_detected"] = False

        # ----------------------------------------------
        # No phone detection result
        # ----------------------------------------------

        if not phone_results:

            self.reset_people(people)

            return alerts

        result = phone_results[0]

        if result.boxes is None or len(result.boxes) == 0:

            self.reset_people(people)

            return alerts

        # ----------------------------------------------
        # Process phone detections
        # ----------------------------------------------

        for det in result.boxes:

            cls = int(det.cls[0])

            label = result.names[cls]

            if label != "mobile_phone":

                continue

            # ------------------------------------------
            # Confidence
            # ------------------------------------------

            confidence = float(det.conf[0])

            if confidence < self.PHONE_CONFIDENCE:

                continue

            # ------------------------------------------
            # Phone bounding box
            # ------------------------------------------

            px1, py1, px2, py2 = map(
                int,
                det.xyxy[0]
            )

            phone_cx = (px1 + px2) / 2.0
            phone_cy = (py1 + py2) / 2.0

            best_person = None
            best_score = 0.0

            # ------------------------------------------
            # Match phone to person
            # ------------------------------------------

            for person in people.values():

                person_box = person.get("box")

                if not person_box:

                    continue

                x1, y1, x2, y2 = map(
                    float,
                    person_box
                )

                person_width = max(
                    x2 - x1,
                    1.0
                )

                person_height = max(
                    y2 - y1,
                    1.0
                )

                # --------------------------------------
                # Expanded person box
                # --------------------------------------

                expand_x = person_width * self.PERSON_BOX_EXPANSION
                expand_y = person_height * self.PERSON_BOX_EXPANSION

                ex1 = x1 - expand_x
                ey1 = y1 - expand_y

                ex2 = x2 + expand_x
                ey2 = y2 + expand_y

                # --------------------------------------
                # Center inside normal person box
                # --------------------------------------

                inside_normal = (

                    x1 <= phone_cx <= x2

                    and

                    y1 <= phone_cy <= y2

                )

                # --------------------------------------
                # Center inside expanded person box
                # --------------------------------------

                inside_expanded = (

                    ex1 <= phone_cx <= ex2

                    and

                    ey1 <= phone_cy <= ey2

                )

                # --------------------------------------
                # Normalized distance
                # --------------------------------------

                person_cx = (x1 + x2) / 2.0
                person_cy = (y1 + y2) / 2.0

                dx = abs(phone_cx - person_cx) / person_width
                dy = abs(phone_cy - person_cy) / person_height

                distance = (dx * dx + dy * dy) ** 0.5

                # --------------------------------------
                # Matching score
                # --------------------------------------

                score = 0.0

                if inside_normal:

                    # Strongest possible association
                    score = 1.0

                elif inside_expanded:

                    # Phone slightly outside body box,
                    # probably near hand.
                    score = 0.85

                elif distance <= self.MAX_CENTER_DISTANCE:

                    # Nearby phone.
                    score = 0.60

                # --------------------------------------
                # Confidence contributes only after
                # spatial association.
                # --------------------------------------

                score *= confidence

                # --------------------------------------
                # Keep best person
                # --------------------------------------

                if score > best_score:

                    best_score = score
                    best_person = person

            # ------------------------------------------
            # No valid person
            # ------------------------------------------

            if best_person is None:

                continue

            # ------------------------------------------
            # Require reasonable association
            # ------------------------------------------

            if best_score < 0.30:

                continue

            # ------------------------------------------
            # Zone policy
            # ------------------------------------------

            rules = best_person.get(
                "zone_rules",
                {}
            )

            # Phone allowed in this zone
            if rules.get("phone_allowed", True):

                continue

            # ------------------------------------------
            # Valid phone detection
            # ------------------------------------------

            best_person["phone_detected"] = True

        # ----------------------------------------------
        # Update phone counters
        # ----------------------------------------------

        for person in people.values():

            if person["phone_detected"]:

                person["phone_frames"] += 1

            else:

                person["phone_frames"] = 0

                person["phone_alerted"] = False

                self.alert_manager.clear(
                    person["id"],
                    "Phone Usage"
                )

            # ------------------------------------------
            # Raise alert after threshold
            # ------------------------------------------

            if (

                person["phone_frames"]
                >= self.FRAME_THRESHOLD

                and

                not person["phone_alerted"]

            ):

                if self.alert_manager.should_alert(
                    person["id"],
                    "Phone Usage"
                ):

                    alerts.append({

                        "type": "Phone Usage",

                        "person_id": person["id"],

                        "severity": "MEDIUM",

                        "zone": person["zone"]

                    })

                    person["phone_alerted"] = True

        return alerts

    # --------------------------------------------------
    # Reset Phone State
    # --------------------------------------------------

    def reset_people(self, people):

        for person in people.values():

            person["phone_frames"] = 0

            person["phone_alerted"] = False

            person["phone_detected"] = False

            self.alert_manager.clear(
                person["id"],
                "Phone Usage"
            )