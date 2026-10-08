from sqlalchemy.orm import Session
from app.models.ticket import Ticket
from app.models.ticket_attachment import TicketAttachment
from app.repositories.ticket_attachment_repository import (
    TicketAttachmentRepository,
)
from app.repositories.ticket_history_repository import (
    TicketHistoryRepository,
)
from app.services.ticket_comment_service import TicketNotFoundError


class TicketAttachmentService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = TicketAttachmentRepository(db)
        self.history_repository = TicketHistoryRepository(db)

    def list_attachments(
        self,
        ticket_id: int,
    ) -> list[TicketAttachment]:
        if self.db.get(Ticket, ticket_id) is None:
            raise TicketNotFoundError("Chamado nao encontrado.")

        return self.repository.list_by_ticket(ticket_id)

    def get_attachment(
        self,
        ticket_id: int,
        attachment_id: int,
    ) -> TicketAttachment | None:
        if self.db.get(Ticket, ticket_id) is None:
            raise TicketNotFoundError("Chamado nao encontrado.")

        return self.repository.get_for_ticket(
            ticket_id,
            attachment_id,
        )

    def add_attachment(
        self,
        ticket_id: int,
        user_id: int,
        original_filename: str,
        storage_path: str,
        file_size: int,
        mime_type: str,
    ) -> TicketAttachment:
        if self.db.get(Ticket, ticket_id) is None:
            raise TicketNotFoundError("Chamado nao encontrado.")

        attachment = self.repository.create(
            ticket_id=ticket_id,
            user_id=user_id,
            original_filename=original_filename,
            storage_path=storage_path,
            file_size=file_size,
            mime_type=mime_type,
        )

        self.history_repository.create(
            ticket_id=ticket_id,
            user_id=user_id,
            action="attachment_added",
            description="Anexo adicionado ao chamado.",
        )

        return attachment