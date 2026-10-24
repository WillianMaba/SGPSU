
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.process_stage import ProcessStage
from app.models.process_stage_history import ProcessStageHistory


class ProcessStageRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        process_id: int,
        stage_id: int,
    ) -> ProcessStage | None:

        statement = (
            select(ProcessStage)
            .where(
                ProcessStage.id == stage_id,
                ProcessStage.process_id == process_id,
            )
        )

        return self.db.scalar(statement)

    def get_by_sequence(
        self,
        process_id: int,
        sequence: int,
    ) -> ProcessStage | None:

        statement = (
            select(ProcessStage)
            .where(
                ProcessStage.process_id == process_id,
                ProcessStage.sequence == sequence,
            )
        )

        return self.db.scalar(statement)

    def list_by_process(
        self,
        process_id: int,
    ) -> list[ProcessStage]:

        statement = (
            select(ProcessStage)
            .where(
                ProcessStage.process_id == process_id
            )
            .order_by(
                ProcessStage.sequence.asc(),
                ProcessStage.id.asc(),
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    def create(
        self,
        stage: ProcessStage,
    ) -> ProcessStage:

        self.db.add(stage)
        self.db.flush()
        self.db.refresh(stage)

        return stage

    def update(
        self,
        stage: ProcessStage,
        values: dict,
    ) -> ProcessStage:

        for field, value in values.items():
            setattr(stage, field, value)

        self.db.add(stage)
        self.db.flush()
        self.db.refresh(stage)

        return stage

    def add_history(
        self,
        history: ProcessStageHistory,
    ) -> ProcessStageHistory:

        self.db.add(history)
        self.db.flush()
        self.db.refresh(history)

        return history

    def list_history(
        self,
        stage_id: int,
    ) -> list[ProcessStageHistory]:

        statement = (
            select(ProcessStageHistory)
            .where(
                ProcessStageHistory.process_stage_id == stage_id
            )
            .order_by(
                ProcessStageHistory.created_at.asc(),
                ProcessStageHistory.id.asc(),
            )
        )

        return list(
            self.db.scalars(statement).all()
        )
