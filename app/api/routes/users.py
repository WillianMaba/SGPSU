from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.authorization import require_permission
from app.core.permissions import PermissionNames
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.core.authorization import require_permission
from app.core.permissions import PermissionNames
from app.services.user_service import (
    UserAlreadyExistsError,
    UserService,
)


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post(
    "/",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            PermissionNames.USERS_CREATE
        )
    ),
) -> User:

    service = UserService(db)

    try:
        user = service.create_user(data)
        db.commit()

        return user

    except UserAlreadyExistsError as exc:
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
    response_model=list[UserRead],
)
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PermissionNames.USERS_READ)
    ),
) -> list[User]:

    return UserService(db).get_users()


@router.get(
    "/{user_id}",
    response_model=UserRead,
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PermissionNames.USERS_READ)
    ),
) -> User:

    user = UserService(db).get_user(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario nao encontrado.",
        )

    return user


@router.patch(
    "/{user_id}",
    response_model=UserRead,
)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PermissionNames.USERS_UPDATE)
    ),
) -> User:

    service = UserService(db)

    user = service.get_user(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario nao encontrado.",
        )

    try:
        updated_user = service.update_user(
            user=user,
            data=data,
        )

        db.commit()

        return updated_user

    except UserAlreadyExistsError as exc:
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
    "/{user_id}",
    response_model=UserRead,
)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PermissionNames.USERS_DELETE)
    ),
) -> User:

    service = UserService(db)

    user = service.get_user(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario nao encontrado.",
        )

    deactivated_user = service.deactivate_user(user)

    db.commit()

    return deactivated_user