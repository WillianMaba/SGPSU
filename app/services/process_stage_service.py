
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.process_stage import ProcessStage
from app.models.process_stage_history import ProcessStageHistory
from app.models.user import User

from app.repositories.process_stage_repository import (
    ProcessStageRepository,
)

from app.schemas.process_stage import (
    ProcessStageCreate,
    ProcessStageUpdate,
)


class ProcessStageNotFoundError(Exception):
    pass


class ProcessStageReferenceError(Exception):
    pass


class ProcessStageSequenceError(Exception):
    pass


class ProcessStageInvalidUpdateError(Exception):
    pass


class ProcessStageInvalidTransitionError(Exception):
    pass


class ProcessStageService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = ProcessStageRepository(db)

    # ========================================================
    # VALIDACOES INTERNAS
    # ========================================================

    def _validate_responsible(
        self,
        responsible_id: int | None,
    ) -> None:

        if responsible_id is None:
            return

        responsible = self.db.get(
            User,
            responsible_id,
        )

        if responsible is None or not responsible.is_active:
            raise ProcessStageReferenceError(
                "Responsavel nao encontrado ou inativo."
            )

    def _validate_sequence(
        self,
        process_id: int,
        sequence: int,
        current_stage_id: int | None = None,
    ) -> None:

        existing = self.repository.get_by_sequence(
            process_id=process_id,
            sequence=sequence,
        )

        if existing is None:
            return

        if existing.id == current_stage_id:
            return

        raise ProcessStageSequenceError(
            "Ja existe uma etapa com esta sequencia neste processo."
        )

    def _get_stage(
        self,
        process_id: int,
        stage_id: int,
    ) -> ProcessStage:

        stage = self.repository.get_by_id(
            process_id=process_id,
            stage_id=stage_id,
        )

        if stage is None:
            raise ProcessStageNotFoundError(
                "Etapa nao encontrada neste processo."
            )

        return stage

    def _register_history(
        self,
        stage_id: int,
        user_id: int,
        action: str,
        description: str | None = None,
    ) -> ProcessStageHistory:

        history = ProcessStageHistory(
            process_stage_id=stage_id,
            user_id=user_id,
            action=action,
            description=description,
        )

        return self.repository.add_history(history)

    # ========================================================
    # CRIAR ETAPA
    # ========================================================

    def create_stage(
        self,
        process_id: int,
        user_id: int,
        data: ProcessStageCreate,
    ) -> ProcessStage:

        self._validate_sequence(
            process_id=process_id,
            sequence=data.sequence,
        )

        self._validate_responsible(
            data.responsible_id,
        )

        stage = ProcessStage(
            process_id=process_id,
            name=data.name,
            description=data.description,
            sequence=data.sequence,
            responsible_id=data.responsible_id,
            is_completed=False,
        )

        stage = self.repository.create(stage)

        self._register_history(
            stage_id=stage.id,
            user_id=user_id,
            action="created",
            description="Etapa criada.",
        )

        return stage

    # ========================================================
    # CONSULTAR ETAPAS
    # ========================================================

    def get_stage(
        self,
        process_id: int,
        stage_id: int,
    ) -> ProcessStage:

        return self._get_stage(
            process_id=process_id,
            stage_id=stage_id,
        )

    def list_stages(
        self,
        process_id: int,
    ) -> list[ProcessStage]:

        return self.repository.list_by_process(
            process_id=process_id,
        )

    # ========================================================
    # ATUALIZAR ETAPA
    # ========================================================

    def update_stage(
        self,
        process_id: int,
        stage_id: int,
        user_id: int,
        data: ProcessStageUpdate,
    ) -> ProcessStage:

        stage = self._get_stage(
            process_id=process_id,
            stage_id=stage_id,
        )

        values = data.model_dump(
            exclude_unset=True,
        )

        if not values:
            return stage

        for field in ("name", "sequence"):
            if field in values and values[field] is None:
                raise ProcessStageInvalidUpdateError(
                    f"O campo {field} nao pode ser nulo."
                )

        if "sequence" in values:
            self._validate_sequence(
                process_id=process_id,
                sequence=values["sequence"],
                current_stage_id=stage.id,
            )

        if "responsible_id" in values:
            self._validate_responsible(
                values["responsible_id"],
            )

        changed_values = {
            field: value
            for field, value in values.items()
            if getattr(stage, field) != value
        }

        if not changed_values:
            return stage

        stage = self.repository.update(
            stage=stage,
            values=changed_values,
        )

        changed_fields = ", ".join(
            sorted(changed_values.keys())
        )

        self._register_history(
            stage_id=stage.id,
            user_id=user_id,
            action="updated",
            description=(
                f"Campos atualizados: {changed_fields}."
            ),
        )

        return stage

    # ========================================================
    # INICIAR ETAPA
    # ========================================================

    def start_stage(
        self,
        process_id: int,
        stage_id: int,
        user_id: int,
    ) -> ProcessStage:

        stage = self._get_stage(
            process_id=process_id,
            stage_id=stage_id,
        )

        if stage.is_completed:
            raise ProcessStageInvalidTransitionError(
                "Uma etapa concluida nao pode ser iniciada novamente."
            )

        if stage.started_at is not None:
            raise ProcessStageInvalidTransitionError(
                "Esta etapa ja foi iniciada."
            )

        stage = self.repository.update(
            stage=stage,
            values={
                "started_at": datetime.now(timezone.utc),
            },
        )

        self._register_history(
            stage_id=stage.id,
            user_id=user_id,
            action="started",
            description="Etapa iniciada.",
        )

        return stage

    # ========================================================
    # CONCLUIR ETAPA
    # ========================================================

    def complete_stage(
        self,
        process_id: int,
        stage_id: int,
        user_id: int,
    ) -> ProcessStage:

        stage = self._get_stage(
            process_id=process_id,
            stage_id=stage_id,
        )

        if stage.is_completed:
            raise ProcessStageInvalidTransitionError(
                "Esta etapa ja esta concluida."
            )

        if stage.started_at is None:
            raise ProcessStageInvalidTransitionError(
                "A etapa precisa ser iniciada antes da conclusao."
            )

        stage = self.repository.update(
            stage=stage,
            values={
                "is_completed": True,
                "completed_at": datetime.now(timezone.utc),
            },
        )

        self._register_history(
            stage_id=stage.id,
            user_id=user_id,
            action="completed",
            description="Etapa concluida.",
        )

        return stage

    # ========================================================
    # CONSULTAR HISTORICO
    # ========================================================

    def list_history(
        self,
        process_id: int,
        stage_id: int,
    ) -> list[ProcessStageHistory]:

        stage = self._get_stage(
            process_id=process_id,
            stage_id=stage_id,
        )

        return self.repository.list_history(
            stage_id=stage.id,
        )
