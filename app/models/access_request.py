from datetime import datetime
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.access_request_resource import AccessRequestResource
    from app.models.request import Request


class AccessRequest(Base):
    __tablename__ = "access_requests"

    __table_args__ = (
        UniqueConstraint(
            "request_id",
            name="uq_access_requests_request_id",
        ),
        CheckConstraint(
            "operation_type IN ('NEW', 'CHANGE', 'REVOKE')",
            name="ck_access_requests_operation_type",
        ),
        CheckConstraint(
            "period_type IN ('PERMANENT', 'TEMPORARY')",
            name="ck_access_requests_period_type",
        ),
        CheckConstraint(
            "end_at IS NULL OR start_at IS NULL OR end_at > start_at",
            name="ck_access_requests_valid_period",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    request_id: Mapped[int] = mapped_column(
        ForeignKey("requests.id"),
        nullable=False,
    )

    operation_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    justification: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    period_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PERMANENT",
    )

    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    end_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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

    request: Mapped["Request"] = relationship(
        "Request",
        back_populates="access_request",
    )

    resources: Mapped[list["AccessRequestResource"]] = relationship(
        "AccessRequestResource",
        back_populates="access_request",
    )