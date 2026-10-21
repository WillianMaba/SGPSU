from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.process_progress import ProcessProgress


class ProcessProgressRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        progress: ProcessProgress,
    ) -> ProcessProgress:

        self.db.add(progress)
        self.db.flush()
        self.db.refresh(progress)

        return progress

    def list_by_process(
        self,
        process_id: int,
    ) -> list[ProcessProgress]:

        statement = (
            select(ProcessProgress)
            .where(
                ProcessProgress.process_id == process_id
            )
            .order_by(
                ProcessProgress.created_at.asc(),
                ProcessProgress.id.asc(),
            )
        )

        return list(
            self.db.scalars(statement).all()
        )