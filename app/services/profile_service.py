from sqlalchemy.orm import Session
from app.models.profile import Profile
from app.repositories.profile_repository import ProfileRepository
from app.schemas.profile import ProfileCreate, ProfileUpdate


class ProfileAlreadyExistsError(Exception):
    pass


class ProfileService:
    def __init__(self, db: Session):
        self.repository = ProfileRepository(db)

    def create_profile(self, data: ProfileCreate) -> Profile:
        existing_profile = self.repository.get_by_name(
            data.name,
        )

        if existing_profile is not None:
            raise ProfileAlreadyExistsError(
                "Ja existe um perfil com este nome."
            )

        return self.repository.create(data)

    def get_profile(self, profile_id: int) -> Profile | None:
        return self.repository.get_by_id(profile_id)

    def get_profiles(self) -> list[Profile]:
        return self.repository.list()

    def update_profile(
        self,
        profile: Profile,
        data: ProfileUpdate,
    ) -> Profile:

        if data.name is not None:
            existing_profile = self.repository.get_by_name(
                data.name,
            )

            if (
                existing_profile is not None
                and existing_profile.id != profile.id
            ):
                raise ProfileAlreadyExistsError(
                    "Ja existe outro perfil com este nome."
                )

        return self.repository.update(
            profile=profile,
            data=data,
        )

    def deactivate_profile(
        self,
        profile: Profile,
    ) -> Profile:
        return self.repository.deactivate(profile)