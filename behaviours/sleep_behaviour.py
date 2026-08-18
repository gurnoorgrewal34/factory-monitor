class SleepBehaviour:

    def __init__(self):
        self.alerted_people = set()

    def process(self, sleep_engine):

        alerts = []

        for tid, track in sleep_engine.tracks.items():

            state = track.smoothed_state

            if state != "SLEEPING":

                self.alerted_people.discard(tid)

                continue

            if track.alerted:

                if tid not in self.alerted_people:

                    alerts.append({

                        "type": "Sleep",

                        "severity": "CRITICAL",

                        "person_id": tid,

                        "persistent": True

                    })

                    self.alerted_people.add(tid)

        return alerts