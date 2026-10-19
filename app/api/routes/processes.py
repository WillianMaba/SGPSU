from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.core.authorization import require_permission
from app.core.permissions import PermissionNames
from app.db.session import get_db
from app.models.user import User

from app.schemas.process import (
    ProcessCreate,
    ProcessRead,
    ProcessUpdate,
)

from app.services.authorization_service import AuthorizationService
from app.services.process_access_service import ProcessAccessService

from app.services.process_service import (
    ProcessInitialStatusError,
    ProcessInvalidUpdateError,
    ProcessReferenceError,
    ProcessService,
)


router = APIRouter(
    prefix="/processes",
    tags=["Processes"],
)


# ============================================================
# CRIAR PROCESSO
# ============================================================

@router.post(
    "/",
    response_model=ProcessRead,
    status_code=status.HTTP_201_CREATED,
)
def create_process(
    data: ProcessCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PermissionNames.PROCESSES_CREATE)
    ),
) -> ProcessRead:

    authorization = AuthorizationService(db)

    # Informar um responsavel durante a criacao exige
    # a permissao especifica de atribuicao.
    if data.responsible_id is not None:

        if not authorization.has_permission(
            current_user,
            PermissionNames.PROCESSES_ASSIGN,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Usuario nao possui permissao "
                    "para atribuir responsaveis."
                ),
            )

    service = ProcessService(db)

    try:
        process = service.create_process(
            data=data,
            created_by_id=current_user.id,
        )

        db.commit()

        return process

    except ProcessReferenceError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except ProcessInitialStatusError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflito de integridade ao criar o processo.",
        ) from exc


# ============================================================
# LISTAR PROCESSOS
# ============================================================

@router.get(
    "/",
    response_model=list[ProcessRead],
)
def list_processes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ProcessRead]:

    authorization = AuthorizationService(db)

    can_read_all = authorization.has_permission(
        current_user,
        PermissionNames.PROCESSES_READ_ALL,
    )

    if can_read_all:
        return ProcessService(db).get_processes()

    can_read = authorization.has_permission(
        current_user,
        PermissionNames.PROCESSES_READ,
    )

    if not can_read:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario nao possui permissao para consultar processos.",
        )

    return ProcessService(db).get_visible_processes(
        current_user.id,
    )


# ============================================================
# CONSULTAR PROCESSO
# ============================================================

@router.get(
    "/{process_id}",
    response_model=ProcessRead,
)
def get_process(
    process_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProcessRead:

    return ProcessAccessService(db).get_readable_process(
        user=current_user,
        process_id=process_id,
    )


# ============================================================
# ATUALIZAR PROCESSO
# ============================================================

@router.patch(
    "/{process_id}",
    response_model=ProcessRead,
)
def update_process(
    process_id: int,
    data: ProcessUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProcessRead:

    access = ProcessAccessService(db)

    process = access.get_readable_process(
        user=current_user,
        process_id=process_id,
    )

    access.require_update(
        user=current_user,
        process=process,
    )

    values = data.model_dump(
        exclude_unset=True,
    )

    # Alterar o responsavel exige uma permissao adicional.
    if "responsible_id" in values:

        authorization = AuthorizationService(db)

        if not authorization.has_permission(
            current_user,
            PermissionNames.PROCESSES_ASSIGN,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Usuario nao possui permissao "
                    "para atribuir responsaveis."
                ),
            )

    try:
        updated = ProcessService(db).update_process(
            process=process,
            data=data,
        )

        db.commit()

        return updated

    except ProcessInvalidUpdateError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except ProcessReferenceError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflito de integridade ao atualizar o processo.",
        ) from exc