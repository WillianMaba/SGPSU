from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.ticket import Ticket
from app.schemas.ticket import TicketCreate, TicketUpdate


class TicketRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, ticket_id: int) -> Ticket | None:
        statement = select(Ticket).where(
            Ticket.id == ticket_id,
        )

        return self.db.scalar(statement)

    def list(self) -> list[Ticket]:
        statement = select(Ticket).order_by(
            Ticket.id.desc(),
        )

        return list(
            self.db.scalars(statement).all()
        )

    def create(
        self,
        data: TicketCreate,
        requester_id: int,
    ) -> Ticket:

        ticket = Ticket(
            title=data.title,
            description=data.description,
            status_id=data.status_id,
            priority_id=data.priority_id,
            category_id=data.category_id,
            requester_id=requester_id,
            assignee_id=data.assignee_id,
        )

        self.db.add(ticket)
        self.db.flush()
        self.db.refresh(ticket)

        return ticket

    def update(
        self,
        ticket: Ticket,
        data: TicketUpdate,
    ) -> Ticket:

        values = data.model_dump(
            exclude_unset=True,
        )

        for field, value in values.items():
            setattr(ticket, field, value)

        self.db.add(ticket)
        self.db.flush()
        self.db.refresh(ticket)

        return ticket