from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProcessCreate(BaseModel):

    model_config = ConfigDict(extra="forbid")

    title: str = Field(
        min_length=3,
        max_length=200,
    )

    description: str | None = None

    process_type_id: int = Field(gt=0)

    responsible_id: int | None = Field(
        default=None,
        gt=0,
    )


class ProcessUpdate(BaseModel):

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(
        default=None,
        min_length=3,
        max_length=200,
    )

    description: str | None = None

    process_type_id: int | None = Field(
        default=None,
        gt=0,
    )

    responsible_id: int | None = Field(
        default=None,
        gt=0,
    )


class ProcessRead(BaseModel):

    id: int

    protocol: str

    title: str

    description: str | None

    process_type_id: int

    status_id: int

    created_by_id: int

    responsible_id: int | None

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )