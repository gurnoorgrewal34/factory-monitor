from datetime import date
from typing import (
    Literal,
    Optional,
)

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
)


# ==========================================================
# COMPANY
# ==========================================================

class CompanyCreateRequest(BaseModel):

    company_name: str = Field(
        min_length=1,
        max_length=200
    )

    gstin: str = Field(
        min_length=1,
        max_length=20
    )

    industry: str = Field(
        min_length=1,
        max_length=150
    )

    city: str = Field(
        min_length=1,
        max_length=100
    )

    state: str = Field(
        min_length=1,
        max_length=100
    )

    contact_name: str = Field(
        min_length=1,
        max_length=150
    )

    contact_email: EmailStr

    contact_phone: Optional[str] = Field(
        default=None,
        max_length=30
    )
    
    status: bool = True

    registration_date: Optional[date] = None

    company_logo: Optional[str] = None


# ==========================================================
# PLANT
# ==========================================================

class PlantCreateRequest(BaseModel):

    company_id: int = Field(
        gt=0
    )

    plant_name: str = Field(
        min_length=1,
        max_length=200
    )

    plant_type: str = Field(
        min_length=1,
        max_length=100
    )

    area_sq_ft: Optional[float] = Field(
        default=None,
        ge=0
    )

    location: str = Field(
        min_length=1,
        max_length=255
    )

    plant_head: str = Field(
        min_length=1,
        max_length=150
    )

    status: bool = True


# ==========================================================
# DEPARTMENT
# ==========================================================

class DepartmentCreateRequest(BaseModel):

    plant_id: int = Field(
        gt=0
    )

    department_name: str = Field(
        min_length=1,
        max_length=200
    )

    department_head: str = Field(
        min_length=1,
        max_length=150
    )

    employee_count: int = Field(
        default=0,
        ge=0
    )

    status: bool = True


# ==========================================================
# WORKSTATION
# ==========================================================

class WorkstationCreateRequest(BaseModel):

    department_id: int = Field(
        gt=0
    )

    workstation_name: str = Field(
        min_length=1,
        max_length=200
    )

    workstation_type: str = Field(
        min_length=1,
        max_length=100
    )

    operator_name: str = Field(
        min_length=1,
        max_length=150
    )

    status: bool = True
    
    
class CompanyUpdateRequest(BaseModel):
    company_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    gstin: Optional[str] = Field(default=None, min_length=1, max_length=20)
    industry: Optional[str] = Field(default=None, min_length=1, max_length=150)
    city: Optional[str] = Field(default=None, min_length=1, max_length=100)
    state: Optional[str] = Field(default=None, min_length=1, max_length=100)
    contact_name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(default=None, max_length=30)
    status: Optional[bool] = None
    registration_date: Optional[date] = None
    company_logo: Optional[str] = None


class PlantUpdateRequest(BaseModel):
    company_id: Optional[int] = Field(default=None, gt=0)
    plant_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    plant_type: Optional[str] = Field(default=None, min_length=1, max_length=100)
    area_sq_ft: Optional[float] = Field(default=None, ge=0)
    location: Optional[str] = Field(default=None, min_length=1, max_length=255)
    plant_head: Optional[str] = Field(default=None, min_length=1, max_length=150)
    status: Optional[bool] = None


class DepartmentUpdateRequest(BaseModel):
    plant_id: Optional[int] = Field(default=None, gt=0)
    department_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    department_head: Optional[str] = Field(default=None, min_length=1, max_length=150)
    employee_count: Optional[int] = Field(default=None, ge=0)
    status: Optional[bool] = None


class WorkstationUpdateRequest(BaseModel):
    department_id: Optional[int] = Field(default=None, gt=0)
    workstation_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    workstation_type: Optional[str] = Field(default=None, min_length=1, max_length=100)
    operator_name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    status: Optional[bool] = None