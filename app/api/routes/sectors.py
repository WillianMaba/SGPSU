from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.api.routes.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.sector import SectorCreate, SectorRead, SectorUpdate
from app.services.sector_service import (
    SectorAlreadyExistsError,
    SectorService,
)


router = APIRouter(
    prefix="/sectors",
    tags=["Sectors"],
)


@router.post(
    "/",
    response_model=SectorRead,
    status_code=status.HTTP_201_CREATED,
)
def create_sector(
    data: SectorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:

    service = SectorService(db)

    try:
        sector = service.create_sector(data)
        db.commit()

        return sector

    except SectorAlreadyExistsError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Os dados informados violam uma regra de integridade do banco.",
        ) from exc


@router.get(
    "/",
    response_model=list[SectorRead],
)
def list_sectors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list:

    return SectorService(db).get_sectors()


@router.get(
    "/{sector_id}",
    response_model=SectorRead,
)
def get_sector(
    sector_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:

    sector = SectorService(db).get_sector(sector_id)

    if sector is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setor nao encontrado.",
        )

    return sector


@router.patch(
    "/{sector_id}",
    response_model=SectorRead,
)
def update_sector(
    sector_id: int,
    data: SectorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:

    service = SectorService(db)

    sector = service.get_sector(sector_id)

    if sector is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setor nao encontrado.",
        )

    try:
        updated_sector = service.update_sector(
            sector=sector,
            data=data,
        )

        db.commit()

        return updated_sector

    except SectorAlreadyExistsError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Os dados informados violam uma regra de integridade do banco.",
        ) from exc


@router.delete(
    "/{sector_id}",
    response_model=SectorRead,
)
def deactivate_sector(
    sector_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:

    service = SectorService(db)

    sector = service.get_sector(sector_id)

    if sector is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setor nao encontrado.",
        )

    deactivated_sector = service.deactivate_sector(sector)

    db.commit()

    return deactivated_sector