from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.access_grant import AccessGrant
    from app.models.access_request import AccessRequest
    from app.models.access_resource import AccessResource


class AccessRequestResource(Base):
    __tablename__ = "access_request_resources"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    access_request_id: Mapped[int] = mapped_column(
        ForeignKey("access_requests.id"),
        nullable=False,
    )

    access_resource_id: Mapped[int] = mapped_column(
        ForeignKey("access_resources.id"),
        nullable=False,
    )

    requested_scope: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    requested_permissions: Mapped[list[str] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    justification: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    access_request: Mapped["AccessRequest"] = relationship(
        "AccessRequest",
        back_populates="resources",
    )

    resource: Mapped["AccessResource"] = relationship(
        "AccessResource",
        back_populates="request_resources",
    )

    grants: Mapped[list["AccessGrant"]] = relationship(
        "AccessGrant",
        back_populates="request_resource",
    )