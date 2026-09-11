from typing import Optional
from pydantic import BaseModel, Field


class RoleCreateRequest(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100
    )

    display_name: str = Field(
        min_length=1,
        max_length=150
    )

    hierarchy_level: int = Field(
        ge=1
    )

    scope_type: str = Field(
        min_length=1,
        max_length=50
    )

    is_active: bool = True


class RoleUpdateRequest(BaseModel):
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100
    )

    display_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=150
    )

    hierarchy_level: Optional[int] = Field(
        default=None,
        ge=1
    )

    scope_type: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=50
    )

    is_active: Optional[bool] = None