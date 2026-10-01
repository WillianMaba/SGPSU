from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.permission import Permission
from app.models.profile import Profile
from app.models.profile_permission import ProfilePermission
from app.models.user import User


class AuthorizationService:
    def __init__(self, db: Session):
        self.db = db

    def has_permission(
        self,
        user: User,
        permission_name: str,
    ) -> bool:

        if user.profile_id is None:
            return False

        statement = (
            select(Permission.id)
            .join(
                ProfilePermission,
                ProfilePermission.permission_id == Permission.id,
            )
            .join(
                Profile,
                Profile.id == ProfilePermission.profile_id,
            )
            .where(
                Profile.id == user.profile_id,
                Profile.is_active.is_(True),
                ProfilePermission.is_active.is_(True),
                Permission.name == permission_name,
                Permission.is_active.is_(True),
            )
        )

        permission_id = self.db.scalar(statement)

        return permission_id is not None