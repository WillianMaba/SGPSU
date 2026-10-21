from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.db.session import get_db
from app.models.user import User

from app.schemas.process_progress import (
    ProcessProgressCreate,
    ProcessProgressRead,
)

from app.services.process_access_service import ProcessAccessService
from app.services.process_progress_service import ProcessProgressService


router = APIRouter(
    prefix="/processes",
    tags=["Process Progress"],
)


@router.post(
    "/{process_id}/progress",
    response_model=ProcessProgressRead,
    status_code=status.HTTP_201_CREATED,
)
def add_process_progress(
    process_id: int,
    data: ProcessProgressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProcessProgressRead:

    access = ProcessAccessService(db)

    process = access.get_readable_process(
        user=current_user,
        process_id=process_id,
    )

    access.require_update(
        user=current_user,
        process=process,
    )

    service = ProcessProgressService(db)

    try:
        progress = service.add_progress(
            process_id=process.id,
            user_id=current_user.id,
            data=data,
        )

        db.commit()

        return progress

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflito de integridade ao registrar movimentacao.",
        ) from exc


@router.get(
    "/{process_id}/progress",
    response_model=list[ProcessProgressRead],
)
def list_process_progress(
    process_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ProcessProgressRead]:

    access = ProcessAccessService(db)

    process = access.get_readable_process(
        user=current_user,
        process_id=process_id,
    )

    return ProcessProgressService(db).list_progress(
        process_id=process.id,
    )