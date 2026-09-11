from fastapi import (
    Depends,
    HTTPException,
    status,
)

from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from jose import (
    JWTError,
    jwt,
)

from database.user_repository import (
    UserRepository,
)

from security.jwt_handler import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
)


bearer_scheme = HTTPBearer()

user_repository = UserRepository()


# ==================================================
# GET CURRENT AUTHENTICATED USER
# ==================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme
    )
):

    token = credentials.credentials

    try:

        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[
                JWT_ALGORITHM
            ]
        )

        user_id = payload.get(
            "sub"
        )

        if user_id is None:

            raise HTTPException(
                status_code=
                    status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token."
            )

    except JWTError:

        raise HTTPException(
            status_code=
                status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Invalid or expired authentication token."
            )
        )


    # ==============================================
    # LOAD USER FROM DATABASE
    # ==============================================

    user = (
        user_repository
        .get_by_id(
            int(user_id)
        )
    )


    if user is None:

        raise HTTPException(
            status_code=
                status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists."
        )


    if not user.account_status:

        raise HTTPException(
            status_code=
                status.HTTP_403_FORBIDDEN,
            detail="User account is inactive."
        )


    return user


# ==================================================
# ROLE AUTHORIZATION
# ==================================================

def require_roles(
    *allowed_roles
):

    def role_checker(
        current_user=Depends(
            get_current_user
        )
    ):

        if (
            current_user.role
            not in allowed_roles
        ):

            raise HTTPException(
                status_code=
                    status.HTTP_403_FORBIDDEN,
                detail=(
                    "You do not have permission "
                    "to access this resource."
                )
            )

        return current_user

    return role_checker