from sqlalchemy.orm import Session
from app.models.permission import Permission
from app.repositories.permission_repository import PermissionRepository
from app.schemas.permission import PermissionCreate, PermissionUpdate


class PermissionAlreadyExistsError(Exception):
    pass


class PermissionService:
    def __init__(self, db: Session):
        self.repository = PermissionRepository(db)

    def create_permission(
        self,
        data: PermissionCreate,
    ) -> Permission:

        existing_permission = self.repository.get_by_name(
            data.name,
        )

        if existing_permission is not None:
            raise PermissionAlreadyExistsError(
                "Ja existe uma permissao com este nome."
            )

        return self.repository.create(data)

    def get_permission(
        self,
        permission_id: int,
    ) -> Permission | None:

        return self.repository.get_by_id(permission_id)

    def get_permissions(self) -> list[Permission]:
        return self.repository.list()

    def update_permission(
        self,
        permission: Permission,
        data: PermissionUpdate,
    ) -> Permission:

        if data.name is not None:
            existing_permission = self.repository.get_by_name(
                data.name,
            )

            if (
                existing_permission is not None
                and existing_permission.id != permission.id
            ):
                raise PermissionAlreadyExistsError(
                    "Ja existe outra permissao com este nome."
                )

        return self.repository.update(
            permission=permission,
            data=data,
        )

    def deactivate_permission(
        self,
        permission: Permission,
    ) -> Permission:

        return self.repository.deactivate(permission)