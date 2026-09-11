from fastapi import (
    APIRouter,
    Depends,
    Request,
)

from security.auth_dependencies import (
    get_current_user,
)

from services.dashboard_service import (
    DashboardService,
)


router = APIRouter(
    prefix="/dashboard",
    tags=[
        "Dashboard"
    ],
)


# ==========================================================
# DASHBOARD OVERVIEW
# ==========================================================

@router.get(
    "/overview"
)
def get_dashboard_overview(
    request: Request,
    current_user=Depends(
        get_current_user
    )
):

    camera_manager = (
        request.app.state.camera_manager
    )

    dashboard_service = (
        DashboardService(
            camera_manager=
                camera_manager
        )
    )

    data = (
        dashboard_service
        .get_dashboard_overview()
    )

    return {
        "success": True,
        "data": data,
    }