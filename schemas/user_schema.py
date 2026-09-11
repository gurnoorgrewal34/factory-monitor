from typing import (

    Optional,
)

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
)


class UserCreateRequest(BaseModel):

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128
    )

    # role: Literal[
    #     "super_admin",
    #     "plant_admin",
    #     "department_head",
    #     "supervisor",
    # ]
    
    role: str = Field(
        min_length=1,
        max_length=100
    )

    full_name: str = Field(
        min_length=1,
        max_length=100
    )

    job_title: Optional[str] = None

    phone_number: Optional[str] = None

    image_url: Optional[str] = None

    account_status: bool = False

    company: Optional[str] = None

    plant: Optional[str] = None

    department: Optional[str] = None

    workstation: Optional[str] = None
    
    
    
class UserUpdateRequest(BaseModel):

    email: Optional[EmailStr] = None

    role: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100
    )

    full_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100
    )

    job_title: Optional[str] = None

    phone_number: Optional[str] = None

    image_url: Optional[str] = None

    account_status: Optional[bool] = None

    company: Optional[str] = None

    plant: Optional[str] = None

    department: Optional[str] = None

    workstation: Optional[str] = None