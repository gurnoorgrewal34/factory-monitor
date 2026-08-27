from collections import deque

from alerts.alert_manager import AlertManager

from app.config import DEBUG


class SmokingBehaviour:

    def __init__(self):

        self.alert_manager = AlertManager()

        ##################################################
        # TEMPORAL CONFIRMATION
        #
        # A single cigarette detection must NOT create
        # a Smoking alert.
        #
        # We require 3 positive observations among the
        # latest 5 detector observations.
        ##################################################

        self.WINDOW_SIZE = 5

        self.MIN_VALID_OBSERVATIONS = 3

        ##################################################
        # CLEAR CONFIRMATION
        #
        # Require several negative detector observations
        # before resetting an active smoking state.
        ##################################################

        self.CLEAR_OBSERVATIONS = 3

        ##################################################
        # ASSOCIATION SETTINGS
        #
        # Cigarettes are tiny compared with a person box,
        # therefore normal person-vs-cigarette IoU is not
        # a reliable association measure.
        ##################################################

        self.MIN_CIGARETTE_CONTAINMENT = 0.35

        # Slightly expand person horizontally so a cigarette
        # near a hand beside the body can still associate.
        self.HORIZONTAL_MARGIN_RATIO = 0.15

        ##################################################
        # Per-person state
        #
        # person_id -> {
        #     "history": deque,
        #     "negative_count": int,
        #     "alerted": bool
        # }
        ##################################################

        self.states = {}

    ##################################################
    # GET / CREATE PERSON STATE
    ##################################################

    def _get_state(self, person_id):

        state = self.states.get(
            person_id
        )

        if state is None:

            state = {

                "history": deque(
                    maxlen=self.WINDOW_SIZE
                ),

                "negative_count": 0,

                "alerted": False

            }

            self.states[
                person_id
            ] = state

        return state

    ##################################################
    # BOX INTERSECTION
    ##################################################

    @staticmethod
    def _intersection_area(
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

        width = max(
            0.0,
            ix2 - ix1
        )

        height = max(
            0.0,
            iy2 - iy1
        )

        return (
            width
            *
            height
        )

    ##################################################
    # CIGARETTE -> PERSON ASSOCIATION
    ##################################################

    def _association_score(
        self,
        person_box,
        cigarette_box
    ):

        px1, py1, px2, py2 = map(
            float,
            person_box
        )

        cx1, cy1, cx2, cy2 = map(
            float,
            cigarette_box
        )

        person_width = max(
            1.0,
            px2 - px1
        )

        person_height = max(
            1.0,
            py2 - py1
        )

        ##################################################
        # We care mainly about the upper part of the body:
        #
        # head / mouth / chest / hands.
        #
        # A cigarette detected around somebody's feet
        # should not classify that person as smoking.
        ##################################################

        margin_x = (
            person_width
            *
            self.HORIZONTAL_MARGIN_RATIO
        )

        upper_body_box = [

            px1 - margin_x,

            py1,

            px2 + margin_x,

            py1
            +
            person_height * 0.70

        ]

        ##################################################
        # Cigarette center
        ##################################################

        cigarette_center_x = (
            cx1 + cx2
        ) / 2.0

        cigarette_center_y = (
            cy1 + cy2
        ) / 2.0

        center_inside = (

            upper_body_box[0]
            <= cigarette_center_x
            <= upper_body_box[2]

            and

            upper_body_box[1]
            <= cigarette_center_y
            <= upper_body_box[3]

        )

        ##################################################
        # Cigarette containment
        #
        # Normal IoU is bad here because:
        #
        # cigarette = tiny
        # person    = huge
        #
        # Instead:
        #
        # intersection / cigarette area
        ##################################################

        cigarette_area = max(

            1.0,

            (
                cx2 - cx1
            )
            *
            (
                cy2 - cy1
            )

        )

        intersection = (
            self._intersection_area(
                upper_body_box,
                cigarette_box
            )
        )

        containment = (
            intersection
            /
            cigarette_area
        )

        ##################################################
        # Reject poor associations
        ##################################################

        if (
            not center_inside
            and
            containment
            <
            self.MIN_CIGARETTE_CONTAINMENT
        ):

            return 0.0

        ##################################################
        # Prefer cigarettes nearer the upper-body center
        ##################################################

        body_center_x = (
            upper_body_box[0]
            +
            upper_body_box[2]
        ) / 2.0

        body_center_y = (
            upper_body_box[1]
            +
            upper_body_box[3]
        ) / 2.0

        dx = (
            cigarette_center_x
            -
            body_center_x
        )

        dy = (
            cigarette_center_y
            -
            body_center_y
        )

        normalized_distance = (

            (
                dx * dx
                +
                dy * dy
            )
            ** 0.5

        ) / max(
            person_height,
            1.0
        )

        ##################################################
        # Higher = better association
        ##################################################

        score = (

            containment

            +
            max(
                0.0,
                1.0 - normalized_distance
            )

        )

        return score

    ##################################################
    # FIND BEST PERSON
    ##################################################

    def _find_best_person(
        self,
        people,
        cigarette_box
    ):

        best_person = None

        best_score = 0.0

        for person in people.values():

            person_box = person.get(
                "box"
            )

            if person_box is None:
                continue

            score = (
                self._association_score(
                    person_box,
                    cigarette_box
                )
            )

            if score > best_score:

                best_score = score

                best_person = person

        return (
            best_person,
            best_score
        )

    ##################################################
    # MAIN CHECK
    ##################################################

    def check(
        self,
        people,
        smoking_results
    ):

        alerts = []

        ##################################################
        # IDs receiving cigarette evidence during THIS
        # fresh SmokingDetector inference.
        ##################################################

        positive_ids = set()

        ##################################################
        # EXTRACT CIGARETTE DETECTIONS
        ##################################################

        if smoking_results:

            result = smoking_results[0]

            if result.boxes is not None:

                for det in result.boxes:

                    cls = int(
                        det.cls[0]
                    )

                    label = (
                        result.names[cls]
                        .lower()
                        .strip()
                    )

                    if label != "cigarette":
                        continue

                    confidence = float(
                        det.conf[0]
                    )

                    cigarette_box = (
                        det.xyxy[0]
                        .cpu()
                        .tolist()
                    )

                    ##################################################
                    # Find most likely owner of cigarette
                    ##################################################

                    (
                        best_person,
                        score
                    ) = self._find_best_person(

                        people,

                        cigarette_box

                    )

                    if best_person is None:
                        continue

                    ##################################################
                    # Zone policy
                    ##################################################

                    # rules = (
                    #     best_person.get(
                    #         "zone_rules"
                    #     )
                    #     or {}
                    # )

                    # # Smoking is explicitly permitted here.
                    # if rules.get(
                    #     "smoking_allowed",
                    #     False
                    # ):

                    #     continue

                    person_id = (
                        best_person["id"]
                    )

                    positive_ids.add(
                        person_id
                    )

                    if DEBUG:

                        print(

                            "SMOKING CANDIDATE -> "

                            f"Person={person_id} | "

                            f"Confidence="
                            f"{confidence:.3f} | "

                            f"Association="
                            f"{score:.3f}"

                        )

        ##################################################
        # UPDATE TEMPORAL STATE
        ##################################################

        current_person_ids = set(
            people.keys()
        )

        for person_id in current_person_ids:

            person = people.get(
                person_id
            )

            if person is None:
                continue

            state = self._get_state(
                person_id
            )

            positive = (
                person_id
                in positive_ids
            )

            state["history"].append(
                positive
            )

            ##################################################
            # Positive observation
            ##################################################

            if positive:

                state[
                    "negative_count"
                ] = 0

            ##################################################
            # Negative observation
            ##################################################

            else:

                state[
                    "negative_count"
                ] += 1

            valid_count = sum(
                1
                for value
                in state["history"]
                if value
            )

            ##################################################
            # DEBUG
            ##################################################

            if DEBUG:

                print(

                    "SMOKING WINDOW -> "

                    f"Person={person_id} | "

                    f"Valid="
                    f"{valid_count}/"
                    f"{len(state['history'])} | "

                    f"Required="
                    f"{self.MIN_VALID_OBSERVATIONS}/"
                    f"{self.WINDOW_SIZE} | "

                    f"Negative="
                    f"{state['negative_count']}/"
                    f"{self.CLEAR_OBSERVATIONS}"

                )

            ##################################################
            # CONFIRM SMOKING
            ##################################################

            if (

                len(
                    state["history"]
                )
                >=
                self.WINDOW_SIZE

                and

                valid_count
                >=
                self.MIN_VALID_OBSERVATIONS

            ):

                ##################################################
                # Double-check zone policy using current state.
                ##################################################

                # rules = (
                #     person.get(
                #         "zone_rules"
                #     )
                #     or {}
                # )

                # if rules.get(
                #     "smoking_allowed",
                #     False
                # ):

                #     continue

                if not state["alerted"]:

                    if (
                        self.alert_manager
                        .should_alert(
                            person_id,
                            "Smoking"
                        )
                    ):

                        state[
                            "alerted"
                        ] = True

                        alerts.append({

                            "type": "Smoking",

                            "person_id":
                                person_id,

                            "zone":
                                person.get(
                                    "zone",
                                    "Unknown"
                                ),

                            "severity": "HIGH",

                            "persistent": False,

                            "display_seconds": 5.0

                        })

                        print(

                            "[ALERT] [SMOKING] "

                            f"Person ID="
                            f"{person_id} | "

                            f"Zone="
                            f"{person.get('zone')}"

                        )

            ##################################################
            # CLEAR SMOKING STATE
            ##################################################

            if (

                state["alerted"]

                and

                state["negative_count"]
                >=
                self.CLEAR_OBSERVATIONS

            ):

                state[
                    "alerted"
                ] = False

                state[
                    "history"
                ].clear()

                state[
                    "negative_count"
                ] = 0

                self.alert_manager.clear(

                    person_id,

                    "Smoking"

                )

                if DEBUG:

                    print(

                        "SMOKING CLEARED -> "

                        f"Person={person_id}"

                    )

        ##################################################
        # Remove states belonging to IDs no longer known
        ##################################################

        stale_ids = [

            person_id

            for person_id
            in self.states

            if person_id
            not in current_person_ids

        ]

        for person_id in stale_ids:

            self.alert_manager.clear(
                person_id,
                "Smoking"
            )

            self.states.pop(
                person_id,
                None
            )

        return alerts