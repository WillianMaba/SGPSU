from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.ticket_history import TicketHistory


class TicketHistoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_ticket(
        self,
        ticket_id: int,
    ) -> list[TicketHistory]:
        statement = (
            select(TicketHistory)
            .where(TicketHistory.ticket_id == ticket_id)
            .order_by(TicketHistory.id.desc())
        )

        return list(self.db.scalars(statement).all())

    def create(
        self,
        ticket_id: int,
        user_id: int,
        action: str,
        description: str | None = None,
    ) -> TicketHistory:
        history = TicketHistory(
            ticket_id=ticket_id,
            user_id=user_id,
            action=action,
            description=description,
        )

        self.db.add(history)
        self.db.flush()
        self.db.refresh(history)

        return history