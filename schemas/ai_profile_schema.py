from typing import List, Optional

from pydantic import (
    BaseModel,
    Field,
)


class AIProfileCreateRequest(BaseModel):

    name: str = Field(
        min_length=1,
        max_length=150
    )


    model_path_or_url: Optional[str] = None
    description: Optional[str] = None

    modules: List[str]

    is_active: bool = True


class AIProfileUpdateRequest(BaseModel):

    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=150
    )

    description: Optional[str] = None
    
    model_path_or_url: Optional[str] = None

    modules: Optional[List[str]] = None

    is_active: Optional[bool] = None