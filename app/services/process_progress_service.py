from sqlalchemy.orm import Session

from app.models.process_progress import ProcessProgress
from app.repositories.process_progress_repository import (
    ProcessProgressRepository,
)
from app.schemas.process_progress import ProcessProgressCreate


class ProcessProgressService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = ProcessProgressRepository(db)

    def add_progress(
        self,
        process_id: int,
        user_id: int,
        data: ProcessProgressCreate,
    ) -> ProcessProgress:

        progress = ProcessProgress(
            process_id=process_id,
            user_id=user_id,
            description=data.description,
        )

        return self.repository.create(progress)

    def list_progress(
        self,
        process_id: int,
    ) -> list[ProcessProgress]:

        return self.repository.list_by_process(process_id)