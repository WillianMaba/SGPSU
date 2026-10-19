from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.process import Process
from app.models.process_status import ProcessStatus
from app.models.process_type import ProcessType
from app.models.user import User

from app.repositories.process_repository import ProcessRepository
from app.schemas.process import ProcessCreate, ProcessUpdate


class ProcessReferenceError(Exception):
    pass


class ProcessInitialStatusError(Exception):
    pass


class ProcessInvalidUpdateError(Exception):
    pass


class ProcessService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = ProcessRepository(db)

    def _validate_type(
        self,
        process_type_id: int,
    ) -> None:

        process_type = self.db.get(
            ProcessType,
            process_type_id,
        )

        if process_type is None or not process_type.is_active:
            raise ProcessReferenceError(
                "Tipo de processo nao encontrado ou inativo."
            )

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
            raise ProcessReferenceError(
                "Responsavel nao encontrado ou inativo."
            )

    def create_process(
        self,
        data: ProcessCreate,
        created_by_id: int,
    ) -> Process:

        self._validate_type(
            data.process_type_id,
        )

        self._validate_responsible(
            data.responsible_id,
        )

        statement = select(ProcessStatus).where(
            ProcessStatus.name == "Aberto",
            ProcessStatus.is_active.is_(True),
        )

        initial_status = self.db.scalar(statement)

        if initial_status is None:
            raise ProcessInitialStatusError(
                "O status inicial Aberto nao esta cadastrado ou ativo."
            )

        # PRC- + 20 caracteres hexadecimais = 24 caracteres.
        protocol = f"PRC-{uuid4().hex[:20].upper()}"

        process = Process(
            protocol=protocol,
            title=data.title.strip(),
            description=data.description,
            process_type_id=data.process_type_id,
            status_id=initial_status.id,
            created_by_id=created_by_id,
            responsible_id=data.responsible_id,
        )

        return self.repository.create(process)

    def get_process(
        self,
        process_id: int,
    ) -> Process | None:

        return self.repository.get_by_id(process_id)

    def get_processes(self) -> list[Process]:

        return self.repository.list_all()

    def get_visible_processes(
        self,
        user_id: int,
    ) -> list[Process]:

        return self.repository.list_visible_to_user(user_id)

    def update_process(
        self,
        process: Process,
        data: ProcessUpdate,
    ) -> Process:

        values = data.model_dump(
            exclude_unset=True,
        )

        if not values:
            return process

        required_fields = (
            "title",
            "process_type_id",
        )

        for field in required_fields:
            if field in values and values[field] is None:
                raise ProcessInvalidUpdateError(
                    f"O campo {field} nao pode ser nulo."
                )

        if "title" in values:
            values["title"] = values["title"].strip()

            if len(values["title"]) < 3:
                raise ProcessInvalidUpdateError(
                    "O titulo deve possuir pelo menos 3 caracteres validos."
                )

        if "process_type_id" in values:
            self._validate_type(
                values["process_type_id"],
            )

        if "responsible_id" in values:
            self._validate_responsible(
                values["responsible_id"],
            )

        changed_values = {
            field: value
            for field, value in values.items()
            if getattr(process, field) != value
        }

        if not changed_values:
            return process

        return self.repository.update(
            process=process,
            values=changed_values,
        )