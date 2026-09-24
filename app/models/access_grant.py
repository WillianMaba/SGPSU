from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.access_request_resource import AccessRequestResource
    from app.models.user import User


class AccessGrant(Base):
    __tablename__ = "access_grants"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    access_request_resource_id: Mapped[int] = mapped_column(
        ForeignKey("access_request_resources.id"),
        nullable=False,
    )

    granted_scope: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    granted_permissions: Mapped[list[str] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    effective_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    granted_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    request_resource: Mapped["AccessRequestResource"] = relationship(
        "AccessRequestResource",
        back_populates="grants",
    )

    granted_by: Mapped["User"] = relationship(
        "User",
        foreign_keys=[granted_by_id],
        back_populates="access_grants",
    )