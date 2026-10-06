from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.permission import Permission
from app.models.profile_permission import ProfilePermission


class ProfilePermissionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(
        self,
        profile_id: int,
        permission_id: int,
    ) -> ProfilePermission | None:

        statement = select(ProfilePermission).where(
            ProfilePermission.profile_id == profile_id,
            ProfilePermission.permission_id == permission_id,
        )

        return self.db.scalar(statement)

    def list_by_profile(
        self,
        profile_id: int,
    ) -> list[Permission]:

        statement = (
            select(Permission)
            .join(
                ProfilePermission,
                ProfilePermission.permission_id == Permission.id,
            )
            .where(
                ProfilePermission.profile_id == profile_id,
                ProfilePermission.is_active.is_(True),
            )
            .order_by(Permission.id)
        )

        return list(
            self.db.scalars(statement).all()
        )

    def create(
        self,
        profile_id: int,
        permission_id: int,
    ) -> ProfilePermission:

        profile_permission = ProfilePermission(
            profile_id=profile_id,
            permission_id=permission_id,
            is_active=True,
        )

        self.db.add(profile_permission)
        self.db.flush()
        self.db.refresh(profile_permission)

        return profile_permission

    def activate(
        self,
        profile_permission: ProfilePermission,
    ) -> ProfilePermission:

        profile_permission.is_active = True

        self.db.add(profile_permission)
        self.db.flush()
        self.db.refresh(profile_permission)

        return profile_permission

    def deactivate(
        self,
        profile_permission: ProfilePermission,
    ) -> ProfilePermission:

        profile_permission.is_active = False

        self.db.add(profile_permission)
        self.db.flush()
        self.db.refresh(profile_permission)

        return profile_permission