from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.ticket_comment import TicketComment


class TicketCommentRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_ticket(
        self,
        ticket_id: int,
    ) -> list[TicketComment]:
        statement = (
            select(TicketComment)
            .where(TicketComment.ticket_id == ticket_id)
            .order_by(TicketComment.id.asc())
        )

        return list(self.db.scalars(statement).all())

    def create(
        self,
        ticket_id: int,
        user_id: int,
        content: str,
    ) -> TicketComment:
        comment = TicketComment(
            ticket_id=ticket_id,
            user_id=user_id,
            content=content,
        )

        self.db.add(comment)
        self.db.flush()
        self.db.refresh(comment)

        return comment