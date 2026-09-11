from fastapi import (
    APIRouter,
    Depends,
    status,
)

from schemas.organization_schema import (
    CompanyCreateRequest,
    CompanyUpdateRequest,

    PlantCreateRequest,
    PlantUpdateRequest,

    DepartmentCreateRequest,
    DepartmentUpdateRequest,

    WorkstationCreateRequest,
    WorkstationUpdateRequest,
)

from services.organization_service import (
    OrganizationService,
)

from security.auth_dependencies import (
    get_current_user,
)




router = APIRouter(
    tags=[
        "Organization Management"
    ]
)


organization_service = (
    OrganizationService()
)


# ==========================================================
# CREATE COMPANY
# Any authenticated active user can create
# ==========================================================

@router.post(
    "/companies",
    status_code=status.HTTP_201_CREATED
)
def create_company(
    request: CompanyCreateRequest,

    current_user=Depends(
        get_current_user
    )
):

    company = (
        organization_service
        .create_company(
            request
        )
    )

    return {
        "success": True,
        "message": (
            "Company registered successfully."
        ),
        "company": company
    }


# ==========================================================
# CREATE PLANT
# Any authenticated active user can create
# ==========================================================

@router.post(
    "/plants",
    status_code=status.HTTP_201_CREATED
)
def create_plant(
    request: PlantCreateRequest,

    current_user=Depends(
        get_current_user
    )
):

    plant = (
        organization_service
        .create_plant(
            request
        )
    )

    return {
        "success": True,
        "message": (
            "Plant registered successfully."
        ),
        "plant": plant
    }


# ==========================================================
# CREATE DEPARTMENT
# Any authenticated active user can create
# ==========================================================

@router.post(
    "/departments",
    status_code=status.HTTP_201_CREATED
)
def create_department(
    request: DepartmentCreateRequest,

    current_user=Depends(
        get_current_user
    )
):

    department = (
        organization_service
        .create_department(
            request
        )
    )

    return {
        "success": True,
        "message": (
            "Department registered successfully."
        ),
        "department": department
    }


# ==========================================================
# CREATE WORKSTATION
# Any authenticated active user can create
# ==========================================================

@router.post(
    "/workstations",
    status_code=status.HTTP_201_CREATED
)
def create_workstation(
    request: WorkstationCreateRequest,

    current_user=Depends(
        get_current_user
    )
):

    workstation = (
        organization_service
        .create_workstation(
            request
        )
    )

    return {
        "success": True,
        "message": (
            "Workstation registered successfully."
        ),
        "workstation": workstation
    }


# ==========================================================
# GET ALL COMPANIES
# Any authenticated active user can view
# ==========================================================

@router.get(
    "/companies"
)
def get_companies(
    current_user=Depends(
        get_current_user
    )
):

    companies = (
        organization_service
        .get_companies()
    )

    return {
        "success": True,
        "total": len(companies),
        "companies": companies
    }


# ==========================================================
# GET PLANTS OF COMPANY
# Any authenticated active user can view
# ==========================================================

@router.get(
    "/companies/{company_id}/plants"
)
def get_company_plants(
    company_id: int,

    current_user=Depends(
        get_current_user
    )
):

    plants = (
        organization_service
        .get_plants_by_company(
            company_id
        )
    )

    return {
        "success": True,
        "total": len(plants),
        "plants": plants
    }


# ==========================================================
# GET DEPARTMENTS OF PLANT
# Any authenticated active user can view
# ==========================================================

@router.get(
    "/plants/{plant_id}/departments"
)
def get_plant_departments(
    plant_id: int,

    current_user=Depends(
        get_current_user
    )
):

    departments = (
        organization_service
        .get_departments_by_plant(
            plant_id
        )
    )

    return {
        "success": True,
        "total": len(departments),
        "departments": departments
    }


# ==========================================================
# GET WORKSTATIONS OF DEPARTMENT
# Any authenticated active user can view
# ==========================================================

@router.get(
    "/departments/{department_id}/workstations"
)
def get_department_workstations(
    department_id: int,

    current_user=Depends(
        get_current_user
    )
):

    workstations = (
        organization_service
        .get_workstations_by_department(
            department_id
        )
    )

    return {
        "success": True,
        "total": len(workstations),
        "workstations": workstations
    }
    
    
 # ==========================================================
# DELETE COMPANY
# ==========================================================

@router.delete(
    "/companies/{company_id}"
)
def delete_company(
    company_id: int,

    current_user=Depends(
        get_current_user
    )
):

    organization_service.delete_company(
        company_id
    )

    return {
        "success": True,
        "message":
            "Company deleted successfully."
    }
    
    
    
# ==========================================================
# DELETE PLANT
# ==========================================================

@router.delete(
    "/plants/{plant_id}"
)
def delete_plant(
    plant_id: int,

    current_user=Depends(
        get_current_user
    )
):

    organization_service.delete_plant(
        plant_id
    )

    return {
        "success": True,
        "message":
            "Plant deleted successfully."
    }
    
    
    
# ==========================================================
# DELETE DEPARTMENT
# ==========================================================

@router.delete(
    "/departments/{department_id}"
)
def delete_department(
    department_id: int,

    current_user=Depends(
        get_current_user
    )
):

    organization_service.delete_department(
        department_id
    )

    return {
        "success": True,
        "message":
            "Department deleted successfully."
    }
    
    
    
# ==========================================================
# DELETE WORKSTATION
# ==========================================================

@router.delete(
    "/workstations/{workstation_id}"
)
def delete_workstation(
    workstation_id: int,

    current_user=Depends(
        get_current_user
    )
):

    organization_service.delete_workstation(
        workstation_id
    )

    return {
        "success": True,
        "message":
            "Workstation deleted successfully."
    }


# update company   
@router.put(
    "/companies/{company_id}"
)
def update_company(
    company_id: int,
    request: CompanyUpdateRequest,
    current_user=Depends(
        get_current_user
    )
):

    company = (
        organization_service
        .update_company(
            company_id,
            request
        )
    )

    return {
        "success": True,
        "message": (
            "Company updated successfully"
        ),
        "company": company
    }
    
    
# ==========================================================
# UPDATE PLANT
# ==========================================================

@router.put(
    "/plants/{plant_id}"
)
def update_plant(
    plant_id: int,
    request: PlantUpdateRequest,
    current_user=Depends(
        get_current_user
    )
):

    plant = (
        organization_service
        .update_plant(
            plant_id,
            request
        )
    )

    return {
        "success": True,
        "message": (
            "Plant updated successfully"
        ),
        "plant": plant
    }
    
    
@router.put(
    "/departments/{department_id}"
)
def update_department(
    department_id: int,
    request: DepartmentUpdateRequest,
    current_user=Depends(
        get_current_user
    )
):

    department = (
        organization_service
        .update_department(
            department_id,
            request
        )
    )

    return {
        "success": True,
        "message": (
            "Department updated successfully"
        ),
        "department": department
    }
    
    
@router.put(
    "/workstations/{workstation_id}"
)
def update_workstation(
    workstation_id: int,
    request: WorkstationUpdateRequest,
    current_user=Depends(
        get_current_user
    )
):

    workstation = (
        organization_service
        .update_workstation(
            workstation_id,
            request
        )
    )

    return {
        "success": True,
        "message": (
            "Workstation updated successfully"
        ),
        "workstation": workstation
    }