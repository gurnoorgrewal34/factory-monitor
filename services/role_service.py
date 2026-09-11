from fastapi import HTTPException

from database.role_repository import RoleRepository


class RoleService:

    def __init__(self):
        self.repository = RoleRepository()

    def get_all_roles(self):
        return self.repository.get_all()

    def get_role_by_id(
        self,
        role_id: int
    ):
        role = (
            self.repository
            .get_by_id(role_id)
        )

        if role is None:
            raise HTTPException(
                status_code=404,
                detail="Role not found."
            )

        return role

    def create_role(
        self,
        request
    ):
        name = (
            request.name
            .strip()
            .lower()
            .replace(" ", "_")
        )

        existing = (
            self.repository
            .get_by_name(name)
        )

        if existing:
            raise HTTPException(
                status_code=409,
                detail="A role with this name already exists."
            )

        data = request.model_dump()

        data["name"] = name

        data["display_name"] = (
            request.display_name
            .strip()
        )

        data["scope_type"] = (
            request.scope_type
            .strip()
            .lower()
        )

        return self.repository.create(
            data
        )

    def update_role(
        self,
        role_id: int,
        request
    ):
        current = self.get_role_by_id(
            role_id
        )

        updates = (
            request.model_dump(
                exclude_unset=True
            )
        )

        if "name" in updates:
            name = (
                updates["name"]
                .strip()
                .lower()
                .replace(" ", "_")
            )

            existing = (
                self.repository
                .get_by_name(name)
            )

            if (
                existing
                and existing.id != current.id
            ):
                raise HTTPException(
                    status_code=409,
                    detail="A role with this name already exists."
                )

            updates["name"] = name

        if "display_name" in updates:
            updates["display_name"] = (
                updates["display_name"]
                .strip()
            )

        if "scope_type" in updates:
            updates["scope_type"] = (
                updates["scope_type"]
                .strip()
                .lower()
            )

        role = self.repository.update(
            role_id,
            updates
        )

        if role is None:
            raise HTTPException(
                status_code=404,
                detail="Role not found."
            )

        return role

    def delete_role(
        self,
        role_id: int
    ):
        self.get_role_by_id(
            role_id
        )

        deleted = (
            self.repository
            .delete(role_id)
        )

        return deleted