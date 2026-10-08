from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TicketHistoryRead(BaseModel):
    id: int
    ticket_id: int
    user_id: int
    action: str
    description: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)