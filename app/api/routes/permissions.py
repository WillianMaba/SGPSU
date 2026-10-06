from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.authorization import require_permission
from app.core.permissions import PermissionNames
from app.db.session import get_db
from app.models.user import User
from app.schemas.permission import (
    PermissionCreate,
    PermissionRead,
    PermissionUpdate,
)
from app.services.permission_service import (
    PermissionAlreadyExistsError,
    PermissionService,
)


router = APIRouter(
    prefix="/permissions",
    tags=["Permissions"],
)


@router.post(
    "/",
    response_model=PermissionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_permission(
    data: PermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            PermissionNames.PERMISSIONS_CREATE
        )
    ),
) -> PermissionRead:

    service = PermissionService(db)

    try:
        permission = service.create_permission(data)
        db.commit()

        return permission

    except PermissionAlreadyExistsError as exc:
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
    response_model=list[PermissionRead],
)
def list_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            PermissionNames.PERMISSIONS_READ
        )
    ),
) -> list[Permission]:

    return PermissionService(db).get_permissions()


@router.get(
    "/{permission_id}",
    response_model=PermissionRead,
)
def get_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            PermissionNames.PERMISSIONS_READ
        )
    ),
) -> Permission:

    permission = PermissionService(db).get_permission(
        permission_id,
    )

    if permission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permissao nao encontrada.",
        )

    return permission


@router.patch(
    "/{permission_id}",
    response_model=PermissionRead,
)
def update_permission(
    permission_id: int,
    data: PermissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            PermissionNames.PERMISSIONS_UPDATE
        )
    ),
) -> Permission:

    service = PermissionService(db)

    permission = service.get_permission(
        permission_id,
    )

    if permission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permissao nao encontrada.",
        )

    try:
        updated_permission = service.update_permission(
            permission=permission,
            data=data,
        )

        db.commit()

        return updated_permission

    except PermissionAlreadyExistsError as exc:
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
    "/{permission_id}",
    response_model=PermissionRead,
)
def deactivate_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            PermissionNames.PERMISSIONS_DELETE
        )
    ),
) -> Permission:

    service = PermissionService(db)

    permission = service.get_permission(
        permission_id,
    )

    if permission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permissao nao encontrada.",
        )

    deactivated_permission = service.deactivate_permission(
        permission,
    )

    db.commit()

    return deactivated_permission