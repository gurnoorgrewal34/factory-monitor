class PersonProcessor:

    def __init__(self, memory, zone_engine, behaviour):

        self.memory = memory
        self.zone_engine = zone_engine
        self.behaviour = behaviour

    ##################################################

    def process(self, track_id, box):

        x1, y1, x2, y2 = map(int, box)

        ##################################################
        # Calculate Center
        ##################################################

        cx = int((x1 + x2) / 2)
        cy = int((y1 + y2) / 2)

        center = (cx, cy)

        ##################################################
        # Update Memory
        ##################################################

        self.memory.update(track_id, center, box)

        ##################################################
        # Zone Information
        ##################################################

        zone = self.zone_engine.get_zone(center)

        zone_info = self.zone_engine.get_zone_info(center)

        self.memory.update_zone(track_id, zone)

        ##################################################
        # Get Person
        ##################################################

        person = self.memory.get(track_id)

        draw_box = (x1, y1, x2, y2)

        person["box"] = draw_box

        # Store current zone
        person["zone"] = zone

        ##################################################
        # Store complete zone information
        ##################################################

        person["zone_info"] = zone_info

        if zone_info is not None:

            person["zone_rules"] = zone_info.get("rules", {})

            person["monitor"] = zone_info.get("monitor", {})

        else:

            person["zone_rules"] = {}

            person["monitor"] = {}

        ##################################################
        # Behaviour Processing
        ##################################################

        alerts = self.behaviour.process(person)

        ##################################################

        return person, alerts, draw_box