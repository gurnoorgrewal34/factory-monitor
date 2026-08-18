from behaviours.restricted_area import RestrictedAreaBehaviour
from behaviours.loitering import LoiteringBehaviour
from behaviours.social_loitering import SocialLoiteringBehaviour
from behaviours.helmet_behaviour import HelmetBehaviour
from behaviours.phone_behaviour import PhoneBehaviour
from behaviours.fire_behaviour import FireBehaviour
from behaviours.smoke_behaviour import SmokeBehaviour
from behaviours.running_behaviour import RunningBehaviour
from behaviours.smoking_behaviour import SmokingBehaviour

from behaviours.activity_behaviour import ActivityBehaviour
from behaviours.pose_behaviour import PoseBehaviour
from behaviours.idle_behaviour import IdleBehaviour

from zones.zone_policy import ZonePolicy

from behaviours.group_behaviour import GroupBehaviour
from behaviours.group_standing import GroupStandingBehaviour

from behaviours.fall_behaviour import FallBehaviour

from behaviours.sleep_behaviour import SleepBehaviour
from behaviours.after_shift_behaviour import AfterShiftBehaviour

from app.config import RUNNING_ENABLED

class BehaviourEngine:

    def __init__(self, zone_engine, orchestrator=None):

        self.orchestrator = orchestrator

        self.zone_policy = ZonePolicy(zone_engine)

        self.restricted = RestrictedAreaBehaviour()
        self.loitering = LoiteringBehaviour()
        self.running = RunningBehaviour()
        self.activity = ActivityBehaviour()
        self.social = SocialLoiteringBehaviour()
        self.helmet = HelmetBehaviour()
        self.phone = PhoneBehaviour()
        self.smoking = SmokingBehaviour()
        
        self.fire = FireBehaviour()
        self.smoke = SmokeBehaviour()
        self.pose = PoseBehaviour()
        self.fall = FallBehaviour()
        
        self.idle = IdleBehaviour()
        self.group = GroupBehaviour()
        self.group_standing = GroupStandingBehaviour()
        
        
        self.sleep = SleepBehaviour()
        self.after_shift = AfterShiftBehaviour()
        
    ####################################################
    # Individual Behaviours
    ####################################################

    def process(self, person):

        alerts = []

        zone = person["zone"]

        ####################################################
        # Restricted Area
        ####################################################

        if self.zone_policy.allows(zone, "restricted"):

            alert = self.restricted.check(person)

            if alert is not None:
                alerts.append(alert)

        ####################################################
        # Loitering
        ####################################################

        if self.zone_policy.allows(zone, "loitering"):

            alert = self.loitering.check(person)

            if alert is not None:
                alerts.append(alert)

        ####################################################
        # Activity Status
        ####################################################

        self.activity.check(person)
        
        ####################################################
        # Idle Behaviour
        ####################################################

        alert = self.idle.check(person)

        if alert is not None:
            alerts.append(alert)
            
            
    
        
        ####################################################
        # Running
        ####################################################
        if RUNNING_ENABLED:

            alert = self.running.check(person)

            if alert is not None:
                 alerts.append(alert)
            

        return alerts

    ####################################################
    # Group Behaviours
    ####################################################

    def process_group(self, people):

        alerts = []

        # ======================================================
        # GROUP CLASSIFICATION
        #
        # This ONLY classifies the relationship between people.
        #
        # It does NOT generate alerts.
        # ======================================================

        self.group.process(people)

        # ======================================================
        # PEOPLE STANDING IN GROUP
        #
        # This is an independent alert behaviour.
        #
        # It does NOT modify:
        # - Idle
        # - Standing Without Working
        # - Running
        # - Activity
        # - Social Loitering
        # ======================================================

        group_alerts = self.group_standing.check(
            people
        )

        if group_alerts:

            alerts.extend(
                group_alerts
            )

        # ======================================================
        # SOCIAL LOITERING
        #
        # Completely independent from group standing.
        # ======================================================

        social_alerts = self.social.check(
            people
        )

        if social_alerts:

            alerts.extend(
                social_alerts
            )

        return alerts
        
    
    ####################################################
    # Helmet Behaviour
    ####################################################

    def process_helmet(self, people, helmet_results):

        return self.helmet.check(
            people,
            helmet_results
        )
        
    ####################################################
    # Phone Behaviour
    ####################################################

    def process_phone(self, people, phone_results):

        return self.phone.check(
            people,
            phone_results
        )    
        
    ####################################################
    # Smoking Behaviour
    ####################################################    
    def process_smoking(self, people, smoking_results):

        return self.smoking.check(

        people,

        smoking_results

    )    
        
    ####################################################
    # Fall Behaviour
    ####################################################

    def process_fall(
        self,
        fall_results
    ):

        return self.fall.check(
            fall_results
        )
        
        
    ####################################################
    # Sleep Behaviour
    ####################################################

    def process_sleep(self, sleep_engine):

        return self.sleep.process(
            sleep_engine
        )
        
        
    ####################################################
    # After-Shift Behaviour
    ####################################################

    def process_after_shift(
        self,
        current_people,
        frame_time
    ):

        return self.after_shift.process(
            current_people,
            frame_time
        )