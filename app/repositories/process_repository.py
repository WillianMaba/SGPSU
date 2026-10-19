from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.process import Process


class ProcessRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        process_id: int,
    ) -> Process | None:

        return self.db.get(
            Process,
            process_id,
        )

    def list_all(self) -> list[Process]:

        statement = (
            select(Process)
            .order_by(Process.id.desc())
        )

        return list(
            self.db.scalars(statement).all()
        )

    def list_visible_to_user(
        self,
        user_id: int,
    ) -> list[Process]:

        statement = (
            select(Process)
            .where(
                or_(
                    Process.created_by_id == user_id,
                    Process.responsible_id == user_id,
                )
            )
            .order_by(Process.id.desc())
        )

        return list(
            self.db.scalars(statement).all()
        )

    def create(
        self,
        process: Process,
    ) -> Process:

        self.db.add(process)
        self.db.flush()
        self.db.refresh(process)

        return process

    def update(
        self,
        process: Process,
        values: dict,
    ) -> Process:

        for field, value in values.items():
            setattr(process, field, value)

        self.db.add(process)
        self.db.flush()
        self.db.refresh(process)

        return process