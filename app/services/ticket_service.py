from sqlalchemy.orm import Session
from app.models.ticket import Ticket
from app.models.ticket_category import TicketCategory
from app.models.ticket_history import TicketHistory
from app.models.ticket_priority import TicketPriority
from app.models.ticket_status import TicketStatus
from app.models.user import User
from app.repositories.ticket_repository import TicketRepository
from app.repositories.ticket_history_repository import (
    TicketHistoryRepository,
)
from app.schemas.ticket import TicketCreate, TicketUpdate


class TicketReferenceNotFoundError(Exception):
    pass


class TicketInvalidUpdateError(Exception):
    pass


class TicketService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = TicketRepository(db)
        self.history_repository = TicketHistoryRepository(db)

    def _validate_references(
        self,
        status_id: int,
        priority_id: int,
        category_id: int,
        assignee_id: int | None,
    ) -> None:
        status = self.db.get(TicketStatus, status_id)
        if status is None or not status.is_active:
            raise TicketReferenceNotFoundError(
                "Status do chamado nao encontrado ou inativo."
            )

        priority = self.db.get(TicketPriority, priority_id)
        if priority is None or not priority.is_active:
            raise TicketReferenceNotFoundError(
                "Prioridade do chamado nao encontrada ou inativa."
            )

        category = self.db.get(TicketCategory, category_id)
        if category is None or not category.is_active:
            raise TicketReferenceNotFoundError(
                "Categoria do chamado nao encontrada ou inativa."
            )

        if assignee_id is not None:
            assignee = self.db.get(User, assignee_id)
            if assignee is None or not assignee.is_active:
                raise TicketReferenceNotFoundError(
                    "Responsavel pelo chamado nao encontrado ou inativo."
                )

    def create_ticket(
        self,
        data: TicketCreate,
        requester_id: int,
    ) -> Ticket:
        self._validate_references(
            status_id=data.status_id,
            priority_id=data.priority_id,
            category_id=data.category_id,
            assignee_id=data.assignee_id,
        )

        ticket = self.repository.create(
            data=data,
            requester_id=requester_id,
        )

        self.history_repository.create(
            ticket_id=ticket.id,
            user_id=requester_id,
            action="created",
            description="Chamado criado.",
        )

        return ticket

    def get_ticket(self, ticket_id: int) -> Ticket | None:
        return self.repository.get_by_id(ticket_id)

    def get_tickets(self) -> list[Ticket]:
        return self.repository.list()

    def update_ticket(
        self,
        ticket: Ticket,
        data: TicketUpdate,
        changed_by_id: int,
    ) -> Ticket:
        values = data.model_dump(exclude_unset=True)

        if not values:
            return ticket

        required_fields = (
            "title",
            "description",
            "status_id",
            "priority_id",
            "category_id",
        )

        for field in required_fields:
            if field in values and values[field] is None:
                raise TicketInvalidUpdateError(
                    f"O campo {field} nao pode ser nulo."
                )

        reference_models = {
            "status_id": (TicketStatus, "Status"),
            "priority_id": (TicketPriority, "Prioridade"),
            "category_id": (TicketCategory, "Categoria"),
        }

        for field, (model, label) in reference_models.items():
            if field in values:
                reference = self.db.get(model, values[field])

                if reference is None or not reference.is_active:
                    raise TicketReferenceNotFoundError(
                        f"{label} do chamado nao encontrado ou inativo."
                    )

        if "assignee_id" in values and values["assignee_id"] is not None:
            assignee = self.db.get(User, values["assignee_id"])

            if assignee is None or not assignee.is_active:
                raise TicketReferenceNotFoundError(
                    "Responsavel pelo chamado nao encontrado ou inativo."
                )

        labels = {
            "title": "titulo",
            "description": "descricao",
            "status_id": "status",
            "priority_id": "prioridade",
            "category_id": "categoria",
            "assignee_id": "responsavel",
        }

        changed_fields = [
            field
            for field, value in values.items()
            if getattr(ticket, field) != value
        ]

        if not changed_fields:
            return ticket

        updated_ticket = self.repository.update(
            ticket=ticket,
            data=data,
        )

        is_assignment_only = changed_fields == ["assignee_id"]

        description = "Campos alterados: " + ", ".join(
            labels[field] for field in changed_fields
        ) + "."

        self.history_repository.create(
            ticket_id=ticket.id,
            user_id=changed_by_id,
            action="assigned" if is_assignment_only else "updated",
            description=description,
        )

        return updated_ticket