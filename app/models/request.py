from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.access_request import AccessRequest
    from app.models.request_status import RequestStatus
    from app.models.user import User


class Request(Base):
    __tablename__ = "requests"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    protocol: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        unique=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    requester_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    status_id: Mapped[int] = mapped_column(
        ForeignKey("request_statuses.id"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    requester: Mapped["User"] = relationship(
        "User",
        foreign_keys=[requester_id],
        back_populates="requested_requests",
    )

    status: Mapped["RequestStatus"] = relationship(
        "RequestStatus",
        back_populates="requests",
    )

    access_request: Mapped["AccessRequest | None"] = relationship(
        "AccessRequest",
        back_populates="request",
        uselist=False,
    )