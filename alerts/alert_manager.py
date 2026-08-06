class AlertManager:

    def __init__(self):

        self.active_alerts = {}

    def should_alert(self, person_id, alert_type):

        key = (person_id, alert_type)

        if key in self.active_alerts:
            return False

        self.active_alerts[key] = True

        return True

    def clear(self, person_id, alert_type):

        key = (person_id, alert_type)

        if key in self.active_alerts:
            del self.active_alerts[key]