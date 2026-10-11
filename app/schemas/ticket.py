from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class TicketCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=1)
    status_id: int
    priority_id: int
    category_id: int
    assignee_id: int | None = None


class TicketUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(
        default=None,
        min_length=3,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        min_length=1,
    )

    priority_id: int | None = None
    category_id: int | None = None
    assignee_id: int | None = None


class TicketRead(BaseModel):
    id: int
    title: str
    description: str
    status_id: int
    priority_id: int
    category_id: int
    requester_id: int
    assignee_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )