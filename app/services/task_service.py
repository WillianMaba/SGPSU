
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.user import User

from app.repositories.task_repository import TaskRepository

from app.schemas.task import TaskCreate, TaskUpdate

class TaskNotFoundError(Exception):
    pass

class TaskReferenceError(Exception):
    pass

class TaskInvalidUpdateError(Exception):
    pass

class TaskInvalidTransitionError(Exception):
    pass

class TaskService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = TaskRepository(db)

    # ========================================================
    # VALIDAR RESPONSAVEL
    # ========================================================

    def _validate_assignee(
        self,
        assigned_to_id: int | None,
    ) -> None:

        if assigned_to_id is None:
            return

        user = self.db.get(
            User,
            assigned_to_id,
        )

        if user is None or not user.is_active:
            raise TaskReferenceError(
                "Responsavel nao encontrado ou inativo."
            )

    # ========================================================
    # LOCALIZAR TAREFA
    # ========================================================

    def _get_task(
        self,
        process_id: int,
        task_id: int,
    ) -> Task:

        task = self.repository.get_by_id(
            process_id=process_id,
            task_id=task_id,
        )

        if task is None:
            raise TaskNotFoundError(
                "Tarefa nao encontrada neste processo."
            )

        return task

    # ========================================================
    # CRIAR TAREFA
    # ========================================================

    def create_task(
        self,
        process_id: int,
        data: TaskCreate,
    ) -> Task:

        self._validate_assignee(
            data.assigned_to_id,
        )

        task = Task(
            process_id=process_id,
            title=data.title,
            description=data.description,
            assigned_to_id=data.assigned_to_id,
            due_at=data.due_at,
            is_completed=False,
        )

        return self.repository.create(task)

    # ========================================================
    # CONSULTAR TAREFAS
    # ========================================================

    def get_task(
        self,
        process_id: int,
        task_id: int,
    ) -> Task:

        return self._get_task(
            process_id=process_id,
            task_id=task_id,
        )

    def list_tasks(
        self,
        process_id: int,
    ) -> list[Task]:

        return self.repository.list_by_process(
            process_id=process_id,
        )

    # ========================================================
    # ATUALIZAR TAREFA
    # ========================================================

    def update_task(
        self,
        process_id: int,
        task_id: int,
        data: TaskUpdate,
    ) -> Task:

        task = self._get_task(
            process_id=process_id,
            task_id=task_id,
        )

        if task.is_completed:
            raise TaskInvalidUpdateError(
                "Nao e permitido editar uma tarefa concluida."
            )

        values = data.model_dump(
            exclude_unset=True,
        )

        if not values:
            return task

        if "title" in values and values["title"] is None:
            raise TaskInvalidUpdateError(
                "O titulo nao pode ser nulo."
            )

        if "assigned_to_id" in values:
            self._validate_assignee(
                values["assigned_to_id"],
            )

        changed_values = {
            field: value
            for field, value in values.items()
            if getattr(task, field) != value
        }

        if not changed_values:
            return task

        return self.repository.update(
            task=task,
            values=changed_values,
        )

    # ========================================================
    # CONCLUIR TAREFA
    # ========================================================

    def complete_task(
        self,
        process_id: int,
        task_id: int,
    ) -> Task:

        task = self._get_task(
            process_id=process_id,
            task_id=task_id,
        )

        if task.is_completed:
            raise TaskInvalidTransitionError(
                "Esta tarefa ja esta concluida."
            )

        return self.repository.update(
            task=task,
            values={
                "is_completed": True,
                "completed_at": datetime.now(timezone.utc),
            },
        )

    # ========================================================
    # REABRIR TAREFA
    # ========================================================

    def reopen_task(
        self,
        process_id: int,
        task_id: int,
    ) -> Task:

        task = self._get_task(
            process_id=process_id,
            task_id=task_id,
        )

        if not task.is_completed:
            raise TaskInvalidTransitionError(
                "Somente tarefas concluidas podem ser reabertas."
            )

        return self.repository.update(
            task=task,
            values={
                "is_completed": False,
                "completed_at": None,
            },
        )