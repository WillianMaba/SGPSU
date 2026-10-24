
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.db.session import get_db
from app.models.user import User

from app.schemas.process_stage import (
    ProcessStageCreate,
    ProcessStageUpdate,
    ProcessStageRead,
    ProcessStageHistoryRead,
)

from app.services.process_access_service import ProcessAccessService

from app.services.process_stage_service import (
    ProcessStageService,
    ProcessStageNotFoundError,
    ProcessStageReferenceError,
    ProcessStageSequenceError,
    ProcessStageInvalidUpdateError,
    ProcessStageInvalidTransitionError,
)


router = APIRouter(
    prefix="/processes",
    tags=["Process Stages"],
)


def get_authorized_process(
    db: Session,
    current_user: User,
    process_id: int,
    require_update: bool = False,
):
    access = ProcessAccessService(db)

    process = access.get_readable_process(
        user=current_user,
        process_id=process_id,
    )

    if require_update:
        access.require_update(
            user=current_user,
            process=process,
        )

    return process


def handle_stage_error(exc: Exception) -> HTTPException:

    if isinstance(exc, ProcessStageNotFoundError):
        return HTTPException(
            status_code=404,
            detail=str(exc),
        )

    if isinstance(exc, ProcessStageReferenceError):
        return HTTPException(
            status_code=400,
            detail=str(exc),
        )

    if isinstance(exc, ProcessStageInvalidUpdateError):
        return HTTPException(
            status_code=422,
            detail=str(exc),
        )

    if isinstance(
        exc,
        (
            ProcessStageSequenceError,
            ProcessStageInvalidTransitionError,
        ),
    ):
        return HTTPException(
            status_code=409,
            detail=str(exc),
        )

    return HTTPException(
        status_code=500,
        detail="Erro interno ao processar a etapa.",
    )


# ============================================================
# CRIAR ETAPA
# ============================================================

@router.post(
    "/{process_id}/stages",
    response_model=ProcessStageRead,
    status_code=status.HTTP_201_CREATED,
)
def create_stage(
    process_id: int,
    data: ProcessStageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    process = get_authorized_process(
        db,
        current_user,
        process_id,
        require_update=True,
    )

    service = ProcessStageService(db)

    try:
        stage = service.create_stage(
            process_id=process.id,
            user_id=current_user.id,
            data=data,
        )

        db.commit()
        return stage

    except (
        ProcessStageReferenceError,
        ProcessStageSequenceError,
    ) as exc:
        db.rollback()
        raise handle_stage_error(exc) from exc

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Conflito de integridade ao criar etapa.",
        ) from exc


# ============================================================
# LISTAR ETAPAS
# ============================================================

@router.get(
    "/{process_id}/stages",
    response_model=list[ProcessStageRead],
)
def list_stages(
    process_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    process = get_authorized_process(
        db,
        current_user,
        process_id,
    )

    return ProcessStageService(db).list_stages(
        process_id=process.id,
    )


# ============================================================
# ATUALIZAR ETAPA
# ============================================================

@router.patch(
    "/{process_id}/stages/{stage_id}",
    response_model=ProcessStageRead,
)
def update_stage(
    process_id: int,
    stage_id: int,
    data: ProcessStageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    process = get_authorized_process(
        db,
        current_user,
        process_id,
        require_update=True,
    )

    service = ProcessStageService(db)

    try:
        stage = service.update_stage(
            process_id=process.id,
            stage_id=stage_id,
            user_id=current_user.id,
            data=data,
        )

        db.commit()
        return stage

    except (
        ProcessStageNotFoundError,
        ProcessStageReferenceError,
        ProcessStageSequenceError,
        ProcessStageInvalidUpdateError,
    ) as exc:
        db.rollback()
        raise handle_stage_error(exc) from exc

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Conflito de integridade ao atualizar etapa.",
        ) from exc


# ============================================================
# INICIAR ETAPA
# ============================================================

@router.post(
    "/{process_id}/stages/{stage_id}/start",
    response_model=ProcessStageRead,
)
def start_stage(
    process_id: int,
    stage_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    process = get_authorized_process(
        db,
        current_user,
        process_id,
        require_update=True,
    )

    service = ProcessStageService(db)

    try:
        stage = service.start_stage(
            process_id=process.id,
            stage_id=stage_id,
            user_id=current_user.id,
        )

        db.commit()
        return stage

    except (
        ProcessStageNotFoundError,
        ProcessStageInvalidTransitionError,
    ) as exc:
        db.rollback()
        raise handle_stage_error(exc) from exc


# ============================================================
# CONCLUIR ETAPA
# ============================================================

@router.post(
    "/{process_id}/stages/{stage_id}/complete",
    response_model=ProcessStageRead,
)
def complete_stage(
    process_id: int,
    stage_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    process = get_authorized_process(
        db,
        current_user,
        process_id,
        require_update=True,
    )

    service = ProcessStageService(db)

    try:
        stage = service.complete_stage(
            process_id=process.id,
            stage_id=stage_id,
            user_id=current_user.id,
        )

        db.commit()
        return stage

    except (
        ProcessStageNotFoundError,
        ProcessStageInvalidTransitionError,
    ) as exc:
        db.rollback()
        raise handle_stage_error(exc) from exc


# ============================================================
# CONSULTAR HISTORICO
# ============================================================

@router.get(
    "/{process_id}/stages/{stage_id}/history",
    response_model=list[ProcessStageHistoryRead],
)
def list_stage_history(
    process_id: int,
    stage_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    process = get_authorized_process(
        db,
        current_user,
        process_id,
    )

    try:
        return ProcessStageService(db).list_history(
            process_id=process.id,
            stage_id=stage_id,
        )

    except ProcessStageNotFoundError as exc:
        raise handle_stage_error(exc) from exc
