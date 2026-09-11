from database.database import (
    SessionLocal,
)

from database.models import (
    Company,
    Plant,
    Department,
    Workstation,
)
from sqlalchemy import (
    func,
)

class OrganizationRepository:

    # ======================================================
    # COMPANY
    # ======================================================

    def get_company_by_id(
        self,
        company_id
    ):

        with SessionLocal() as db:

            return (
                db.query(Company)
                .filter(
                    Company.id == company_id
                )
                .first()
            )


    def get_company_by_gstin(
        self,
        gstin
    ):

        with SessionLocal() as db:

            return (
                db.query(Company)
                .filter(
                    Company.gstin == gstin
                )
                .first()
            )


    def create_company(
        self,
        data
    ):

        with SessionLocal() as db:

            company = Company(
                **data
            )

            db.add(
                company
            )

            db.commit()
            db.refresh(
                company
            )

            return company


    def get_all_companies(
        self
    ):

        with SessionLocal() as db:

            return (
                db.query(Company)
                .order_by(
                    Company.company_name.asc()
                )
                .all()
            )


    def get_companies_with_plant_count(self):

        with SessionLocal() as db:

            rows = (
                db.query(
                    Company,
                    func.count(Plant.id).label(
                        "plant_count"
                    )
                )
                .outerjoin(
                    Plant,
                    Plant.company_id == Company.id
                )
                .group_by(
                    Company.id
                )
                .order_by(
                    Company.id.asc()
                )
                .all()
            )

            result = []

            for company, plant_count in rows:

                result.append({
                    "id": company.id,
                    "company_name": company.company_name,
                    "gstin": company.gstin,
                    "industry": company.industry,
                    "city": company.city,
                    "state": company.state,
                    "contact_name": company.contact_name,
                    "contact_email": company.contact_email,
                    "contact_phone": company.contact_phone,
                    "status": company.status,
                    "registration_date": company.registration_date,
                    "company_logo": company.company_logo,

                    "plant_count": plant_count
                })

            return result
        
        
    def get_company_by_name(
        self,
        company_name
    ):

        with SessionLocal() as db:

            return (
                db.query(
                    Company
                )
                .filter(
                    func.lower(
                        Company.company_name
                    )
                    ==
                    company_name
                    .strip()
                    .lower()
                )
                .first()
            )
    
    
    # ======================================================
    # PLANT
    # ======================================================

    def get_plant_by_id(
        self,
        plant_id
    ):

        with SessionLocal() as db:

            return (
                db.query(Plant)
                .filter(
                    Plant.id == plant_id
                )
                .first()
            )


    def get_plant_by_name(
        self,
        company_id,
        plant_name
    ):

        with SessionLocal() as db:

            return (
                db.query(Plant)
                .filter(
                    Plant.company_id
                    == company_id,

                    Plant.plant_name
                    == plant_name
                )
                .first()
            )


    def create_plant(
        self,
        data
    ):

        with SessionLocal() as db:

            plant = Plant(
                **data
            )

            db.add(
                plant
            )

            db.commit()
            db.refresh(
                plant
            )

            return plant


    def get_plants_by_company(
        self,
        company_id
    ):

        with SessionLocal() as db:

            return (
                db.query(Plant)
                .filter(
                    Plant.company_id
                    == company_id
                )
                .order_by(
                    Plant.plant_name.asc()
                )
                .all()
            )


    # ======================================================
    # DEPARTMENT
    # ======================================================

    def get_department_by_id(
        self,
        department_id
    ):

        with SessionLocal() as db:

            return (
                db.query(Department)
                .filter(
                    Department.id
                    == department_id
                )
                .first()
            )


    def get_department_by_name(
        self,
        plant_id,
        department_name
    ):

        with SessionLocal() as db:

            return (
                db.query(Department)
                .filter(
                    Department.plant_id
                    == plant_id,

                    Department.department_name
                    == department_name
                )
                .first()
            )


    def create_department(
        self,
        data
    ):

        with SessionLocal() as db:

            department = Department(
                **data
            )

            db.add(
                department
            )

            db.commit()
            db.refresh(
                department
            )

            return department


    def get_departments_by_plant(
        self,
        plant_id
    ):

        with SessionLocal() as db:

            return (
                db.query(Department)
                .filter(
                    Department.plant_id
                    == plant_id
                )
                .order_by(
                    Department.department_name.asc()
                )
                .all()
            )


    # ======================================================
    # WORKSTATION
    # ======================================================

    def get_workstation_by_name(
        self,
        department_id,
        workstation_name
    ):

        with SessionLocal() as db:

            return (
                db.query(Workstation)
                .filter(
                    Workstation.department_id
                    == department_id,

                    Workstation.workstation_name
                    == workstation_name
                )
                .first()
            )

    def get_workstation_by_id(
        self,
        workstation_id
    ):

        with SessionLocal() as db:

            return (
                db.query(Workstation)
                .filter(
                    Workstation.id == workstation_id
                )
                .first()
            )
    
    
    
    def create_workstation(
        self,
        data
    ):

        with SessionLocal() as db:

            workstation = Workstation(
                **data
            )

            db.add(
                workstation
            )

            db.commit()
            db.refresh(
                workstation
            )

            return workstation


    def get_workstations_by_department(
        self,
        department_id
    ):

        with SessionLocal() as db:

            return (
                db.query(Workstation)
                .filter(
                    Workstation.department_id
                    == department_id
                )
                .order_by(
                    Workstation.workstation_name.asc()
                )
                .all()
            )
            
    # ======================================================
    # CHECK CHILD RECORDS
    # ======================================================

    def has_plants(
        self,
        company_id
    ):

        with SessionLocal() as db:

            return (
                db.query(Plant)
                .filter(
                    Plant.company_id == company_id
                )
                .first()
                is not None
            )


    def has_departments(
        self,
        plant_id
    ):

        with SessionLocal() as db:

            return (
                db.query(Department)
                .filter(
                    Department.plant_id == plant_id
                )
                .first()
                is not None
            )


    def has_workstations(
        self,
        department_id
    ):

        with SessionLocal() as db:

            return (
                db.query(Workstation)
                .filter(
                    Workstation.department_id == department_id
                )
                .first()
                is not None
            )


    # ======================================================
    # DELETE COMPANY
    # ======================================================

    def delete_company(
        self,
        company_id
    ):

        with SessionLocal() as db:

            company = (
                db.query(Company)
                .filter(
                    Company.id == company_id
                )
                .first()
            )

            if not company:
                return False

            db.delete(company)
            db.commit()

            return True


    # ======================================================
    # DELETE PLANT
    # ======================================================

    def delete_plant(
        self,
        plant_id
    ):

        with SessionLocal() as db:

            plant = (
                db.query(Plant)
                .filter(
                    Plant.id == plant_id
                )
                .first()
            )

            if not plant:
                return False

            db.delete(plant)
            db.commit()

            return True


    # ======================================================
    # DELETE DEPARTMENT
    # ======================================================

    def delete_department(
        self,
        department_id
    ):

        with SessionLocal() as db:

            department = (
                db.query(Department)
                .filter(
                    Department.id == department_id
                )
                .first()
            )

            if not department:
                return False

            db.delete(department)
            db.commit()

            return True


    # ======================================================
    # DELETE WORKSTATION
    # ======================================================

    def delete_workstation(
        self,
        workstation_id
    ):

        with SessionLocal() as db:

            workstation = (
                db.query(Workstation)
                .filter(
                    Workstation.id == workstation_id
                )
                .first()
            )

            if not workstation:
                return False

            db.delete(workstation)
            db.commit()

            return True
        
        
        
   
            
    def get_departments_with_parents(
        self,
        plant_id
    ):

        with SessionLocal() as db:

            rows = (
                db.query(
                    Department,

                    Plant.plant_name.label(
                        "plant_name"
                    ),

                    Company.id.label(
                        "company_id"
                    ),

                    Company.company_name.label(
                        "company_name"
                    ),

                    func.count(
                        Workstation.id
                    ).label(
                        "workstation_count"
                    )
                )
                .join(
                    Plant,
                    Department.plant_id == Plant.id
                )
                .join(
                    Company,
                    Plant.company_id == Company.id
                )
                .outerjoin(
                    Workstation,
                    Workstation.department_id
                    == Department.id
                )
                .filter(
                    Department.plant_id == plant_id
                )
                .group_by(
                    Department.id,
                    Plant.id,
                    Plant.plant_name,
                    Company.id,
                    Company.company_name
                )
                .order_by(
                    Department.department_name.asc()
                )
                .all()
            )

            result = []

            for (
                department,
                plant_name,
                company_id,
                company_name,
                workstation_count
            ) in rows:

                result.append({

                    "id":
                        department.id,

                    "plant_id":
                        department.plant_id,

                    "plant_name":
                        plant_name,

                    "company_id":
                        company_id,

                    "company_name":
                        company_name,

                    "department_name":
                        department.department_name,

                    "department_head":
                        department.department_head,

                    "employee_count":
                        department.employee_count,

                    "status":
                        department.status,

                    "workstation_count":
                        workstation_count,
                })

            return result
        
        
    def get_workstations_with_parents(
        self,
        department_id
    ):

        with SessionLocal() as db:

            rows = (
                db.query(
                    Workstation,
                    Department.department_name.label(
                        "department_name"
                    ),
                    Plant.id.label(
                        "plant_id"
                    ),
                    Plant.plant_name.label(
                        "plant_name"
                    ),
                    Company.id.label(
                        "company_id"
                    ),
                    Company.company_name.label(
                        "company_name"
                    )
                )
                .join(
                    Department,
                    Workstation.department_id
                    == Department.id
                )
                .join(
                    Plant,
                    Department.plant_id
                    == Plant.id
                )
                .join(
                    Company,
                    Plant.company_id
                    == Company.id
                )
                .filter(
                    Workstation.department_id
                    == department_id
                )
                .order_by(
                    Workstation.workstation_name.asc()
                )
                .all()
            )

            result = []

            for (
                workstation,
                department_name,
                plant_id,
                plant_name,
                company_id,
                company_name
            ) in rows:

                result.append({
                    "id":
                        workstation.id,

                    "department_id":
                        workstation.department_id,

                    "department_name":
                        department_name,

                    "plant_id":
                        plant_id,

                    "plant_name":
                        plant_name,

                    "company_id":
                        company_id,

                    "company_name":
                        company_name,

                    "workstation_name":
                        workstation.workstation_name,

                    "workstation_type":
                        workstation.workstation_type,

                    "operator_name":
                        workstation.operator_name,

                    "status":
                        workstation.status,
                })

            return result
        
        
    def update_company(
        self,
        company_id,
        updates
    ):

        with SessionLocal() as db:

            company = (
                db.query(Company)
                .filter(
                    Company.id == company_id
                )
                .first()
            )

            if not company:
                return None

            for field, value in updates.items():

                if hasattr(
                    company,
                    field
                ):
                    setattr(
                        company,
                        field,
                        value
                    )

            db.commit()
            db.refresh(company)

            return company
        
        
    def update_plant(
        self,
        plant_id,
        updates
    ):

        with SessionLocal() as db:

            plant = (
                db.query(Plant)
                .filter(
                    Plant.id == plant_id
                )
                .first()
            )

            if not plant:
                return None

            for field, value in updates.items():

                if hasattr(
                    plant,
                    field
                ):
                    setattr(
                        plant,
                        field,
                        value
                    )

            db.commit()
            db.refresh(plant)

            return plant
        
    def update_department(
        self,
        department_id,
        updates
    ):

        with SessionLocal() as db:

            department = (
                db.query(Department)
                .filter(
                    Department.id == department_id
                )
                .first()
            )

            if not department:
                return None

            for field, value in updates.items():

                if hasattr(
                    department,
                    field
                ):
                    setattr(
                        department,
                        field,
                        value
                    )

            db.commit()
            db.refresh(department)

            return department
        
        
    def update_workstation(
        self,
        workstation_id,
        updates
    ):

        with SessionLocal() as db:

            workstation = (
                db.query(Workstation)
                .filter(
                    Workstation.id == workstation_id
                )
                .first()
            )

            if not workstation:
                return None

            for field, value in updates.items():

                if hasattr(
                    workstation,
                    field
                ):
                    setattr(
                        workstation,
                        field,
                        value
                    )

            db.commit()
            db.refresh(workstation)

            return workstation
        
        
    def get_plants_with_company(
        self,
        company_id
    ):

        with SessionLocal() as db:

            rows = (
                db.query(
                    Plant,

                    Company.company_name.label(
                        "company_name"
                    ),

                    func.count(
                        Department.id
                    ).label(
                        "department_count"
                    )
                )
                .join(
                    Company,
                    Plant.company_id == Company.id
                )
                .outerjoin(
                    Department,
                    Department.plant_id == Plant.id
                )
                .filter(
                    Plant.company_id == company_id
                )
                .group_by(
                    Plant.id,
                    Company.id,
                    Company.company_name
                )
                .order_by(
                    Plant.plant_name.asc()
                )
                .all()
            )

            result = []

            for (
                plant,
                company_name,
                department_count
            ) in rows:

                result.append({

                    "id":
                        plant.id,

                    "plant_name":
                        plant.plant_name,

                    "company_id":
                        plant.company_id,

                    "company_name":
                        company_name,

                    "plant_type":
                        plant.plant_type,

                    "area_sq_ft":
                        plant.area_sq_ft,

                    "location":
                        plant.location,

                    "plant_head":
                        plant.plant_head,

                    "status":
                        plant.status,

                    "department_count":
                        department_count,
                })

            return result
                