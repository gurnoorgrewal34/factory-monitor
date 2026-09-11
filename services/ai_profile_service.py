from fastapi import HTTPException

from app.orchestrator import Orchestrator

from database.ai_profile_repository import (
    AIProfileRepository,
)


class AIProfileService:

    def __init__(self):

        self.repository = (
            AIProfileRepository()
        )

    def validate_modules(
        self,
        modules
    ):

        if not modules:

            raise HTTPException(
                status_code=400,
                detail=(
                    "At least one AI module "
                    "is required."
                )
            )

        normalized = [
            module.strip().lower()
            for module in modules
            if module
            and module.strip()
        ]

        if not normalized:

            raise HTTPException(
                status_code=400,
                detail=(
                    "At least one valid AI "
                    "module is required."
                )
            )

        orchestrator = (
            Orchestrator()
        )

        invalid = [
            module
            for module in normalized
            if module
            not in orchestrator.available_modules
        ]

        if invalid:

            raise HTTPException(
                status_code=400,
                detail={
                    "message":
                        "Invalid AI modules",

                    "invalid_modules":
                        invalid,

                    "available_modules":
                        sorted(
                            orchestrator
                            .available_modules
                        )
                }
            )

        return sorted(
            set(normalized)
        )

    def get_all_profiles(self):

        return (
            self.repository
            .get_all()
        )

    def get_profile(
        self,
        profile_id: int
    ):

        profile = (
            self.repository
            .get_by_id(
                profile_id
            )
        )

        if profile is None:

            raise HTTPException(
                status_code=404,
                detail="AI profile not found."
            )

        return profile

    def create_profile(
        self,
        request
    ):

        name = (
            request.name
            .strip()
        )

        existing = (
            self.repository
            .get_by_name(
                name
            )
        )

        if existing:

            raise HTTPException(
                status_code=409,
                detail=(
                    "An AI profile with this "
                    "name already exists."
                )
            )

        modules = (
            self.validate_modules(
                request.modules
            )
        )

        data = (
            request.model_dump()
        )

        data["name"] = name

        data["modules"] = modules

        if data.get("description"):
            data["description"] = (
                data["description"]
                .strip()
            )

        return (
            self.repository
            .create(
                data
            )
        )

    def update_profile(
        self,
        profile_id: int,
        request
    ):

        current = (
            self.get_profile(
                profile_id
            )
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
            )

            existing = (
                self.repository
                .get_by_name(
                    name
                )
            )

            if (
                existing
                and
                existing.id != current.id
            ):

                raise HTTPException(
                    status_code=409,
                    detail=(
                        "An AI profile with "
                        "this name already exists."
                    )
                )

            updates["name"] = name

        if "modules" in updates:

            updates["modules"] = (
                self.validate_modules(
                    updates["modules"]
                )
            )

        if (
            "description" in updates
            and
            updates["description"]
        ):

            updates["description"] = (
                updates["description"]
                .strip()
            )

        profile = (
            self.repository
            .update(
                profile_id,
                updates
            )
        )

        if profile is None:

            raise HTTPException(
                status_code=404,
                detail="AI profile not found."
            )

        return profile

    def delete_profile(
        self,
        profile_id: int
    ):

        self.get_profile(
            profile_id
        )

        return (
            self.repository
            .delete(
                profile_id
            )
        )