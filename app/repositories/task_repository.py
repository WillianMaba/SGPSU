
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.task import Task

class TaskRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        process_id: int,
        task_id: int,
    ) -> Task | None:

        statement = (
            select(Task)
            .where(
                Task.id == task_id,
                Task.process_id == process_id,
            )
        )

        return self.db.scalar(statement)

    def list_by_process(
        self,
        process_id: int,
    ) -> list[Task]:

        statement = (
            select(Task)
            .where(Task.process_id == process_id)
            .order_by(
                Task.created_at.asc(),
                Task.id.asc(),
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    def create(
        self,
        task: Task,
    ) -> Task:

        self.db.add(task)
        self.db.flush()
        self.db.refresh(task)

        return task

    def update(
        self,
        task: Task,
        values: dict,
    ) -> Task:

        for field, value in values.items():
            setattr(task, field, value)

        self.db.add(task)
        self.db.flush()
        self.db.refresh(task)

        return task