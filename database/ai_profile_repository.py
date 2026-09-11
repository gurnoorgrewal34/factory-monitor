from database.database import SessionLocal
from database.models import AIProfile


class AIProfileRepository:

    def get_all(self):
        with SessionLocal() as db:
            return (
                db.query(AIProfile)
                .order_by(AIProfile.name.asc())
                .all()
            )

    def get_by_id(
        self,
        profile_id: int
    ):
        with SessionLocal() as db:
            return (
                db.query(AIProfile)
                .filter(
                    AIProfile.id == profile_id
                )
                .first()
            )

    def get_by_name(
        self,
        name: str
    ):
        with SessionLocal() as db:
            return (
                db.query(AIProfile)
                .filter(
                    AIProfile.name == name
                )
                .first()
            )

    def create(
        self,
        data: dict
    ):
        with SessionLocal() as db:

            profile = AIProfile(
                **data
            )

            db.add(profile)
            db.commit()
            db.refresh(profile)

            return profile

    def update(
        self,
        profile_id: int,
        updates: dict
    ):
        with SessionLocal() as db:

            profile = (
                db.query(AIProfile)
                .filter(
                    AIProfile.id == profile_id
                )
                .first()
            )

            if profile is None:
                return None

            for key, value in updates.items():
                setattr(
                    profile,
                    key,
                    value
                )

            db.commit()
            db.refresh(profile)

            return profile

    def delete(
        self,
        profile_id: int
    ):
        with SessionLocal() as db:

            profile = (
                db.query(AIProfile)
                .filter(
                    AIProfile.id == profile_id
                )
                .first()
            )

            if profile is None:
                return None

            deleted = {
                "id": profile.id,
                "name": profile.name,
                "model_path_or_url": profile.model_path_or_url,
                "description": profile.description,
                "modules": profile.modules,
                "is_active": profile.is_active,
            }

            db.delete(profile)
            db.commit()

            return deleted