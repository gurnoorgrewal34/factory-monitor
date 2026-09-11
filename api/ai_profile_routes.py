from fastapi import (
    APIRouter,
    Depends,
)

from schemas.ai_profile_schema import (
    AIProfileCreateRequest,
    AIProfileUpdateRequest,
)

from services.ai_profile_service import (
    AIProfileService,
)

from security.auth_dependencies import (
    get_current_user,
)


router = APIRouter(
    prefix="/ai-profiles",
    tags=["AI Profiles"]
)

service = (
    AIProfileService()
)


@router.get("")
def get_ai_profiles(
    current_user=Depends(
        get_current_user
    )
):

    profiles = (
        service
        .get_all_profiles()
    )

    return {
        "success": True,
        "message":
            "AI profiles retrieved successfully",
        "total":
            len(profiles),
        "profiles":
            profiles
    }


@router.get(
    "/{profile_id}"
)
def get_ai_profile(
    profile_id: int,
    current_user=Depends(
        get_current_user
    )
):

    profile = (
        service
        .get_profile(
            profile_id
        )
    )

    return {
        "success": True,
        "message":
            "AI profile retrieved successfully",
        "profile":
            profile
    }


@router.post(
    "",
    status_code=201
)
def create_ai_profile(
    request: AIProfileCreateRequest,
    current_user=Depends(
        get_current_user
    )
):

    profile = (
        service
        .create_profile(
            request
        )
    )

    return {
        "success": True,
        "message":
            "AI profile created successfully",
        "profile":
            profile
    }


@router.put(
    "/{profile_id}"
)
def update_ai_profile(
    profile_id: int,
    request: AIProfileUpdateRequest,
    current_user=Depends(
        get_current_user
    )
):

    profile = (
        service
        .update_profile(
            profile_id,
            request
        )
    )

    return {
        "success": True,
        "message":
            "AI profile updated successfully",
        "profile":
            profile
    }


@router.delete(
    "/{profile_id}"
)
def delete_ai_profile(
    profile_id: int,
    current_user=Depends(
        get_current_user
    )
):

    profile = (
        service
        .delete_profile(
            profile_id
        )
    )

    return {
        "success": True,
        "message":
            "AI profile deleted successfully",
        "profile":
            profile
    }