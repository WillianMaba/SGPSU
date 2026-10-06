from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.permission import Permission
from app.schemas.permission import PermissionCreate, PermissionUpdate


class PermissionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        permission_id: int,
    ) -> Permission | None:

        statement = select(Permission).where(
            Permission.id == permission_id,
        )

        return self.db.scalar(statement)

    def get_by_name(
        self,
        name: str,
    ) -> Permission | None:

        statement = select(Permission).where(
            Permission.name == name,
        )

        return self.db.scalar(statement)

    def list(self) -> list[Permission]:
        statement = select(Permission).order_by(
            Permission.id,
        )

        return list(
            self.db.scalars(statement).all()
        )

    def create(
        self,
        data: PermissionCreate,
    ) -> Permission:

        permission = Permission(
            name=data.name,
            description=data.description,
            is_active=True,
        )

        self.db.add(permission)
        self.db.flush()
        self.db.refresh(permission)

        return permission

    def update(
        self,
        permission: Permission,
        data: PermissionUpdate,
    ) -> Permission:

        values = data.model_dump(
            exclude_unset=True,
        )

        for field, value in values.items():
            setattr(permission, field, value)

        self.db.add(permission)
        self.db.flush()
        self.db.refresh(permission)

        return permission

    def deactivate(
        self,
        permission: Permission,
    ) -> Permission:

        permission.is_active = False

        self.db.add(permission)
        self.db.flush()
        self.db.refresh(permission)

        return permission