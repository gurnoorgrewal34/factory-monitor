from fastapi import (
    APIRouter,
)

from schemas.auth_schema import (
    LoginRequest,
)

from services.auth_service import (
    AuthService,
)

from fastapi import (
    APIRouter,
    Depends,
)

from security.auth_dependencies import (
    get_current_user,
)


router = APIRouter(

    prefix="/auth",

    tags=[
        "Authentication"
    ]
)


auth_service = (
    AuthService()
)


# ==================================================
# LOGIN
# ==================================================

@router.post(
    "/login"
)
def login(
    request: LoginRequest
):

    result = (
        auth_service
        .login(
            request
        )
    )

    return {

        "success":
            True,

        "message":
            "Login successful",

        **result
    }
    
    
# ==================================================
# CURRENT USER
# ==================================================

@router.get(
    "/me"
)
def get_me(
    current_user=Depends(
        get_current_user
    )
):

    return {

        "success":
            True,

        "user": {

            "id":
                current_user.id,

            "email":
                current_user.email,

            "full_name":
                current_user.full_name,

            "role":
                current_user.role,

            "company":
                current_user.company,

            "plant":
                current_user.plant,

            "department":
                current_user.department,

            "workstation":
                current_user.workstation,
        }
    }