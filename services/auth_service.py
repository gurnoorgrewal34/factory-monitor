from fastapi import (
    HTTPException,
)

from database.user_repository import (
    UserRepository,
)

from security.password import (
    verify_password,
)

from security.jwt_handler import (
    create_access_token,
)

from database.role_repository import (
    RoleRepository,
)

class AuthService:

    def __init__(self):

        self.repository = (
            UserRepository()
        )

        self.role_repository = (
            RoleRepository()
        )


    def login(
        self,
        request
    ):

        email = (
            str(
                request.email
            )
            .strip()
            .lower()
        )


        # ==========================================
        # FIND USER
        # ==========================================

        user = (
            self.repository
            .get_by_email(
                email
            )
        )


        if user is None:

            raise HTTPException(
                status_code=401,
                detail=(
                    "Invalid email or password."
                )
            )


        # ==========================================
        # VERIFY PASSWORD
        # ==========================================

        password_valid = (
            verify_password(

                request.password,

                user.password
            )
        )


        if not password_valid:

            raise HTTPException(
                status_code=401,
                detail=(
                    "Invalid email or password."
                )
            )


        # ==========================================
        # CHECK ACCOUNT STATUS
        # ==========================================

        if not user.account_status:

            raise HTTPException(
                status_code=403,
                detail=(
                    "Your account is inactive."
                )
            )

        # ==========================================
        # VALIDATE SYSTEM ROLE
        # ==========================================

        role = (
            user.role
            .strip()
            .lower()
        )


        role_record = (
            self.role_repository
            .get_by_name(
                role
            )
        )

        if role_record is None:

            raise HTTPException(
                status_code=403,
                detail=(
                    "User does not have a valid "
                    "system role."
                )
            )

        if not role_record.is_active:

            raise HTTPException(
                status_code=403,
                detail=(
                    "Your assigned role is inactive."
                )
            )
            
        # ==========================================
        # GENERATE ACCESS TOKEN
        # ==========================================

        access_token = (
            create_access_token(

                user_id=
                    user.id,

                email=
                    user.email,

                role=
                    role
            )
        )


        # ==========================================
        # RESPONSE
        # ==========================================

        return {

            "access_token":
                access_token,

            "token_type":
                "bearer",

            "user": {

                "id":
                    user.id,

                "email":
                    user.email,

                "full_name":
                    user.full_name,

                "role":
                    role,

                "company":
                    user.company,

                "plant":
                    user.plant,

                "department":
                    user.department,

                "workstation":
                    user.workstation
            }
        }