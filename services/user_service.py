from fastapi import (
    HTTPException,
)

from database.user_repository import (
    UserRepository,
)

from security.password import (
    hash_password,
)

from database.role_repository import (
    RoleRepository,
)

class UserService:

    def __init__(self):

        self.repository = (
            UserRepository()
        )

        self.role_repository = (
            RoleRepository()
        )


    def create_user(
        self,
        request
    ):

        try:

            # ==========================================
            # NORMALIZE EMAIL
            # ==========================================

            email = (
                str(
                    request.email
                )
                .strip()
                .lower()
            )


            
            # ==========================================
            # VALIDATE DYNAMIC ROLE
            # ==========================================

            role_name = (
                request.role
                .strip()
                .lower()
                .replace(" ", "_")
            )

            role = (
                self.role_repository
                .get_by_name(
                    role_name
                )
            )

            if role is None:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Role '{role_name}' "
                        "does not exist."
                    )
                )

            if not role.is_active:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Role '{role_name}' "
                        "is inactive."
                    )
                )
            
            # ==========================================
            # CHECK DUPLICATE EMAIL
            # ==========================================

            existing_user = (
                self.repository
                .get_by_email(
                    email
                )
            )

            if existing_user:

                raise HTTPException(
                    status_code=409,
                    detail=(
                        "A user with this email "
                        "already exists."
                    )
                )


            # ==========================================
            # CHECK DUPLICATE PHONE NUMBER
            # ==========================================

            if request.phone_number:

                existing_phone = (
                    self.repository
                    .get_by_phone_number(
                        request.phone_number
                    )
                )

                if existing_phone:

                    raise HTTPException(
                        status_code=409,
                        detail=(
                            "A user with this phone "
                            "number already exists."
                        )
                    )


            # ==========================================
            # REQUEST -> DICTIONARY
            # ==========================================

            user_data = (
                request.model_dump()
            )
            
            
            user_data["role"] = role.name
            
            user_data["role_id"] = role.id


            # ==========================================
            # NORMALIZED EMAIL
            # ==========================================

            user_data[
                "email"
            ] = email


            # ==========================================
            # HASH PASSWORD
            # ==========================================

            user_data[
                "password"
            ] = hash_password(
                request.password
            )


            # ==========================================
            # CREATE USER
            # ==========================================

            user = (
                self.repository
                .create(
                    user_data
                )
            )

            return user


        # ==============================================
        # EXPECTED API ERRORS
        # ==============================================

        except HTTPException:

            raise


        # ==============================================
        # UNEXPECTED ERROR
        # ==============================================

        except Exception as exc:

            print(
                "USER REGISTRATION ERROR ->",
                repr(exc)
            )

            raise HTTPException(
                status_code=500,
                detail=(
                    "User registration failed."
                )
            )
            
            
            
   # ==================================================
    # GET ALL VISIBLE USERS + ROLE SUMMARY
    # ==================================================

    # ==================================================
    # GET VISIBLE USERS + FILTERS + SUMMARY
    # ==================================================

    def get_all_users(
        self,
        current_user,
        role=None,
        company=None,
        plant=None,
        department=None,
        workstation=None,
        search=None,
    ):

        # ==============================================
        # FIRST: SECURITY / HIERARCHY
        # ==============================================

        users = (
            self.repository
            .get_visible_users(
                current_user
            )
        )


        # ==============================================
        # ROLE FILTER
        # ==============================================

        if role:

            normalized_role = (
                role
                .strip()
                .lower()
                .replace(" ", "_")
            )

            users = [
                user
                for user in users
                if (
                    user.role
                    and
                    user.role.strip().lower()
                    ==
                    normalized_role
                )
            ]


        # ==============================================
        # COMPANY FILTER
        # ==============================================

        if company:

            company_value = (
                company
                .strip()
                .lower()
            )

            users = [
                user
                for user in users
                if (
                    user.company
                    and
                    user.company.strip().lower()
                    ==
                    company_value
                )
            ]


        # ==============================================
        # PLANT FILTER
        # ==============================================

        if plant:

            plant_value = (
                plant
                .strip()
                .lower()
            )

            users = [
                user
                for user in users
                if (
                    user.plant
                    and
                    user.plant.strip().lower()
                    ==
                    plant_value
                )
            ]


        # ==============================================
        # DEPARTMENT FILTER
        # ==============================================

        if department:

            department_value = (
                department
                .strip()
                .lower()
            )

            users = [
                user
                for user in users
                if (
                    user.department
                    and
                    user.department.strip().lower()
                    ==
                    department_value
                )
            ]


        # ==============================================
        # WORKSTATION FILTER
        # ==============================================

        if workstation:

            workstation_value = (
                workstation
                .strip()
                .lower()
            )

            users = [
                user
                for user in users
                if (
                    user.workstation
                    and
                    user.workstation.strip().lower()
                    ==
                    workstation_value
                )
            ]


        # ==============================================
        # SEARCH
        # Search by name / email / job title
        # ==============================================

        if search:

            search_value = (
                search
                .strip()
                .lower()
            )

            users = [
                user
                for user in users
                if (
                    search_value
                    in (
                        user.full_name or ""
                    ).lower()

                    or

                    search_value
                    in (
                        user.email or ""
                    ).lower()

                    or

                    search_value
                    in (
                        user.job_title or ""
                    ).lower()
                )
            ]


        # ==============================================
        # COUNTS FOR CURRENT RESULT
        # ==============================================

        role_counts = {
            "super_admin": 0,
            "plant_admin": 0,
            "department_head": 0,
            "supervisor": 0,
        }


        for user in users:

            if user.role in role_counts:

                role_counts[
                    user.role
                ] += 1


        # ==============================================
        # SAFE USER RESPONSE
        # ==============================================

        user_list = [

            self.repository.to_dict(
                user
            )

            for user in users
        ]


        # ==============================================
        # RESPONSE
        # ==============================================

        return {

            "summary": {

                "total":
                    len(user_list),

                "role_counts":
                    role_counts,
            },

            "users":
                user_list,
        }
            
    def can_manage_user(
        self,
        current_user,
        target_user
    ):

        # ==========================================
        # SELF
        # ==========================================

        if current_user.id == target_user.id:
            return True


        # ==========================================
        # LOAD BOTH ROLES
        # ==========================================

        actor_role = (
            self.role_repository
            .get_by_name(
                current_user.role
            )
        )

        target_role = (
            self.role_repository
            .get_by_name(
                target_user.role
            )
        )


        if actor_role is None or target_role is None:
            return False


        # ==========================================
        # HIERARCHY
        #
        # Must be strictly higher.
        # ==========================================

        if (
            actor_role.hierarchy_level
            <=
            target_role.hierarchy_level
        ):
            return False


        # ==========================================
        # ORGANIZATION SCOPE
        # ==========================================

        scope = (
            actor_role.scope_type
            .strip()
            .lower()
        )


        if scope == "global":
            return True


        if scope == "plant":

            return (
                current_user.plant
                ==
                target_user.plant
            )


        if scope == "department":

            return (
                current_user.plant
                ==
                target_user.plant

                and

                current_user.department
                ==
                target_user.department
            )


        if scope == "workstation":

            return (
                current_user.plant
                ==
                target_user.plant

                and

                current_user.department
                ==
                target_user.department

                and

                current_user.workstation
                ==
                target_user.workstation
            )


        return False
    
    
    def update_user(
        self,
        user_id: int,
        request,
        current_user
    ):

        target_user = (
            self.repository
            .get_by_id(
                user_id
            )
        )

        if target_user is None:

            raise HTTPException(
                status_code=404,
                detail="User not found."
            )


        if not self.can_manage_user(
            current_user,
            target_user
        ):

            raise HTTPException(
                status_code=403,
                detail=(
                    "You are not authorized "
                    "to update this user."
                )
            )


        updates = (
            request.model_dump(
                exclude_unset=True
            )
        )


        # ==========================================
        # SELF-EDIT SECURITY
        # ==========================================

        if current_user.id == target_user.id:

            protected_fields = {
                "role",
                "account_status",
                "company",
                "plant",
                "department",
                "workstation",
            }

            attempted = (
                protected_fields
                &
                set(updates.keys())
            )

            if attempted:

                raise HTTPException(
                    status_code=403,
                    detail={
                        "message":
                            "You cannot change these "
                            "fields on your own account.",

                        "fields":
                            sorted(attempted)
                    }
                )


        # ==========================================
        # EMAIL
        # ==========================================

        if "email" in updates:

            email = (
                str(updates["email"])
                .strip()
                .lower()
            )

            existing = (
                self.repository
                .get_by_email(
                    email
                )
            )

            if (
                existing
                and existing.id != target_user.id
            ):

                raise HTTPException(
                    status_code=409,
                    detail=(
                        "A user with this email "
                        "already exists."
                    )
                )

            updates["email"] = email


        # ==========================================
        # PHONE
        # ==========================================

        if (
            "phone_number" in updates
            and updates["phone_number"]
        ):

            existing = (
                self.repository
                .get_by_phone_number(
                    updates["phone_number"]
                )
            )

            if (
                existing
                and existing.id != target_user.id
            ):

                raise HTTPException(
                    status_code=409,
                    detail=(
                        "A user with this phone "
                        "number already exists."
                    )
                )


        # ==========================================
        # ROLE
        # ==========================================

        if "role" in updates:

            role_name = (
                updates["role"]
                .strip()
                .lower()
                .replace(" ", "_")
            )

            new_role = (
                self.role_repository
                .get_by_name(
                    role_name
                )
            )

            if new_role is None:

                raise HTTPException(
                    status_code=400,
                    detail="Role does not exist."
                )

            if not new_role.is_active:

                raise HTTPException(
                    status_code=400,
                    detail="Role is inactive."
                )

            actor_role = (
                self.role_repository
                .get_by_name(
                    current_user.role
                )
            )

            if actor_role is None:

                raise HTTPException(
                    status_code=403,
                    detail="Current role is invalid."
                )

            if (
                new_role.hierarchy_level
                >=
                actor_role.hierarchy_level
            ):

                raise HTTPException(
                    status_code=403,
                    detail=(
                        "You cannot assign a role "
                        "equal to or higher than "
                        "your own role."
                    )
                )

            updates["role"] = new_role.name


        updated = (
            self.repository
            .update(
                user_id,
                updates
            )
        )

        return updated
    
    
    
    
    def delete_user(
        self,
        user_id: int,
        current_user
    ):

        target_user = (
            self.repository
            .get_by_id(
                user_id
            )
        )

        if target_user is None:

            raise HTTPException(
                status_code=404,
                detail="User not found."
            )


        # Do  self-deletion.
        if (
            current_user.id
            ==
            target_user.id
        ):

            deleted_user = (
                self.repository
                .delete(
                    user_id
                )
            )

            return deleted_user


        if not self.can_manage_user(
            current_user,
            target_user
        ):

            raise HTTPException(
                status_code=403,
                detail=(
                    "You are not authorized "
                    "to delete this user."
                )
            )


        deleted = (
            self.repository
            .delete(
                user_id
            )
        )

        return deleted