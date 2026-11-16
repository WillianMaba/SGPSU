from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.core.authorization import require_permission
from app.core.permissions import PermissionNames
from app.db.session import get_db

from app.models.repository_access import RepositoryAccess
from app.models.user import User

from app.schemas.repository import (
    RepositoryCreate,
    RepositoryRead,
    RepositoryUpdate,
)
from app.schemas.folder import (
    FolderCreate,
    FolderRead,
    FolderUpdate,
)

from app.services.repository_service import (
    RepositoryService,
    RepositoryNotFoundError,
    RepositoryInvalidUpdateError,
)
from app.services.folder_service import (
    FolderService,
    FolderNotFoundError,
    FolderReferenceError,
    FolderInvalidUpdateError,
)
from app.services.resource_access_service import ResourceAccessService


router = APIRouter(
    prefix="/repositories",
    tags=["Repositories and Folders"],
)


def require_acl(
    allowed: bool,
    detail: str,
) -> None:
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


# ============================================================
# REPOSITORIES
# ============================================================

@router.post(
    "/",
    response_model=RepositoryRead,
    status_code=status.HTTP_201_CREATED,
)
def create_repository(
    data: RepositoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PermissionNames.REPOSITORIES_CREATE)
    ),
):
    try:
        service = RepositoryService(db)
        repository = service.create(data)

        # O criador recebe administração direta do repositório.
        db.add(
            RepositoryAccess(
                repository_id=repository.id,
                user_id=current_user.id,
                profile_id=None,
                sector_id=None,
                permission="ADMIN",
                effect="ALLOW",
                is_active=True,
            )
        )

        db.commit()
        db.refresh(repository)

        return repository

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ja existe um repositorio com esses dados.",
        ) from exc


@router.get(
    "/",
    response_model=list[RepositoryRead],
)
def list_repositories(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PermissionNames.REPOSITORIES_READ)
    ),
):
    repositories = RepositoryService(db).list_active()
    access = ResourceAccessService(db)

    return [
        repository
        for repository in repositories
        if access.can_read(current_user, repository)
    ]


@router.get(
    "/{repository_id}",
    response_model=RepositoryRead,
)
def get_repository(
    repository_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PermissionNames.REPOSITORIES_READ)
    ),
):
    try:
        repository = RepositoryService(db).get(repository_id)

        require_acl(
            ResourceAccessService(db).can_read(
                current_user,
                repository,
            ),
            "Usuario nao possui acesso a este repositorio.",
        )

        return repository

    except RepositoryNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch(
    "/{repository_id}",
    response_model=RepositoryRead,
)
def update_repository(
    repository_id: int,
    data: RepositoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PermissionNames.REPOSITORIES_UPDATE)
    ),
):
    try:
        service = RepositoryService(db)
        repository = service.get(repository_id)

        require_acl(
            ResourceAccessService(db).can_modify(
                current_user,
                repository,
            ),
            "Usuario nao possui permissao de modificacao neste repositorio.",
        )

        updated = service.update(repository_id, data)
        db.commit()
        return updated

    except RepositoryNotFoundError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    except RepositoryInvalidUpdateError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Conflito ao atualizar o repositorio.",
        ) from exc


# ============================================================
# FOLDERS
# ============================================================

@router.post(
    "/{repository_id}/folders",
    response_model=FolderRead,
    status_code=status.HTTP_201_CREATED,
)
def create_folder(
    repository_id: int,
    data: FolderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PermissionNames.FOLDERS_CREATE)
    ),
):
    try:
        service = RepositoryService(db)
        repository = service.get(repository_id)
        access = ResourceAccessService(db)

        if data.parent_folder_id is None:
            allowed = access.can_write(current_user, repository)
        else:
            parent = FolderService(db).get(
                repository_id,
                data.parent_folder_id,
            )
            allowed = access.can_write(current_user, parent)

        require_acl(
            allowed,
            "Usuario nao possui permissao para criar pasta neste local.",
        )

        folder = FolderService(db).create(repository_id, data)
        db.commit()
        return folder

    except RepositoryNotFoundError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    except FolderNotFoundError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    except FolderReferenceError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ja existe uma pasta com esse nome neste local.",
        ) from exc


@router.get(
    "/{repository_id}/folders",
    response_model=list[FolderRead],
)
def list_folders(
    repository_id: int,
    parent_folder_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PermissionNames.FOLDERS_READ)
    ),
):
    try:
        repository = RepositoryService(db).get(repository_id)
        service = FolderService(db)
        access = ResourceAccessService(db)

        if parent_folder_id is None:
            require_acl(
                access.can_read(current_user, repository),
                "Usuario nao possui acesso a este repositorio.",
            )
        else:
            parent = service.get(repository_id, parent_folder_id)
            require_acl(
                access.can_read(current_user, parent),
                "Usuario nao possui acesso a esta pasta.",
            )

        folders = service.list_by_repository(
            repository_id,
            parent_folder_id,
        )

        return [
            folder
            for folder in folders
            if access.can_read(current_user, folder)
        ]

    except RepositoryNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    except FolderNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    except FolderReferenceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/{repository_id}/folders/{folder_id}",
    response_model=FolderRead,
)
def get_folder(
    repository_id: int,
    folder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PermissionNames.FOLDERS_READ)
    ),
):
    try:
        folder = FolderService(db).get(repository_id, folder_id)

        require_acl(
            ResourceAccessService(db).can_read(current_user, folder),
            "Usuario nao possui acesso a esta pasta.",
        )

        return folder

    except FolderNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch(
    "/{repository_id}/folders/{folder_id}",
    response_model=FolderRead,
)
def update_folder(
    repository_id: int,
    folder_id: int,
    data: FolderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PermissionNames.FOLDERS_UPDATE)
    ),
):
    try:
        service = FolderService(db)
        folder = service.get(repository_id, folder_id)
        access = ResourceAccessService(db)

        require_acl(
            access.can_modify(current_user, folder),
            "Usuario nao possui permissao para modificar esta pasta.",
        )

        # Mover uma pasta também exige escrita no destino.
        if "parent_folder_id" in data.model_fields_set:
            if data.parent_folder_id is None:
                destination = RepositoryService(db).get(repository_id)
            else:
                destination = service.get(
                    repository_id,
                    data.parent_folder_id,
                )

            require_acl(
                access.can_write(current_user, destination),
                "Usuario nao possui permissao para mover a pasta para este local.",
            )

        updated = service.update(repository_id, folder_id, data)
        db.commit()
        return updated

    except FolderNotFoundError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    except FolderReferenceError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    except FolderInvalidUpdateError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    except RepositoryNotFoundError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Conflito ao atualizar a pasta. Verifique se ja existe "
                "outra pasta com esse nome no destino.",
        ) from exc