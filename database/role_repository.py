from database.database import SessionLocal
from database.models import Role


class RoleRepository:

    def get_all(self):
        with SessionLocal() as db:
            return (
                db.query(Role)
                .order_by(Role.hierarchy_level.desc())
                .all()
            )

    def get_by_id(self, role_id: int):
        with SessionLocal() as db:
            return (
                db.query(Role)
                .filter(Role.id == role_id)
                .first()
            )

    def get_by_name(self, name: str):
        with SessionLocal() as db:
            return (
                db.query(Role)
                .filter(Role.name == name)
                .first()
            )

    def create(self, data: dict):
        with SessionLocal() as db:
            role = Role(**data)

            db.add(role)
            db.commit()
            db.refresh(role)

            return role

    def update(
        self,
        role_id: int,
        updates: dict
    ):
        with SessionLocal() as db:
            role = (
                db.query(Role)
                .filter(Role.id == role_id)
                .first()
            )

            if role is None:
                return None

            for key, value in updates.items():
                setattr(
                    role,
                    key,
                    value
                )

            db.commit()
            db.refresh(role)

            return role

    def delete(
        self,
        role_id: int
    ):
        with SessionLocal() as db:
            role = (
                db.query(Role)
                .filter(Role.id == role_id)
                .first()
            )

            if role is None:
                return None

            role_data = {
                "id": role.id,
                "name": role.name,
                "display_name": role.display_name,
                "hierarchy_level": role.hierarchy_level,
                "scope_type": role.scope_type,
                "is_active": role.is_active,
            }

            db.delete(role)
            db.commit()

            return role_data