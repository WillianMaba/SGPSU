from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime

class RepositoryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=500)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise ValueError("O nome deve possuir pelo menos 3 caracteres validos.")
        return value


class RepositoryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=500)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if len(value) < 3:
            raise ValueError("O nome deve possuir pelo menos 3 caracteres validos.")
        return value


class RepositoryRead(BaseModel):
    id: int
    name: str
    description: str | None
    is_active: bool
    created_at: object
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
    