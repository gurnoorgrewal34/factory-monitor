from database.dashboard_repository import (
    DashboardRepository,
)


class DashboardService:

    def __init__(
        self,
        camera_manager
    ):

        self.repository = (
            DashboardRepository()
        )

        self.camera_manager = (
            camera_manager
        )


    # ======================================================
    # PERCENTAGE
    # ======================================================

    @staticmethod
    def _percentage(
        count,
        total
    ):

        if total == 0:
            return 0.0

        return round(
            (
                count
                /
                total
            )
            * 100,
            2
        )


    # ======================================================
    # GET RUNTIME CAMERAS
    # ======================================================

    def _get_runtime_cameras(
        self
    ):

        manager = (
            self.camera_manager
        )


        # ------------------------------------------
        # Supports manager.cameras dictionary/list
        # ------------------------------------------

        if hasattr(
            manager,
            "cameras"
        ):

            cameras = (
                manager.cameras
            )

            if isinstance(
                cameras,
                dict
            ):

                return list(
                    cameras.values()
                )

            if isinstance(
                cameras,
                list
            ):

                return cameras


        # ------------------------------------------
        # Supports get_all_cameras()
        # ------------------------------------------

        if hasattr(
            manager,
            "get_all_cameras"
        ):

            cameras = (
                manager
                .get_all_cameras()
            )

            if isinstance(
                cameras,
                dict
            ):

                return list(
                    cameras.values()
                )

            return list(
                cameras
                or []
            )


        return []


    # ======================================================
    # CAMERA RUNTIME SUMMARY
    #
    # STATUS RULES:
    #
    # config status = inactive
    #     -> inactive
    #
    # config status = active
    # running = True
    # no error
    #     -> active
    #
    # config status = active
    # running = False
    # no error
    #     -> standby
    #
    # any runtime error
    #     -> inactive
    # ======================================================

    def _get_camera_runtime_summary(
        self
    ):

        active = 0
        standby = 0
        inactive = 0

        modules_running = 0

        runtime_cameras = (
            self._get_runtime_cameras()
        )


        for camera in runtime_cameras:

            try:

                # ======================================
                # RUNTIME STATUS
                # ======================================

                runtime_status = (
                    camera.get_status()
                )


                running = (
                    runtime_status.get(
                        "running",
                        False
                    )
                )


                last_error = (
                    runtime_status.get(
                        "last_error"
                    )
                )


                modules = (
                    runtime_status.get(
                        "modules",
                        []
                    )
                    or []
                )


                # ======================================
                # CONFIGURED STATUS
                #
                # Frontend / DB controlled:
                #
                # active
                # inactive
                # ======================================

                configured_status = (
                    str(
                        camera.config.get(
                            "status",
                            "inactive"
                        )
                    )
                    .strip()
                    .lower()
                )


                # ======================================
                # INACTIVE
                #
                # Explicit configured state has
                # highest priority.
                # ======================================

                if (
                    configured_status
                    ==
                    "inactive"
                ):

                    inactive += 1

                    continue


                # ======================================
                # ACTIVE
                #
                # Camera is configured active
                # and runtime is successfully running.
                # ======================================

                if (
                    configured_status
                    ==
                    "active"
                    and
                    running
                    and
                    not last_error
                ):

                    active += 1


                    # ----------------------------------
                    # Count modules only when camera
                    # is actually processing.
                    # ----------------------------------

                    if "all" in modules:

                        # Existing architecture keeps
                        # "all" as one module selection.
                        #
                        # We intentionally do not expand
                        # it here so existing behavior
                        # is not disturbed.

                        modules_running += 1

                    else:

                        modules_running += len(
                            modules
                        )

                    continue


                # ======================================
                # STANDBY
                #
                # Camera is configured active,
                # but runtime has not been started.
                # ======================================

                if (
                    configured_status
                    ==
                    "active"
                    and
                    not running
                    and
                    not last_error
                ):

                    standby += 1

                    continue


                # ======================================
                # ERROR / UNKNOWN STATE
                #
                # Treat runtime failures safely
                # as inactive.
                # ======================================

                inactive += 1


            except Exception as exc:

                print(
                    "DASHBOARD CAMERA STATUS ERROR ->",
                    repr(exc)
                )

                inactive += 1


        return {

            "active":
                active,

            "standby":
                standby,

            "inactive":
                inactive,

            "modules_running":
                modules_running,

            "runtime_camera_count":
                len(
                    runtime_cameras
                ),
        }


    # ======================================================
    # DASHBOARD OVERVIEW
    # ======================================================

    def get_dashboard_overview(
        self
    ):

        # ==================================================
        # COMPANIES
        # ==================================================

        companies = (
            self.repository
            .get_company_counts()
        )


        companies[
            "added_this_month"
        ] = (
            self.repository
            .get_companies_added_this_month()
        )


        # ==================================================
        # PLANTS
        # ==================================================

        plants = (
            self.repository
            .get_plant_counts()
        )


        # ==================================================
        # ORGANIZATION
        # ==================================================

        organization = (
            self.repository
            .get_organization_counts()
        )


        # ==================================================
        # TOTAL REGISTERED CAMERAS
        # ==================================================

        total_cameras = (
            self.repository
            .get_total_camera_count()
        )


        # ==================================================
        # RUNTIME CAMERA SUMMARY
        # ==================================================

        runtime = (
            self._get_camera_runtime_summary()
        )


        active = (
            runtime[
                "active"
            ]
        )


        standby = (
            runtime[
                "standby"
            ]
        )


        inactive = (
            runtime[
                "inactive"
            ]
        )


        # ==================================================
        # CAMERAS PRESENT IN DB BUT NOT LOADED IN RUNTIME
        #
        # These cannot currently process or stream.
        # Treat them as inactive.
        # ==================================================

        runtime_count = (
            runtime[
                "runtime_camera_count"
            ]
        )


        missing_runtime_cameras = max(
            total_cameras
            -
            runtime_count,
            0
        )


        inactive += (
            missing_runtime_cameras
        )


        # ==================================================
        # REGISTERED COMPANIES
        # ==================================================

        registered_companies = (
            self.repository
            .get_registered_companies()
        )


        # ==================================================
        # FINAL RESPONSE
        # ==================================================

        return {

            # ==============================================
            # COMPANIES
            # ==============================================

            "companies": {

                "total":
                    companies[
                        "total"
                    ],

                "active":
                    companies[
                        "active"
                    ],

                "added_this_month":
                    companies[
                        "added_this_month"
                    ],
            },


            # ==============================================
            # PLANTS
            # ==============================================

            "plants": {

                "total":
                    plants[
                        "total"
                    ],

                "active":
                    plants[
                        "active"
                    ],
            },


            # ==============================================
            # ORGANIZATION
            # ==============================================

            "organization": {

                "departments":
                    organization[
                        "departments"
                    ],

                "workstations":
                    organization[
                        "workstations"
                    ],
            },


            # ==============================================
            # CAMERAS
            #
            # NEW STANDARD:
            #
            # active
            # standby
            # inactive
            # ==============================================

            "cameras": {

                "total":
                    total_cameras,

                "active":
                    active,

                "standby":
                    standby,

                "inactive":
                    inactive,
            },


            # ==============================================
            # AI
            # ==============================================

            "ai": {

                "modules_running":
                    runtime[
                        "modules_running"
                    ],
            },


            # ==============================================
            # CAMERA HEALTH
            # ==============================================

            "camera_health": {

                "active": {

                    "count":
                        active,

                    "percentage":
                        self._percentage(
                            active,
                            total_cameras
                        ),
                },


                "standby": {

                    "count":
                        standby,

                    "percentage":
                        self._percentage(
                            standby,
                            total_cameras
                        ),
                },


                "inactive": {

                    "count":
                        inactive,

                    "percentage":
                        self._percentage(
                            inactive,
                            total_cameras
                        ),
                },
            },


            # ==============================================
            # REGISTERED COMPANIES
            # ==============================================

            "registered_companies":
                registered_companies,
        }