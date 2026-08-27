class ZonePolicy:

    def __init__(
        self,
        zone_engine
    ):

        self.zone_engine = (
            zone_engine
        )

    ##################################################
    # GET ZONE INFO
    ##################################################

    def get_zone(
        self,
        zone_name
    ):

        if (
            not zone_name
            or
            zone_name == "Unknown"
        ):

            return None

        return (
            self.zone_engine
            .get_zone_by_name(
                zone_name
            )
        )

    ##################################################
    # RESTRICTED ZONE
    ##################################################

    def is_restricted(
            self,
            zone_name
        ):

            zone = (
                self.zone_engine
                .get_zone_by_name(
                    zone_name
                )
            )

            if zone is None:
                return False

            return (
                str(
                    zone.get(
                        "zone_type",
                        "normal"
                    )
                )
                .lower()
                .strip()
                ==
                "restricted"
            )

    ##################################################
    # BACKWARD-COMPATIBLE ALLOWS
    #
    # Normal AI modules are no longer controlled
    # by zone rules.
    ##################################################

    def allows(
        self,
        zone_name,
        behaviour
    ):

        if behaviour == "restricted":

            return self.is_restricted(
                zone_name
            )

        return True

    ##################################################
    # BACKWARD-COMPATIBLE MONITOR
    #
    # AI module selection is controlled by
    # Orchestrator, not zone monitor dictionaries.
    ##################################################

    def monitor(
        self,
        zone_name,
        item
    ):

        return True