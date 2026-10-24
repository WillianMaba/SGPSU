
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProcessStageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=3, max_length=150)

    description: str | None = None

    sequence: int = Field(gt=0)

    responsible_id: int | None = Field(
        default=None,
        gt=0,
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()

        if len(value) < 3:
            raise ValueError(
                "O nome deve possuir pelo menos 3 caracteres validos."
            )

        return value


class ProcessStageUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(
        default=None,
        min_length=3,
        max_length=150,
    )

    description: str | None = None

    sequence: int | None = Field(
        default=None,
        gt=0,
    )

    responsible_id: int | None = Field(
        default=None,
        gt=0,
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if len(value) < 3:
            raise ValueError(
                "O nome deve possuir pelo menos 3 caracteres validos."
            )

        return value


class ProcessStageRead(BaseModel):
    id: int
    process_id: int

    name: str
    description: str | None
    sequence: int

    responsible_id: int | None

    is_completed: bool

    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProcessStageHistoryRead(BaseModel):
    id: int
    process_stage_id: int
    user_id: int

    action: str
    description: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
