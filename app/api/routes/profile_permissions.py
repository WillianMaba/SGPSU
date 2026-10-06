from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.authorization import require_permission
from app.core.permissions import PermissionNames
from app.db.session import get_db
from app.models.user import User
from app.schemas.permission import PermissionRead
from app.schemas.profile_permission import ProfilePermissionRead
from app.services.profile_permission_service import (
    PermissionNotFoundError,
    ProfileNotFoundError,
    ProfilePermissionService,
)


router = APIRouter(
    prefix="/profiles",
    tags=["Profile Permissions"],
)


@router.get(
    "/{profile_id}/permissions",
    response_model=list[PermissionRead],
)
def list_profile_permissions(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            PermissionNames.PROFILE_PERMISSIONS_READ
        )
    ),
) -> list:

    service = ProfilePermissionService(db)

    try:
        return service.list_permissions(profile_id)

    except ProfileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/{profile_id}/permissions/{permission_id}",
    response_model=ProfilePermissionRead,
    status_code=status.HTTP_201_CREATED,
)
def add_profile_permission(
    profile_id: int,
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            PermissionNames.PROFILE_PERMISSIONS_MANAGE
        )
    ),
) -> ProfilePermissionRead:

    service = ProfilePermissionService(db)

    try:
        profile_permission = service.add_permission(
            profile_id=profile_id,
            permission_id=permission_id,
        )

        db.commit()

        return profile_permission

    except ProfileNotFoundError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except PermissionNotFoundError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{profile_id}/permissions/{permission_id}",
    response_model=ProfilePermissionRead,
)
def remove_profile_permission(
    profile_id: int,
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            PermissionNames.PROFILE_PERMISSIONS_MANAGE
        )
    ),
) -> ProfilePermissionRead:

    service = ProfilePermissionService(db)

    try:
        profile_permission = service.remove_permission(
            profile_id=profile_id,
            permission_id=permission_id,
        )

        db.commit()

        return profile_permission

    except PermissionNotFoundError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc