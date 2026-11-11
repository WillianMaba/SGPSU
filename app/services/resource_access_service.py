
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.repository import Repository
from app.models.folder import Folder
from app.models.file import File

from app.models.repository_access import RepositoryAccess
from app.models.folder_access import FolderAccess
from app.models.file_access import FileAccess

from app.models.user import User


class ResourceAccessError(Exception):
    pass


class ResourceAccessService:

    VALID_PERMISSIONS = {
        "READ",
        "WRITE",
        "MODIFY",
        "DELETE",
        "ADMIN",
    }

    def __init__(self, db: Session):
        self.db = db

    # ========================================================
    # IDENTIFICAR REGRAS APLICAVEIS AO USUARIO
    # ========================================================

    def _get_rules(
        self,
        access_model,
        resource_field: str,
        resource_id: int,
        user: User,
        permission: str,
    ) -> list:

        conditions = [
            access_model.user_id == user.id,
        ]

        if user.profile_id is not None:
            conditions.append(
                access_model.profile_id == user.profile_id
            )

        if user.sector_id is not None:
            conditions.append(
                access_model.sector_id == user.sector_id
            )

        statement = (
            select(access_model)
            .where(
                getattr(access_model, resource_field) == resource_id,
                access_model.is_active.is_(True),
                access_model.permission.in_(
                    [permission, "ADMIN"]
                ),
                or_(*conditions),
            )
        )

        return list(self.db.scalars(statement).all())

    # ========================================================
    # LOCALIZAR HIERARQUIA DE PASTAS
    # ========================================================

    def _get_folder_hierarchy(
        self,
        folder: Folder,
    ) -> list[Folder] | None:

        hierarchy = []
        visited = set()
        current = folder

        while current is not None:

            if current.id in visited:
                return None

            visited.add(current.id)

            if (
                not current.is_active
                or current.repository_id != folder.repository_id
            ):
                return None

            hierarchy.append(current)

            if current.parent_folder_id is None:
                break

            parent = self.db.get(
                Folder,
                current.parent_folder_id,
            )

            if parent is None:
                return None

            current = parent

        return hierarchy

    # ========================================================
    # COLETAR REGRAS DA HIERARQUIA
    # ========================================================

    def _collect_resource_rules(
        self,
        user: User,
        resource,
        permission: str,
    ) -> list:

        rules = []

        if isinstance(resource, Repository):

            if not resource.is_active:
                return []

            rules.extend(
                self._get_rules(
                    RepositoryAccess,
                    "repository_id",
                    resource.id,
                    user,
                    permission,
                )
            )

            return rules

        if isinstance(resource, Folder):

            if not resource.is_active:
                return []

            hierarchy = self._get_folder_hierarchy(resource)

            if hierarchy is None:
                return []

            repository = self.db.get(
                Repository,
                resource.repository_id,
            )

            if repository is None or not repository.is_active:
                return []

            for folder in hierarchy:
                rules.extend(
                    self._get_rules(
                        FolderAccess,
                        "folder_id",
                        folder.id,
                        user,
                        permission,
                    )
                )

            rules.extend(
                self._get_rules(
                    RepositoryAccess,
                    "repository_id",
                    repository.id,
                    user,
                    permission,
                )
            )

            return rules

        if isinstance(resource, File):

            if not resource.is_active:
                return []

            folder = self.db.get(
                Folder,
                resource.folder_id,
            )

            if folder is None:
                return []

            hierarchy = self._get_folder_hierarchy(folder)

            if hierarchy is None:
                return []

            repository = self.db.get(
                Repository,
                folder.repository_id,
            )

            if repository is None or not repository.is_active:
                return []

            rules.extend(
                self._get_rules(
                    FileAccess,
                    "file_id",
                    resource.id,
                    user,
                    permission,
                )
            )

            for parent_folder in hierarchy:
                rules.extend(
                    self._get_rules(
                        FolderAccess,
                        "folder_id",
                        parent_folder.id,
                        user,
                        permission,
                    )
                )

            rules.extend(
                self._get_rules(
                    RepositoryAccess,
                    "repository_id",
                    repository.id,
                    user,
                    permission,
                )
            )

            return rules

        return []

    # ========================================================
    # VERIFICAR ACESSO
    # ========================================================

    def can_access(
        self,
        user: User,
        resource,
        permission: str,
    ) -> bool:

        permission = permission.upper()

        if permission not in self.VALID_PERMISSIONS:
            return False

        if not user.is_active:
            return False

        rules = self._collect_resource_rules(
            user=user,
            resource=resource,
            permission=permission,
        )

        if not rules:
            return False

        # DENY aplicavel sempre prevalece.
        if any(rule.effect == "DENY" for rule in rules):
            return False

        # Sem DENY, basta existir um ALLOW aplicavel.
        return any(
            rule.effect == "ALLOW"
            for rule in rules
        )

    # ========================================================
    # EXIGIR ACESSO
    # ========================================================

    def require_access(
        self,
        user: User,
        resource,
        permission: str,
    ) -> None:

        if not self.can_access(
            user=user,
            resource=resource,
            permission=permission,
        ):
            raise ResourceAccessError(
                "Usuario nao possui acesso a este recurso."
            )

    # ========================================================
    # ATALHOS DE AUTORIZACAO
    # ========================================================

    def can_read(self, user: User, resource) -> bool:
        return self.can_access(user, resource, "READ")

    def can_write(self, user: User, resource) -> bool:
        return self.can_access(user, resource, "WRITE")

    def can_modify(self, user: User, resource) -> bool:
        return self.can_access(user, resource, "MODIFY")

    def can_delete(self, user: User, resource) -> bool:
        return self.can_access(user, resource, "DELETE")

    def can_admin(self, user: User, resource) -> bool:
        return self.can_access(user, resource, "ADMIN")
