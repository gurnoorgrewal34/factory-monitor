class Orchestrator:

    def __init__(self):

        ##################################################
        # Available Modules
        ##################################################
        self.available_modules = {

            "helmet",
            "phone",
            "fire",
            "smoke",
            "smoking",

            "pose",
            "sleep",
            "fall",

            "group",

            "running",
            "restricted",
            "loitering",
            "idle",
            "activity",

            "after_shift",
            "vehicle",
            "suspicious_theft"
        }
        
        
        
        
        
        ##################################################
        # INTERNAL DEPENDENCIES
        #
        # selected_modules = what USER selected
        #
        # runtime dependencies = internal processing
        # required to make the selected behaviour work.
        #
        # IMPORTANT:
        # These dependencies do NOT automatically enable
        # their user-facing alerts.
        ##################################################

        self.dependencies = {

            # Idle needs:
            # pose_state + wrist movement
            "idle": {
                "pose"
            },

            # Activity is based on pose_state
            "activity": {
                "pose"
            },

            # Current "group" feature runs:
            # GroupBehaviour
            # GroupStandingBehaviour
            # SocialLoiteringBehaviour
            #
            # Group standing/social logic needs pose and
            # hand movement information.
            "group": {
                "pose"
            },
        }

        ##################################################
        # Default
        #
        # Keep ALL as default so the current project
        # continues to behave exactly as before.
        ##################################################

        self.selected_modules = set(
            self.available_modules
        )

    ##################################################
    # ENABLED
    ##################################################

    def enabled(self, module):

        module = module.lower().strip()

        return module in self.selected_modules

    ##################################################
    # ANY ENABLED
    ##################################################

    def any_enabled(self, *modules):

        for module in modules:

            if self.enabled(module):

                return True

        return False

    ##################################################
    # ENABLE ALL
    ##################################################

    def enable_all(self):

        self.selected_modules = set(
            self.available_modules
        )

        print(
            "ORCHESTRATOR -> ALL MODULES ENABLED"
        )

    ##################################################
    # DISABLE ALL
    ##################################################

    def disable_all(self):

        self.selected_modules.clear()

        print(
            "ORCHESTRATOR -> "
            "ALL OPTIONAL MODULES DISABLED"
        )

    ##################################################
    # ENABLE ONE
    ##################################################

    def enable(self, module):

        module = module.lower().strip()

        if module not in self.available_modules:

            print(
                f"ORCHESTRATOR -> "
                f"Unknown module: {module}"
            )

            return False

        self.selected_modules.add(
            module
        )

        print(
            f"ORCHESTRATOR -> "
            f"ENABLED: {module.upper()}"
        )

        return True

    ##################################################
    # DISABLE ONE
    ##################################################

    def disable(self, module):

        module = module.lower().strip()

        if module in self.selected_modules:

            self.selected_modules.remove(
                module
            )

            print(
                f"ORCHESTRATOR -> "
                f"DISABLED: {module.upper()}"
            )

        return True

    ##################################################
    # SET ONLY ONE
    ##################################################

    def only(self, module):

        module = module.lower().strip()

        if module not in self.available_modules:

            print(
                f"ORCHESTRATOR -> "
                f"Unknown module: {module}"
            )

            return False

        self.selected_modules = {
            module
        }

        print(
            "ORCHESTRATOR -> "
            f"ONLY {module.upper()} ENABLED"
        )

        return True

    ##################################################
    # SET MULTIPLE
    ##################################################

    def set_modules(self, modules):

        if isinstance(modules, str):
            modules = [modules]

        normalized = [
            module.lower().strip()
            for module in modules
        ]

        # ================================================
        # SPECIAL MODE: ALL
        # ================================================

        if "all" in normalized:

            self.enable_all()

            return True

        # ================================================
        # SELECTED MODULES
        # ================================================

        selected = set()

        for module in normalized:

            if module not in self.available_modules:

                print(
                    "ORCHESTRATOR -> "
                    f"Unknown module: {module}"
                )

                continue

            selected.add(module)

        self.selected_modules = selected

        print(
            "ORCHESTRATOR -> "
            "SELECTED MODULES:"
        )

        print(
            sorted(
                self.selected_modules
            )
        )

        return True

    ##################################################
    # GET ACTIVE MODULES
    ##################################################

    def active_modules(self):

        return sorted(
            self.selected_modules
        )

    
    
    
    
    
    
    ##################################################
    # GET INTERNAL RUNTIME MODULES
    ##################################################

    def runtime_modules(self):

        required = set(
            self.selected_modules
        )

        changed = True

        while changed:

            changed = False

            for module in list(required):

                dependencies = (
                    self.dependencies.get(
                        module,
                        set()
                    )
                )

                for dependency in dependencies:

                    if dependency not in required:

                        required.add(
                            dependency
                        )

                        changed = True

        return required


    ##################################################
    # RUNTIME ENABLED
    #
    # IMPORTANT:
    # Use this for shared internal processors/models.
    #
    # Do NOT use this for deciding which user alert
    # should be generated.
    ##################################################

    def runtime_enabled(self, module):

        module = (
            module.lower().strip()
        )

        return (
            module
            in
            self.runtime_modules()
        )


    ##################################################
    # ANY RUNTIME ENABLED
    ##################################################

    def any_runtime_enabled(
        self,
        *modules
    ):

        for module in modules:

            if self.runtime_enabled(
                module
            ):

                return True

        return False



    ##################################################
    # DEBUG
    ##################################################

    def debug(self):

        print(
            "========================================"
        )

        print(
            "ORCHESTRATOR STATUS"
        )

        print(
            "Active modules:"
        )

        for module in sorted(
            self.selected_modules
        ):

            print(
                f"  [ON] {module}"
            )

        print(
            "========================================"
        )