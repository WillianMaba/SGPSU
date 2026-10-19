from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.permissions import PermissionNames
from app.models.process import Process
from app.models.user import User
from app.services.authorization_service import AuthorizationService


class ProcessAccessService:

    def __init__(self, db: Session):
        self.db = db
        self.authorization = AuthorizationService(db)

    def can_read(
        self,
        user: User,
        process: Process,
    ) -> bool:

        if self.authorization.has_permission(
            user,
            PermissionNames.PROCESSES_READ_ALL,
        ):
            return True

        if not self.authorization.has_permission(
            user,
            PermissionNames.PROCESSES_READ,
        ):
            return False

        return (
            process.created_by_id == user.id
            or process.responsible_id == user.id
        )

    def can_update(
        self,
        user: User,
        process: Process,
    ) -> bool:

        if self.authorization.has_permission(
            user,
            PermissionNames.PROCESSES_UPDATE_ALL,
        ):
            return True

        if not self.authorization.has_permission(
            user,
            PermissionNames.PROCESSES_UPDATE,
        ):
            return False

        return process.responsible_id == user.id

    def require_read(
        self,
        user: User,
        process: Process,
    ) -> None:

        if not self.can_read(user, process):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Processo nao encontrado.",
            )

    def require_update(
        self,
        user: User,
        process: Process,
    ) -> None:

        if not self.can_update(user, process):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Usuario nao possui autorizacao "
                    "para alterar este processo."
                ),
            )

    def get_readable_process(
        self,
        user: User,
        process_id: int,
    ) -> Process:

        process = self.db.get(
            Process,
            process_id,
        )

        if process is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Processo nao encontrado.",
            )

        self.require_read(
            user=user,
            process=process,
        )

        return process