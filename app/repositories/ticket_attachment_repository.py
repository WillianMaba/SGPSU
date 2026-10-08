from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.ticket_attachment import TicketAttachment


class TicketAttachmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_ticket(
        self,
        ticket_id: int,
    ) -> list[TicketAttachment]:
        statement = (
            select(TicketAttachment)
            .where(TicketAttachment.ticket_id == ticket_id)
            .order_by(TicketAttachment.id.desc())
        )

        return list(self.db.scalars(statement).all())

    def get_for_ticket(
        self,
        ticket_id: int,
        attachment_id: int,
    ) -> TicketAttachment | None:
        statement = select(TicketAttachment).where(
            TicketAttachment.ticket_id == ticket_id,
            TicketAttachment.id == attachment_id,
        )

        return self.db.scalar(statement)

    def create(
        self,
        ticket_id: int,
        user_id: int,
        original_filename: str,
        storage_path: str,
        file_size: int,
        mime_type: str,
    ) -> TicketAttachment:
        attachment = TicketAttachment(
            ticket_id=ticket_id,
            user_id=user_id,
            original_filename=original_filename,
            storage_path=storage_path,
            file_size=file_size,
            mime_type=mime_type,
        )

        self.db.add(attachment)
        self.db.flush()
        self.db.refresh(attachment)

        return attachment