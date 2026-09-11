from datetime import date

from sqlalchemy import (
    func,
)

from database.database import (
    SessionLocal,
)

from database.models import (
    Company,
    Plant,
    Department,
    Workstation,
    Camera,
)


class DashboardRepository:

    # ======================================================
    # COMPANY COUNTS
    # ======================================================

    def get_company_counts(
        self
    ):

        with SessionLocal() as db:

            total = (
                db.query(
                    func.count(
                        Company.id
                    )
                )
                .scalar()
                or 0
            )

            active = (
                db.query(
                    func.count(
                        Company.id
                    )
                )
                .filter(
                    Company.status.is_(
                        True
                    )
                )
                .scalar()
                or 0
            )

            return {
                "total": total,
                "active": active,
            }


    # ======================================================
    # COMPANIES ADDED THIS MONTH
    # ======================================================

    def get_companies_added_this_month(
        self
    ):

        today = date.today()

        with SessionLocal() as db:

            return (
                db.query(
                    func.count(
                        Company.id
                    )
                )
                .filter(
                    Company.registration_date.isnot(
                        None
                    ),
                    func.extract(
                        "year",
                        Company.registration_date
                    ) == today.year,
                    func.extract(
                        "month",
                        Company.registration_date
                    ) == today.month
                )
                .scalar()
                or 0
            )


    # ======================================================
    # PLANT COUNTS
    # ======================================================

    def get_plant_counts(
        self
    ):

        with SessionLocal() as db:

            total = (
                db.query(
                    func.count(
                        Plant.id
                    )
                )
                .scalar()
                or 0
            )

            active = (
                db.query(
                    func.count(
                        Plant.id
                    )
                )
                .filter(
                    Plant.status.is_(
                        True
                    )
                )
                .scalar()
                or 0
            )

            return {
                "total": total,
                "active": active,
            }


    # ======================================================
    # DEPARTMENT / WORKSTATION COUNTS
    # ======================================================

    def get_organization_counts(
        self
    ):

        with SessionLocal() as db:

            departments = (
                db.query(
                    func.count(
                        Department.id
                    )
                )
                .scalar()
                or 0
            )

            workstations = (
                db.query(
                    func.count(
                        Workstation.id
                    )
                )
                .scalar()
                or 0
            )

            return {
                "departments": departments,
                "workstations": workstations,
            }


    # ======================================================
    # TOTAL CAMERAS
    # ======================================================

    def get_total_camera_count(
        self
    ):

        with SessionLocal() as db:

            return (
                db.query(
                    func.count(
                        Camera.db_id
                    )
                )
                .scalar()
                or 0
            )


    # ======================================================
    # REGISTERED COMPANIES
    # ======================================================

    def get_registered_companies(
        self
    ):

        with SessionLocal() as db:

            rows = (
                db.query(
                    Company,
                    func.count(
                        func.distinct(
                            Plant.id
                        )
                    ).label(
                        "plant_count"
                    ),
                    func.count(
                        func.distinct(
                            Camera.db_id
                        )
                    ).label(
                        "camera_count"
                    ),
                )
                .outerjoin(
                    Plant,
                    Plant.company_id
                    == Company.id
                )
                .outerjoin(
                    Camera,
                    Camera.plant_id
                    == Plant.id
                )
                .group_by(
                    Company.id
                )
                .order_by(
                    Company.company_name.asc()
                )
                .all()
            )

            result = []

            for (
                company,
                plant_count,
                camera_count
            ) in rows:

                result.append({
                    "id":
                        company.id,

                    "company_name":
                        company.company_name,

                    "industry":
                        company.industry,

                    "city":
                        company.city,

                    "state":
                        company.state,

                    "status":
                        company.status,

                    "plant_count":
                        plant_count,

                    "camera_count":
                        camera_count,
                })

            return result