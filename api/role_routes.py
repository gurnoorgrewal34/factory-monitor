from fastapi import APIRouter, Depends

from schemas.role_schema import (
    RoleCreateRequest,
    RoleUpdateRequest,
)

from services.role_service import (
    RoleService,
)

from security.auth_dependencies import (
    get_current_user,
)


router = APIRouter(
    prefix="/roles",
    tags=["Roles"]
)

role_service = RoleService()


@router.get("")
def get_roles(
    current_user=Depends(
        get_current_user
    )
):
    roles = (
        role_service
        .get_all_roles()
    )

    return {
        "success": True,
        "message": "Roles retrieved successfully",
        "total": len(roles),
        "roles": roles
    }


@router.get("/{role_id}")
def get_role(
    role_id: int,
    current_user=Depends(
        get_current_user
    )
):
    role = (
        role_service
        .get_role_by_id(role_id)
    )

    return {
        "success": True,
        "message": "Role retrieved successfully",
        "role": role
    }


@router.post(
    "",
    status_code=201
)
def create_role(
    request: RoleCreateRequest,
    current_user=Depends(
        get_current_user
    )
):
    role = (
        role_service
        .create_role(request)
    )

    return {
        "success": True,
        "message": "Role created successfully",
        "role": role
    }


@router.put("/{role_id}")
def update_role(
    role_id: int,
    request: RoleUpdateRequest,
    current_user=Depends(
        get_current_user
    )
):
    role = (
        role_service
        .update_role(
            role_id,
            request
        )
    )

    return {
        "success": True,
        "message": "Role updated successfully",
        "role": role
    }


@router.delete("/{role_id}")
def delete_role(
    role_id: int,
    current_user=Depends(
        get_current_user
    )
):
    role = (
        role_service
        .delete_role(role_id)
    )

    return {
        "success": True,
        "message": "Role deleted successfully",
        "role": role
    }