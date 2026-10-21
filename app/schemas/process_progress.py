from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProcessProgressCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str = Field(
        min_length=1,
        max_length=5000,
    )

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "A descricao da movimentacao nao pode estar vazia."
            )

        return value


class ProcessProgressRead(BaseModel):
    id: int
    process_id: int
    user_id: int
    description: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)