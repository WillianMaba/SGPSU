from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TicketAttachmentRead(BaseModel):
    id: int
    ticket_id: int
    user_id: int
    original_filename: str
    file_size: int
    mime_type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)