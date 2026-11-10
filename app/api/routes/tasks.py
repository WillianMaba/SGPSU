
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.db.session import get_db
from app.models.user import User

from app.core.permissions import PermissionNames

from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskRead,
)

from app.services.authorization_service import AuthorizationService
from app.services.process_access_service import ProcessAccessService

from app.services.task_service import (
    TaskService,
    TaskNotFoundError,
    TaskReferenceError,
    TaskInvalidUpdateError,
    TaskInvalidTransitionError,
)

router = APIRouter(
    prefix="/processes",
    tags=["Tasks"],
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

def require_assignment_permission(
    db: Session,
    current_user: User,
) -> None:

    authorization = AuthorizationService(db)

    if not authorization.has_permission(
        current_user,
        PermissionNames.PROCESSES_ASSIGN,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario nao possui permissao para atribuir tarefas.",
        )

def handle_task_error(exc: Exception) -> HTTPException:

    if isinstance(exc, TaskNotFoundError):
        return HTTPException(
            status_code=404,
            detail=str(exc),
        )

    if isinstance(exc, TaskReferenceError):
        return HTTPException(
            status_code=400,
            detail=str(exc),
        )

    if isinstance(exc, TaskInvalidUpdateError):
        return HTTPException(
            status_code=422,
            detail=str(exc),
        )

    if isinstance(exc, TaskInvalidTransitionError):
        return HTTPException(
            status_code=409,
            detail=str(exc),
        )

    return HTTPException(
        status_code=500,
        detail="Erro interno ao processar a tarefa.",
    )

# ============================================================
# CRIAR TAREFA
# ============================================================

@router.post(
    "/{process_id}/tasks",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    process_id: int,
    data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    process = get_authorized_process(
        db,
        current_user,
        process_id,
        require_update=True,
    )

    if data.assigned_to_id is not None:
        require_assignment_permission(
            db,
            current_user,
        )

    try:
        task = TaskService(db).create_task(
            process_id=process.id,
            data=data,
        )

        db.commit()
        return task

    except TaskReferenceError as exc:
        db.rollback()
        raise handle_task_error(exc) from exc

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Conflito de integridade ao criar tarefa.",
        ) from exc

# ============================================================
# LISTAR TAREFAS
# ============================================================

@router.get(
    "/{process_id}/tasks",
    response_model=list[TaskRead],
)
def list_tasks(
    process_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    process = get_authorized_process(
        db,
        current_user,
        process_id,
    )

    return TaskService(db).list_tasks(
        process_id=process.id,
    )

# ============================================================
# CONSULTAR TAREFA
# ============================================================

@router.get(
    "/{process_id}/tasks/{task_id}",
    response_model=TaskRead,
)
def get_task(
    process_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    process = get_authorized_process(
        db,
        current_user,
        process_id,
    )

    try:
        return TaskService(db).get_task(
            process_id=process.id,
            task_id=task_id,
        )

    except TaskNotFoundError as exc:
        raise handle_task_error(exc) from exc

# ============================================================
# ATUALIZAR TAREFA
# ============================================================

@router.patch(
    "/{process_id}/tasks/{task_id}",
    response_model=TaskRead,
)
def update_task(
    process_id: int,
    task_id: int,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    process = get_authorized_process(
        db,
        current_user,
        process_id,
        require_update=True,
    )

    if "assigned_to_id" in data.model_fields_set:
        require_assignment_permission(
            db,
            current_user,
        )

    try:
        task = TaskService(db).update_task(
            process_id=process.id,
            task_id=task_id,
            data=data,
        )

        db.commit()
        return task

    except (
        TaskNotFoundError,
        TaskReferenceError,
        TaskInvalidUpdateError,
    ) as exc:
        db.rollback()
        raise handle_task_error(exc) from exc

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Conflito de integridade ao atualizar tarefa.",
        ) from exc

# ============================================================
# CONCLUIR TAREFA
# ============================================================

@router.post(
    "/{process_id}/tasks/{task_id}/complete",
    response_model=TaskRead,
)
def complete_task(
    process_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    process = get_authorized_process(
        db,
        current_user,
        process_id,
        require_update=True,
    )

    try:
        task = TaskService(db).complete_task(
            process_id=process.id,
            task_id=task_id,
        )

        db.commit()
        return task

    except (
        TaskNotFoundError,
        TaskInvalidTransitionError,
    ) as exc:
        db.rollback()
        raise handle_task_error(exc) from exc

# ============================================================
# REABRIR TAREFA
# ============================================================

@router.post(
    "/{process_id}/tasks/{task_id}/reopen",
    response_model=TaskRead,
)
def reopen_task(
    process_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    process = get_authorized_process(
        db,
        current_user,
        process_id,
        require_update=True,
    )

    try:
        task = TaskService(db).reopen_task(
            process_id=process.id,
            task_id=task_id,
        )

        db.commit()
        return task

    except (
        TaskNotFoundError,
        TaskInvalidTransitionError,
    ) as exc:
        db.rollback()
        raise handle_task_error(exc) from exc