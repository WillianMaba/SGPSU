from sqlalchemy.orm import Session
from app.models.ticket import Ticket
from app.models.ticket_comment import TicketComment
from app.repositories.ticket_comment_repository import (
    TicketCommentRepository,
)
from app.repositories.ticket_history_repository import (
    TicketHistoryRepository,
)


class TicketNotFoundError(Exception):
    pass


class InvalidTicketCommentError(Exception):
    pass


class TicketCommentService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = TicketCommentRepository(db)
        self.history_repository = TicketHistoryRepository(db)

    def list_comments(
        self,
        ticket_id: int,
    ) -> list[TicketComment]:
        ticket = self.db.get(Ticket, ticket_id)

        if ticket is None:
            raise TicketNotFoundError(
                "Chamado nao encontrado."
            )

        return self.repository.list_by_ticket(ticket_id)

    def add_comment(
        self,
        ticket_id: int,
        user_id: int,
        content: str,
    ) -> TicketComment:
        ticket = self.db.get(Ticket, ticket_id)

        if ticket is None:
            raise TicketNotFoundError(
                "Chamado nao encontrado."
            )

        cleaned_content = content.strip()

        if not cleaned_content:
            raise InvalidTicketCommentError(
                "O comentario nao pode estar vazio."
            )

        comment = self.repository.create(
            ticket_id=ticket_id,
            user_id=user_id,
            content=cleaned_content,
        )

        self.history_repository.create(
            ticket_id=ticket_id,
            user_id=user_id,
            action="comment_added",
            description="Comentario adicionado ao chamado.",
        )

        return comment