from detectors.helmet_detector import HelmetDetector
from detectors.phone_detector import PhoneDetector
from detectors.fire_detector import FireDetector
from detectors.smoking_detector import SmokingDetector

class FrameProcessor:

    def __init__(

        self,

        tracker,

        zone_drawer,

        person_processor,

        drawing_processor,

        group_processor,

        alert_overlay,

        behaviour

    ):

        self.tracker = tracker

        self.zone_drawer = zone_drawer

        self.person_processor = person_processor

        self.drawing_processor = drawing_processor

        self.group_processor = group_processor

        self.alert_overlay = alert_overlay

        self.behaviour = behaviour

        self.helmet_detector = HelmetDetector()

        self.phone_detector = PhoneDetector()
        
        self.fire_detector = FireDetector()
        self.smoking_detector = SmokingDetector()

    ##################################################

    def process(self, frame):

        ##################################################
        # Person Detection
        ##################################################

        results = self.tracker.track(frame)

        result = results[0]

        boxes = result.boxes

        annotated = result.plot()

        ##################################################
        # Object Detectors
        ##################################################

        helmet_results = self.helmet_detector.detect(frame)

        phone_results = self.phone_detector.detect(frame)
        
        fire_results = self.fire_detector.detect(frame)
        
        smoking_results = self.smoking_detector.detect(frame)
        ##################################################
        # Draw Zones
        ##################################################

        annotated = self.zone_drawer.draw(annotated)

        ##################################################
        # Person Processing
        ##################################################

        if boxes.id is not None:

            ids = boxes.id.int().cpu().tolist()

            xyxy = boxes.xyxy.cpu().tolist()

            for track_id, box in zip(ids, xyxy):

                person, alerts, draw_box = self.person_processor.process(

                    track_id,

                    box

                )

                if alerts:

                    self.alert_overlay.update(alerts)

                    for alert in alerts:

                        print(alert)

                annotated = self.drawing_processor.draw_person(

                    annotated,

                    draw_box,

                    person

                )

        ##################################################
        # Helmet Behaviour
        ##################################################

        helmet_alerts = self.behaviour.process_helmet(

            self.person_processor.memory.all_people(),

            helmet_results

        )

        if helmet_alerts:

            self.alert_overlay.update(helmet_alerts)

            for alert in helmet_alerts:

                print(alert)

        ##################################################
        # Phone Behaviour
        ##################################################

        phone_alerts = self.behaviour.process_phone(

            self.person_processor.memory.all_people(),

            phone_results

        )

        if phone_alerts:

            self.alert_overlay.update(phone_alerts)

            for alert in phone_alerts:

                print(alert)
                
        
        ##################################################
        # Smoking Behaviour
        ##################################################

        smoking_alerts = self.behaviour.process_smoking(

            self.person_processor.memory.all_people(),

            smoking_results

        )

        if smoking_alerts:

            self.alert_overlay.update(smoking_alerts)

            for alert in smoking_alerts:

                print(alert)
                
                
                
        ##################################################
        # Fire Behaviour
        ##################################################

        fire_alerts = self.behaviour.fire.check(

            fire_results

        )

        if fire_alerts:

            self.alert_overlay.update(fire_alerts)

            for alert in fire_alerts:

                print(alert)        

        
        ##################################################
        # Smoke Behaviour
        ##################################################

        smoke_alerts = self.behaviour.smoke.check(

            fire_results

        )

        if smoke_alerts:

            self.alert_overlay.update(smoke_alerts)

            for alert in smoke_alerts:

                print(alert)
        
        ##################################################
        # Group Behaviours
        ##################################################

        group_alerts = self.group_processor.process()

        if group_alerts:

            self.alert_overlay.update(group_alerts)

            for alert in group_alerts:

                print(alert)

        ##################################################
        # Draw Alert Overlay
        ##################################################

        annotated = self.alert_overlay.draw(annotated)

        return annotated
    
       