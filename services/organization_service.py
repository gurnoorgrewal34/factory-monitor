from fastapi import (
    HTTPException,
)

from database.organization_repository import (
    OrganizationRepository,
)


class OrganizationService:

    def __init__(
        self
    ):

        self.repository = (
            OrganizationRepository()
        )


    # ======================================================
    # COMPANY
    # ======================================================

    def create_company(
        self,
        request
    ):

        try:

            gstin = (
                request.gstin
                .strip()
                .upper()
            )

            existing_company = (
                self.repository
                .get_company_by_gstin(
                    gstin
                )
            )

            if existing_company:

                raise HTTPException(
                    status_code=409,
                    detail=(
                        "A company with this GSTIN "
                        "already exists."
                    )
                )

            company_data = (
                request.model_dump(
                    exclude_none=True
                )
            )

            company_data[
                "gstin"
            ] = gstin

            company = (
                self.repository
                .create_company(
                    company_data
                )
            )

            return self._company_to_dict(
                company
            )

        except HTTPException:
            raise

        except Exception as exc:

            print(
                "CREATE COMPANY ERROR ->",
                repr(exc)
            )

            raise HTTPException(
                status_code=500,
                detail=(
                    "Company registration failed."
                )
            )


    # ======================================================
    # PLANT
    # ======================================================

    def create_plant(
        self,
        request
    ):

        try:

            company = (
                self.repository
                .get_company_by_id(
                    request.company_id
                )
            )

            if not company:

                raise HTTPException(
                    status_code=404,
                    detail="Company not found."
                )

            existing_plant = (
                self.repository
                .get_plant_by_name(
                    request.company_id,
                    request.plant_name.strip()
                )
            )

            if existing_plant:

                raise HTTPException(
                    status_code=409,
                    detail=(
                        "A plant with this name "
                        "already exists in this company."
                    )
                )

            plant_data = (
                request.model_dump()
            )

            plant_data[
                "plant_name"
            ] = (
                request.plant_name
                .strip()
            )

            plant = (
                self.repository
                .create_plant(
                    plant_data
                )
            )

            return self._plant_to_dict(
                plant
            )

        except HTTPException:
            raise

        except Exception as exc:

            print(
                "CREATE PLANT ERROR ->",
                repr(exc)
            )

            raise HTTPException(
                status_code=500,
                detail="Plant registration failed."
            )


    # ======================================================
    # DEPARTMENT
    # ======================================================

    def create_department(
        self,
        request
    ):

        try:

            plant = (
                self.repository
                .get_plant_by_id(
                    request.plant_id
                )
            )

            if not plant:

                raise HTTPException(
                    status_code=404,
                    detail="Plant not found."
                )

            existing_department = (
                self.repository
                .get_department_by_name(
                    request.plant_id,
                    request.department_name.strip()
                )
            )

            if existing_department:

                raise HTTPException(
                    status_code=409,
                    detail=(
                        "A department with this name "
                        "already exists in this plant."
                    )
                )

            department_data = (
                request.model_dump()
            )

            department_data[
                "department_name"
            ] = (
                request.department_name
                .strip()
            )

            department = (
                self.repository
                .create_department(
                    department_data
                )
            )

            return self._department_to_dict(
                department
            )

        except HTTPException:
            raise

        except Exception as exc:

            print(
                "CREATE DEPARTMENT ERROR ->",
                repr(exc)
            )

            raise HTTPException(
                status_code=500,
                detail=(
                    "Department registration failed."
                )
            )


    # ======================================================
    # WORKSTATION
    # ======================================================

    def create_workstation(
        self,
        request
    ):

        try:

            department = (
                self.repository
                .get_department_by_id(
                    request.department_id
                )
            )

            if not department:

                raise HTTPException(
                    status_code=404,
                    detail="Department not found."
                )

            existing_workstation = (
                self.repository
                .get_workstation_by_name(
                    request.department_id,
                    request.workstation_name.strip()
                )
            )

            if existing_workstation:

                raise HTTPException(
                    status_code=409,
                    detail=(
                        "A workstation with this name "
                        "already exists in this department."
                    )
                )

            workstation_data = (
                request.model_dump()
            )

            workstation_data[
                "workstation_name"
            ] = (
                request.workstation_name
                .strip()
            )

            workstation = (
                self.repository
                .create_workstation(
                    workstation_data
                )
            )

            return self._workstation_to_dict(
                workstation
            )

        except HTTPException:
            raise

        except Exception as exc:

            print(
                "CREATE WORKSTATION ERROR ->",
                repr(exc)
            )

            raise HTTPException(
                status_code=500,
                detail=(
                    "Workstation registration failed."
                )
            )



    # ======================================================
    # GET COMPANIES
    # ======================================================

    def get_companies(
        self
    ):

        return (
            self.repository
            .get_companies_with_plant_count()
        )


    # ======================================================
    # GET PLANTS
    # ======================================================

    def get_plants_by_company(
        self,
        company_id
    ):

        company = (
            self.repository
            .get_company_by_id(
                company_id
            )
        )

        if not company:

            raise HTTPException(
                status_code=404,
                detail="Company not found."
            )

        return (
            self.repository
            .get_plants_with_company(
                company_id
            )
        )


    # ======================================================
    # GET DEPARTMENTS
    # ======================================================

    def get_departments_by_plant(
        self,
        plant_id
    ):

        plant = (
            self.repository
            .get_plant_by_id(
                plant_id
            )
        )

        if not plant:

            raise HTTPException(
                status_code=404,
                detail="Plant not found."
            )

        return (
            self.repository
            .get_departments_with_parents(
                plant_id
            )
        )


    # ======================================================
    # GET WORKSTATIONS
    # ======================================================

    def get_workstations_by_department(
        self,
        department_id
    ):

        department = (
            self.repository
            .get_department_by_id(
                department_id
            )
        )

        if not department:

            raise HTTPException(
                status_code=404,
                detail="Department not found."
            )

        return (
            self.repository
            .get_workstations_with_parents(
                department_id
            )
        )


    # ======================================================
    # SAFE RESPONSE HELPERS
    # ======================================================

    @staticmethod
    def _company_to_dict(
        company
    ):

        return {
            "id":
                company.id,

            "company_name":
                company.company_name,

            "gstin":
                company.gstin,

            "industry":
                company.industry,

            "city":
                company.city,

            "state":
                company.state,

            "contact_name":
                company.contact_name,

            "contact_email":
                company.contact_email,

            "contact_phone":
                company.contact_phone,

            "registration_date":
                company.registration_date,
                
            "status": company.status,

            "company_logo":
                company.company_logo,
        }


    @staticmethod
    def _plant_to_dict(
        plant
    ):

        return {
            "id":
                plant.id,

            "company_id":
                plant.company_id,

            "plant_name":
                plant.plant_name,

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
        }


    @staticmethod
    def _department_to_dict(
        department
    ):

        return {
            "id":
                department.id,

            "plant_id":
                department.plant_id,

            "department_name":
                department.department_name,

            "department_head":
                department.department_head,

            "employee_count":
                department.employee_count,

            "status":
                department.status,
        }


    @staticmethod
    def _workstation_to_dict(
        workstation
    ):

        return {
            "id":
                workstation.id,

            "department_id":
                workstation.department_id,

            "workstation_name":
                workstation.workstation_name,

            "workstation_type":
                workstation.workstation_type,

            "operator_name":
                workstation.operator_name,

            "status":
                workstation.status,
        }
        
    
    # ======================================================
    # DELETE COMPANY
    # ======================================================

    def delete_company(
        self,
        company_id
    ):

        company = (
            self.repository
            .get_company_by_id(
                company_id
            )
        )

        if not company:

            raise HTTPException(
                status_code=404,
                detail="Company not found."
            )

        if (
            self.repository
            .has_plants(
                company_id
            )
        ):

            raise HTTPException(
                status_code=409,
                detail=(
                    "Company cannot be deleted because "
                    "it still contains one or more plants. "
                    "Delete the plants first."
                )
            )

        deleted = (
            self.repository
            .delete_company(
                company_id
            )
        )

        if not deleted:

            raise HTTPException(
                status_code=500,
                detail="Company deletion failed."
            )

        return True


    # ======================================================
    # DELETE PLANT
    # ======================================================

    def delete_plant(
        self,
        plant_id
    ):

        plant = (
            self.repository
            .get_plant_by_id(
                plant_id
            )
        )

        if not plant:

            raise HTTPException(
                status_code=404,
                detail="Plant not found."
            )

        if (
            self.repository
            .has_departments(
                plant_id
            )
        ):

            raise HTTPException(
                status_code=409,
                detail=(
                    "Plant cannot be deleted because "
                    "it still contains one or more departments. "
                    "Delete the departments first."
                )
            )

        deleted = (
            self.repository
            .delete_plant(
                plant_id
            )
        )

        if not deleted:

            raise HTTPException(
                status_code=500,
                detail="Plant deletion failed."
            )

        return True


    # ======================================================
    # DELETE DEPARTMENT
    # ======================================================

    def delete_department(
        self,
        department_id
    ):

        department = (
            self.repository
            .get_department_by_id(
                department_id
            )
        )

        if not department:

            raise HTTPException(
                status_code=404,
                detail="Department not found."
            )

        if (
            self.repository
            .has_workstations(
                department_id
            )
        ):

            raise HTTPException(
                status_code=409,
                detail=(
                    "Department cannot be deleted because "
                    "it still contains one or more workstations. "
                    "Delete the workstations first."
                )
            )

        deleted = (
            self.repository
            .delete_department(
                department_id
            )
        )

        if not deleted:

            raise HTTPException(
                status_code=500,
                detail="Department deletion failed."
            )

        return True


    # ======================================================
    # DELETE WORKSTATION
    # ======================================================

    def delete_workstation(
        self,
        workstation_id
    ):

        workstation = (
            self.repository
            .get_workstation_by_id(
                workstation_id
            )
        )

        if not workstation:

            raise HTTPException(
                status_code=404,
                detail="Workstation not found."
            )

        deleted = (
            self.repository
            .delete_workstation(
                workstation_id
            )
        )

        if not deleted:

            raise HTTPException(
                status_code=500,
                detail="Workstation deletion failed."
            )

        return True
    
    
    # ======================================================
    def validate_camera_location(
        self,
        company_id,
        plant_id,
        department_id,
        workstation_id
    ):

        # COMPANY
        company = (
            self.repository
            .get_company_by_id(
                company_id
            )
        )

        if not company:
            raise HTTPException(
                status_code=404,
                detail="Company not found."
            )

        # PLANT
        plant = (
            self.repository
            .get_plant_by_id(
                plant_id
            )
        )

        if not plant:
            raise HTTPException(
                status_code=404,
                detail="Plant not found."
            )

        if plant.company_id != company_id:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Selected plant does not belong "
                    "to the selected company."
                )
            )

        # DEPARTMENT
        department = (
            self.repository
            .get_department_by_id(
                department_id
            )
        )

        if not department:
            raise HTTPException(
                status_code=404,
                detail="Department not found."
            )

        if department.plant_id != plant_id:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Selected department does not belong "
                    "to the selected plant."
                )
            )

        # WORKSTATION
        workstation = (
            self.repository
            .get_workstation_by_id(
                workstation_id
            )
        )

        if not workstation:
            raise HTTPException(
                status_code=404,
                detail="Workstation not found."
            )

        if workstation.department_id != department_id:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Selected workstation does not belong "
                    "to the selected department."
                )
            )

        # ACTIVE STATUS
        if not company.status:
            raise HTTPException(
                status_code=400,
                detail="Selected company is inactive."
            )

        if not plant.status:
            raise HTTPException(
                status_code=400,
                detail="Selected plant is inactive."
            )

        if not department.status:
            raise HTTPException(
                status_code=400,
                detail="Selected department is inactive."
            )

        if not workstation.status:
            raise HTTPException(
                status_code=400,
                detail="Selected workstation is inactive."
            )

        return True
    
    def update_company(
        self,
        company_id,
        request
    ):

        company = (
            self.repository
            .get_company_by_id(
                company_id
            )
        )

        if not company:

            raise HTTPException(
                status_code=404,
                detail="Company not found."
            )

        updates = (
            request.model_dump(
                exclude_unset=True
            )
        )

        if "gstin" in updates:

            gstin = (
                updates["gstin"]
                .strip()
                .upper()
            )

            existing = (
                self.repository
                .get_company_by_gstin(
                    gstin
                )
            )

            if (
                existing
                and
                existing.id != company_id
            ):

                raise HTTPException(
                    status_code=409,
                    detail=(
                        "A company with this GSTIN "
                        "already exists."
                    )
                )

            updates["gstin"] = gstin

        updated = (
            self.repository
            .update_company(
                company_id,
                updates
            )
        )

        if not updated:

            raise HTTPException(
                status_code=500,
                detail="Company update failed."
            )

        return self._company_to_dict(
            updated
        )
        
        
    def update_plant(
        self,
        plant_id,
        request
    ):

        plant = (
            self.repository
            .get_plant_by_id(
                plant_id
            )
        )

        if not plant:

            raise HTTPException(
                status_code=404,
                detail="Plant not found."
            )

        updates = (
            request.model_dump(
                exclude_unset=True
            )
        )

        target_company_id = (
            updates.get(
                "company_id",
                plant.company_id
            )
        )

        company = (
            self.repository
            .get_company_by_id(
                target_company_id
            )
        )

        if not company:

            raise HTTPException(
                status_code=404,
                detail="Company not found."
            )

        if "plant_name" in updates:

            existing = (
                self.repository
                .get_plant_by_name(
                    target_company_id,
                    updates[
                        "plant_name"
                    ].strip()
                )
            )

            if (
                existing
                and
                existing.id != plant_id
            ):

                raise HTTPException(
                    status_code=409,
                    detail=(
                        "A plant with this name "
                        "already exists in this company."
                    )
                )

            updates["plant_name"] = (
                updates[
                    "plant_name"
                ].strip()
            )

        updated = (
            self.repository
            .update_plant(
                plant_id,
                updates
            )
        )

        if not updated:

            raise HTTPException(
                status_code=500,
                detail="Plant update failed."
            )

        return self._plant_to_dict(
            updated
        )
        
        
        
    def update_department(
        self,
        department_id,
        request
    ):

        department = (
            self.repository
            .get_department_by_id(
                department_id
            )
        )

        if not department:

            raise HTTPException(
                status_code=404,
                detail="Department not found."
            )

        updates = (
            request.model_dump(
                exclude_unset=True
            )
        )

        target_plant_id = (
            updates.get(
                "plant_id",
                department.plant_id
            )
        )

        plant = (
            self.repository
            .get_plant_by_id(
                target_plant_id
            )
        )

        if not plant:

            raise HTTPException(
                status_code=404,
                detail="Plant not found."
            )

        if "department_name" in updates:

            existing = (
                self.repository
                .get_department_by_name(
                    target_plant_id,
                    updates[
                        "department_name"
                    ].strip()
                )
            )

            if (
                existing
                and
                existing.id != department_id
            ):

                raise HTTPException(
                    status_code=409,
                    detail=(
                        "A department with this name "
                        "already exists in this plant."
                    )
                )

            updates[
                "department_name"
            ] = (
                updates[
                    "department_name"
                ].strip()
            )

        updated = (
            self.repository
            .update_department(
                department_id,
                updates
            )
        )

        if not updated:

            raise HTTPException(
                status_code=500,
                detail="Department update failed."
            )

        return self._department_to_dict(
            updated
        )
        
    def update_workstation(
        self,
        workstation_id,
        request
    ):

        workstation = (
            self.repository
            .get_workstation_by_id(
                workstation_id
            )
        )

        if not workstation:

            raise HTTPException(
                status_code=404,
                detail="Workstation not found."
            )

        updates = (
            request.model_dump(
                exclude_unset=True
            )
        )

        target_department_id = (
            updates.get(
                "department_id",
                workstation.department_id
            )
        )

        department = (
            self.repository
            .get_department_by_id(
                target_department_id
            )
        )

        if not department:

            raise HTTPException(
                status_code=404,
                detail="Department not found."
            )

        if "workstation_name" in updates:

            existing = (
                self.repository
                .get_workstation_by_name(
                    target_department_id,
                    updates[
                        "workstation_name"
                    ].strip()
                )
            )

            if (
                existing
                and
                existing.id != workstation_id
            ):

                raise HTTPException(
                    status_code=409,
                    detail=(
                        "A workstation with this name "
                        "already exists in this department."
                    )
                )

            updates[
                "workstation_name"
            ] = (
                updates[
                    "workstation_name"
                ].strip()
            )

        updated = (
            self.repository
            .update_workstation(
                workstation_id,
                updates
            )
        )

        if not updated:

            raise HTTPException(
                status_code=500,
                detail="Workstation update failed."
            )

        return self._workstation_to_dict(
            updated
        )
        
    def get_camera_location_details(
        self,
        plant_id=None,
        department_id=None,
        workstation_id=None
    ):

        result = {
            "plant_id": plant_id,
            "plant_name": None,

            "department_id": department_id,
            "department_name": None,

            "workstation_id": workstation_id,
            "workstation_name": None,

            "company_id": None,
            "company_name": None,
        }


        # ==============================================
        # PLANT
        # ==============================================

        if plant_id is not None:

            plant = (
                self.repository
                .get_plant_by_id(
                    plant_id
                )
            )

            if plant:

                result[
                    "plant_name"
                ] = plant.plant_name

                result[
                    "company_id"
                ] = plant.company_id

                company = (
                    self.repository
                    .get_company_by_id(
                        plant.company_id
                    )
                )

                if company:

                    result[
                        "company_name"
                    ] = company.company_name


        # ==============================================
        # DEPARTMENT
        # ==============================================

        if department_id is not None:

            department = (
                self.repository
                .get_department_by_id(
                    department_id
                )
            )

            if department:

                result[
                    "department_name"
                ] = (
                    department
                    .department_name
                )


        # ==============================================
        # WORKSTATION
        # ==============================================

        if workstation_id is not None:

            workstation = (
                self.repository
                .get_workstation_by_id(
                    workstation_id
                )
            )

            if workstation:

                result[
                    "workstation_name"
                ] = (
                    workstation
                    .workstation_name
                )


        return result
    
    
    
    def resolve_camera_location_by_name(
        self,
        company_name: str,
        plant_name: str,
        department_name: str,
        workstation_name: str
    ):

        # ==============================================
        # COMPANY
        # ==============================================

        company = (
            self.repository
            .get_company_by_name(
                company_name.strip()
            )
        )

        if company is None:

            raise HTTPException(
                status_code=404,
                detail="Company not found."
            )


        # ==============================================
        # PLANT
        # ==============================================

        plant = (
            self.repository
            .get_plant_by_name(
                company.id,
                plant_name.strip()
            )
        )

        if plant is None:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Plant not found under "
                    "selected company."
                )
            )


        # ==============================================
        # DEPARTMENT
        # ==============================================

        department = (
            self.repository
            .get_department_by_name(
                plant.id,
                department_name.strip()
            )
        )

        if department is None:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Department not found under "
                    "selected plant."
                )
            )


        # ==============================================
        # WORKSTATION
        # ==============================================

        workstation = (
            self.repository
            .get_workstation_by_name(
                department.id,
                workstation_name.strip()
            )
        )

        if workstation is None:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Workstation not found under "
                    "selected department."
                )
            )


        # ==============================================
        # STATUS VALIDATION
        # ==============================================

        if not company.status:

            raise HTTPException(
                status_code=400,
                detail="Selected company is inactive."
            )

        if not plant.status:

            raise HTTPException(
                status_code=400,
                detail="Selected plant is inactive."
            )

        if not department.status:

            raise HTTPException(
                status_code=400,
                detail="Selected department is inactive."
            )

        if not workstation.status:

            raise HTTPException(
                status_code=400,
                detail="Selected workstation is inactive."
            )


        return {

            "company_id":
                company.id,

            "plant_id":
                plant.id,

            "department_id":
                department.id,

            "workstation_id":
                workstation.id,
        }