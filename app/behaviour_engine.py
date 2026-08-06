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

from zones.zone_policy import ZonePolicy

class BehaviourEngine:

    def __init__(self, zone_engine):

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
        # Running
        ####################################################

        alert = self.running.check(person)

        if alert is not None:

            alerts.append(alert)
            
        return alerts
            

    ####################################################
    # Group Behaviours
    ####################################################

    def process_group(self, people):

        alerts = []

        alerts.extend(

            self.social.check(people)

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