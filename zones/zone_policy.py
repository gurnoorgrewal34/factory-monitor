class ZonePolicy:

    def __init__(self, zone_engine):

        self.zone_engine = zone_engine

    ##################################################

    def allows(self, zone_name, behaviour):

        zone = self.zone_engine.get_zone_by_name(zone_name)

        if zone is None:

            return True

        rules = zone.get("rules", {})

        mapping = {

            "helmet": "helmet_required",

            "phone": "phone_allowed",

            "loitering": "loitering_allowed",

            "restricted": "restricted_access",
            "running": "running_allowed"

        }

        key = mapping.get(behaviour)

        if key is None:

            return True

        return rules.get(key, True)

    ##################################################

    def monitor(self, zone_name, item):

        zone = self.zone_engine.get_zone_by_name(zone_name)

        if zone is None:

            return False

        monitor = zone.get("monitor", {})

        return monitor.get(item, False)