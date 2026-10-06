from sqlalchemy.orm import Session
from app.models.permission import Permission
from app.models.profile_permission import ProfilePermission
from app.repositories.permission_repository import PermissionRepository
from app.repositories.profile_permission_repository import (
    ProfilePermissionRepository,
)
from app.repositories.profile_repository import ProfileRepository


class ProfileNotFoundError(Exception):
    pass


class PermissionNotFoundError(Exception):
    pass


class ProfilePermissionService:
    def __init__(self, db: Session):
        self.profile_repository = ProfileRepository(db)
        self.permission_repository = PermissionRepository(db)
        self.repository = ProfilePermissionRepository(db)

    def list_permissions(
        self,
        profile_id: int,
    ) -> list[Permission]:

        profile = self.profile_repository.get_by_id(
            profile_id,
        )

        if profile is None:
            raise ProfileNotFoundError(
                "Perfil nao encontrado."
            )

        return self.repository.list_by_profile(
            profile_id,
        )

    def add_permission(
        self,
        profile_id: int,
        permission_id: int,
    ) -> ProfilePermission:

        profile = self.profile_repository.get_by_id(
            profile_id,
        )

        if profile is None:
            raise ProfileNotFoundError(
                "Perfil nao encontrado."
            )

        permission = self.permission_repository.get_by_id(
            permission_id,
        )

        if permission is None:
            raise PermissionNotFoundError(
                "Permissao nao encontrada."
            )

        existing = self.repository.get(
            profile_id=profile_id,
            permission_id=permission_id,
        )

        if existing is not None:
            return self.repository.activate(existing)

        return self.repository.create(
            profile_id=profile_id,
            permission_id=permission_id,
        )

    def remove_permission(
        self,
        profile_id: int,
        permission_id: int,
    ) -> ProfilePermission:

        existing = self.repository.get(
            profile_id=profile_id,
            permission_id=permission_id,
        )

        if existing is None:
            raise PermissionNotFoundError(
                "Associacao entre perfil e permissao nao encontrada."
            )

        return self.repository.deactivate(existing)