from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=150,
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )

    sector_id: int | None = None

    profile_id: int | None = None


class UserUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    email: EmailStr | None = None

    sector_id: int | None = None

    profile_id: int | None = None

    is_active: bool | None = None


class UserRead(BaseModel):
    id: int
    name: str
    email: EmailStr
    sector_id: int | None
    profile_id: int | None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )