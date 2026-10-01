from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.api.routes.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.profile import ProfileCreate, ProfileRead, ProfileUpdate
from app.services.profile_service import (
    ProfileAlreadyExistsError,
    ProfileService,
)


router = APIRouter(
    prefix="/profiles",
    tags=["Profiles"],
)


@router.post(
    "/",
    response_model=ProfileRead,
    status_code=status.HTTP_201_CREATED,
)
def create_profile(
    data: ProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:

    service = ProfileService(db)

    try:
        profile = service.create_profile(data)
        db.commit()

        return profile

    except ProfileAlreadyExistsError as exc:
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
    response_model=list[ProfileRead],
)
def list_profiles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list:

    return ProfileService(db).get_profiles()


@router.get(
    "/{profile_id}",
    response_model=ProfileRead,
)
def get_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:

    profile = ProfileService(db).get_profile(profile_id)

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil nao encontrado.",
        )

    return profile


@router.patch(
    "/{profile_id}",
    response_model=ProfileRead,
)
def update_profile(
    profile_id: int,
    data: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:

    service = ProfileService(db)

    profile = service.get_profile(profile_id)

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil nao encontrado.",
        )

    try:
        updated_profile = service.update_profile(
            profile=profile,
            data=data,
        )

        db.commit()

        return updated_profile

    except ProfileAlreadyExistsError as exc:
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
    "/{profile_id}",
    response_model=ProfileRead,
)
def deactivate_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:

    service = ProfileService(db)

    profile = service.get_profile(profile_id)

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil nao encontrado.",
        )

    deactivated_profile = service.deactivate_profile(profile)

    db.commit()

    return deactivated_profile