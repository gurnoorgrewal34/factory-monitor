from fastapi import (
    APIRouter,
    Depends,
    status,
)

from schemas.user_schema import (
    UserCreateRequest,
    UserUpdateRequest,
)

from services.user_service import (
    UserService,
)

from security.auth_dependencies import (
    get_current_user,
)

from typing import Optional


# ==================================================
# ROUTER
# ==================================================

router = APIRouter(
    prefix="/users",
    tags=[
        "Users"
    ]
)


# ==================================================
# SERVICE
# ==================================================

user_service = (
    UserService()
)


# ==================================================
# REGISTER USER
# ==================================================

@router.post(
    "",
    status_code=
        status.HTTP_201_CREATED
)
def register_user(
    request: UserCreateRequest
):

    user = (
        user_service
        .create_user(
            request
        )
    )

    return {

        "success":
            True,

        "message":
            "User registered successfully",

        "user":
            user
    }


# ==================================================
# GET USERS
# Supports role/location/search filters
# ==================================================


@router.get("")
def get_all_users(

    role: Optional[str] = None,

    company: Optional[str] = None,

    plant: Optional[str] = None,

    department: Optional[str] = None,

    workstation: Optional[str] = None,

    search: Optional[str] = None,

    current_user=Depends(
        get_current_user
    )
):

    result = (
        user_service
        .get_all_users(
            current_user=current_user,
            role=role,
            company=company,
            plant=plant,
            department=department,
            workstation=workstation,
            search=search,
        )
    )

    users = result["users"]

    super_admins = [
        user
        for user in users
        if user.get("role") == "super_admin"
    ]

    plant_admins = [
        user
        for user in users
        if user.get("role") == "plant_admin"
    ]

    department_heads = [
        user
        for user in users
        if user.get("role") == "department_head"
    ]

    supervisors = [
        user
        for user in users
        if user.get("role") == "supervisor"
    ]

    return {

        "success":
            True,

        "message":
            "Users retrieved successfully",

        "summary":
            result["summary"],

        "users":
            users,

        "super_admins":
            super_admins,

        "plant_admins":
            plant_admins,

        "department_heads":
            department_heads,

        "supervisors":
            supervisors,
    }


# ==================================================
# UPDATE USER
# ==================================================

@router.patch(
    "/{user_id}"
)
def update_user(
    user_id: int,
    request: UserUpdateRequest,
    current_user=Depends(
        get_current_user
    )
):

    user = (
        user_service
        .update_user(
            user_id,
            request,
            current_user
        )
    )

    return {

        "success":
            True,

        "message":
            "User updated successfully",

        "user":
            user
    }


# ==================================================
# DELETE USER
# ==================================================

@router.delete(
    "/{user_id}"
)
def delete_user(
    user_id: int,
    current_user=Depends(
        get_current_user
    )
):

    user = (
        user_service
        .delete_user(
            user_id,
            current_user
        )
    )

    return {

        "success":
            True,

        "message":
            "User deleted successfully",

        "user":
            user
    }