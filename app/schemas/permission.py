from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class PermissionCreate(BaseModel):
    name: str = Field(min_length=3, max_length=150)
    description: str | None = Field(
        default=None,
        max_length=500,
    )


class PermissionUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=3,
        max_length=150,
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )
    is_active: bool | None = None


class PermissionRead(BaseModel):
    id: int
    name: str
    description: str | None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )