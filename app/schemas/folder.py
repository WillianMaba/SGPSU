from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FolderCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=500)
    parent_folder_id: int | None = Field(default=None, gt=0)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("O nome da pasta nao pode ser vazio.")
        return value


class FolderUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=500)
    parent_folder_id: int | None = Field(default=None, gt=0)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("O nome da pasta nao pode ser vazio.")
        return value


class FolderRead(BaseModel):
    id: int
    repository_id: int
    parent_folder_id: int | None
    name: str
    description: str | None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)