from sqlalchemy.orm import Session
from app.models.ticket import Ticket
from app.models.ticket_category import TicketCategory
from app.models.ticket_priority import TicketPriority
from app.models.ticket_status import TicketStatus
from app.models.user import User
from app.repositories.ticket_repository import TicketRepository
from app.schemas.ticket import TicketCreate, TicketUpdate


class TicketReferenceNotFoundError(Exception):
    pass


class TicketService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = TicketRepository(db)

    def _validate_references(
        self,
        status_id: int,
        priority_id: int,
        category_id: int,
        assignee_id: int | None,
    ) -> None:

        status = self.db.get(
            TicketStatus,
            status_id,
        )

        if status is None or not status.is_active:
            raise TicketReferenceNotFoundError(
                "Status do chamado nao encontrado ou inativo."
            )

        priority = self.db.get(
            TicketPriority,
            priority_id,
        )

        if priority is None or not priority.is_active:
            raise TicketReferenceNotFoundError(
                "Prioridade do chamado nao encontrada ou inativa."
            )

        category = self.db.get(
            TicketCategory,
            category_id,
        )

        if category is None or not category.is_active:
            raise TicketReferenceNotFoundError(
                "Categoria do chamado nao encontrada ou inativa."
            )

        if assignee_id is not None:
            assignee = self.db.get(
                User,
                assignee_id,
            )

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

        return self.repository.create(
            data=data,
            requester_id=requester_id,
        )

    def get_ticket(
        self,
        ticket_id: int,
    ) -> Ticket | None:

        return self.repository.get_by_id(ticket_id)

    def get_tickets(self) -> list[Ticket]:
        return self.repository.list()

    def update_ticket(
        self,
        ticket: Ticket,
        data: TicketUpdate,
    ) -> Ticket:

        status_id = (
            data.status_id
            if data.status_id is not None
            else ticket.status_id
        )

        priority_id = (
            data.priority_id
            if data.priority_id is not None
            else ticket.priority_id
        )

        category_id = (
            data.category_id
            if data.category_id is not None
            else ticket.category_id
        )

        assignee_id = (
            data.assignee_id
            if "assignee_id" in data.model_dump(
                exclude_unset=True,
            )
            else ticket.assignee_id
        )

        self._validate_references(
            status_id=status_id,
            priority_id=priority_id,
            category_id=category_id,
            assignee_id=assignee_id,
        )

        return self.repository.update(
            ticket=ticket,
            data=data,
        )