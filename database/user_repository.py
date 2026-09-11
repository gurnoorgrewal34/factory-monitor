from sqlalchemy import func

from database.database import (
    SessionLocal,
)

from database.models import (
    User,
)


class UserRepository:

    # ==================================================
    # USER MODEL -> SAFE RESPONSE
    # ==================================================

    @staticmethod
    def to_dict(
        user
    ):

        return {

            "id":
                user.id,

            "email":
                user.email,

            "role":
                user.role,
                
            "role_id":
                user.role_id,

            "full_name":
                user.full_name,

            "job_title":
                user.job_title,

            "phone_number":
                user.phone_number,

            "image_url":
                user.image_url,

            "account_status":
                user.account_status,

            "company":
                user.company,

            "plant":
                user.plant,

            "department":
                user.department,

            "workstation":
                user.workstation,

            "created_time":
                (
                    user.created_time.isoformat()
                    if user.created_time
                    else None
                ),
        }


    # ==================================================
    # GET BY EMAIL
    # ==================================================

    def get_by_email(
        self,
        email
    ):

        with SessionLocal() as db:

            user = (

                db.query(
                    User
                )

                .filter(
                    func.lower(
                        User.email
                    )
                    ==
                    email.lower()
                )

                .first()
            )

            return user

    # ==================================================
    # GET USER BY ID
    # ==================================================

    def get_by_id(
        self,
        user_id
    ):

        with SessionLocal() as db:

            return (

                db.query(
                    User
                )

                .filter(
                    User.id
                    ==
                    user_id
                )

                .first()
            )
        # ==================================================
    # GET BY PHONE
    # ==================================================

    def get_by_phone_number(
        self,
        phone_number
    ):

        with SessionLocal() as db:

            return (

                db.query(
                    User
                )

                .filter(
                    User.phone_number
                    ==
                    phone_number
                )

                .first()
            )


    # ==================================================
    # CREATE USER
    # ==================================================

    def create(
        self,
        data
    ):

        with SessionLocal() as db:

            user = User(

                email=
                    data["email"],

                password=
                    data["password"],

                role=
                    data["role"],

                full_name=
                    data["full_name"],

                job_title=
                    data.get(
                        "job_title"
                    ),

                phone_number=
                    data.get(
                        "phone_number"
                    ),

                image_url=
                    data.get(
                        "image_url"
                    ),

                account_status=
                    data.get(
                        "account_status",
                        False
                    ),
                    
                role_id=
                    data.get(
                        "role_id"
                    ),

                company=
                    data.get(
                        "company"
                    ),

                plant=
                    data.get(
                        "plant"
                    ),

                department=
                    data.get(
                        "department"
                    ),

                workstation=
                    data.get(
                        "workstation"
                    ),
            )

            db.add(
                user
            )

            db.commit()

            db.refresh(
                user
            )

            return self.to_dict(
                user
            )
            
            
    def get_all(self):

        with SessionLocal() as db:

            users = (
                db.query(User)
                .order_by(User.id.asc())
                .all()
            )

            return users     
        
        
    def get_visible_users(
        self,
        current_user
    ):

        with SessionLocal() as db:

            query = db.query(User)

            # ==========================================
            # SUPER ADMIN
            # Can see everyone
            # ==========================================

            if current_user.role == "super_admin":

                users = (
                    query
                    .order_by(User.id.asc())
                    .all()
                )

                return users


            # ==========================================
            # PLANT ADMIN
            # Can see Department Heads + Supervisors
            # only from own plant
            # ==========================================

            if current_user.role == "plant_admin":

                users = (
                    query
                    .filter(
                        User.plant
                        == current_user.plant
                    )
                    .filter(
                        User.role.in_(
                            [
                                "department_head",
                                "supervisor",
                            ]
                        )
                    )
                    .order_by(User.id.asc())
                    .all()
                )

                return users


            # ==========================================
            # DEPARTMENT HEAD
            # Can see Supervisors
            # only from own plant + department
            # ==========================================

            if current_user.role == "department_head":

                users = (
                    query
                    .filter(
                        User.plant
                        == current_user.plant
                    )
                    .filter(
                        User.department
                        == current_user.department
                    )
                    .filter(
                        User.role
                        == "supervisor"
                    )
                    .order_by(User.id.asc())
                    .all()
                )

                return users


            # ==========================================
            # SUPERVISOR / UNKNOWN ROLE
            # No subordinate users
            # ==========================================

            return []   
        
        
    def update(
        self,
        user_id: int,
        updates: dict
    ):

        with SessionLocal() as db:

            user = (
                db.query(User)
                .filter(
                    User.id == user_id
                )
                .first()
            )

            if user is None:
                return None

            for key, value in updates.items():

                setattr(
                    user,
                    key,
                    value
                )

            db.commit()
            db.refresh(user)

            return self.to_dict(
                user
            )


    def delete(
        self,
        user_id: int
    ):

        with SessionLocal() as db:

            user = (
                db.query(User)
                .filter(
                    User.id == user_id
                )
                .first()
            )

            if user is None:
                return None

            deleted_user = (
                self.to_dict(
                    user
                )
            )

            db.delete(user)
            db.commit()

            return deleted_user