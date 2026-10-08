from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class TicketCommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=10000)


class TicketCommentRead(BaseModel):
    id: int
    ticket_id: int
    user_id: int
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)