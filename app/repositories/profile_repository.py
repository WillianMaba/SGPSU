from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.profile import Profile
from app.schemas.profile import ProfileCreate, ProfileUpdate


class ProfileRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, profile_id: int) -> Profile | None:
        statement = select(Profile).where(
            Profile.id == profile_id,
        )

        return self.db.scalar(statement)

    def get_by_name(self, name: str) -> Profile | None:
        statement = select(Profile).where(
            Profile.name == name,
        )

        return self.db.scalar(statement)

    def list(self) -> list[Profile]:
        statement = select(Profile).order_by(Profile.id)

        return list(
            self.db.scalars(statement).all()
        )

    def create(self, data: ProfileCreate) -> Profile:
        profile = Profile(
            name=data.name,
            description=data.description,
            is_active=True,
        )

        self.db.add(profile)
        self.db.flush()
        self.db.refresh(profile)

        return profile

    def update(
        self,
        profile: Profile,
        data: ProfileUpdate,
    ) -> Profile:

        values = data.model_dump(
            exclude_unset=True,
        )

        for field, value in values.items():
            setattr(profile, field, value)

        self.db.add(profile)
        self.db.flush()
        self.db.refresh(profile)

        return profile

    def deactivate(self, profile: Profile) -> Profile:
        profile.is_active = False

        self.db.add(profile)
        self.db.flush()
        self.db.refresh(profile)

        return profile