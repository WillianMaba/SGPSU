
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=200)

    description: str | None = None

    assigned_to_id: int | None = Field(
        default=None,
        gt=0,
    )

    due_at: datetime | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        value = value.strip()

        if len(value) < 3:
            raise ValueError(
                "O titulo deve possuir pelo menos 3 caracteres validos."
            )

        return value

class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(
        default=None,
        min_length=3,
        max_length=200,
    )

    description: str | None = None

    assigned_to_id: int | None = Field(
        default=None,
        gt=0,
    )

    due_at: datetime | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if len(value) < 3:
            raise ValueError(
                "O titulo deve possuir pelo menos 3 caracteres validos."
            )

        return value

class TaskRead(BaseModel):
    id: int
    process_id: int

    title: str
    description: str | None

    assigned_to_id: int | None

    due_at: datetime | None

    is_completed: bool

    created_at: datetime
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)