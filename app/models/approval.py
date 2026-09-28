from datetime import datetime
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.process import Process
    from app.models.request import Request
    from app.models.user import User


class Approval(Base):
    __tablename__ = "approvals"

    __table_args__ = (
        CheckConstraint(
            "num_nonnulls(process_id, request_id) = 1",
            name="ck_approvals_target",
        ),
        CheckConstraint(
            "status IN ('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED')",
            name="ck_approvals_status",
        ),
        CheckConstraint(
            "(status = 'PENDING' AND decided_at IS NULL) "
            "OR (status <> 'PENDING' AND decided_at IS NOT NULL)",
            name="ck_approvals_decision_date",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    process_id: Mapped[int | None] = mapped_column(
        ForeignKey("processes.id"),
        nullable=True,
    )

    request_id: Mapped[int | None] = mapped_column(
        ForeignKey("requests.id"),
        nullable=True,
    )

    approver_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    approval_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING",
    )

    decision_comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    decided_at: Mapped[datetime | None] = mapped_column(
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

    process: Mapped["Process | None"] = relationship(
        "Process",
        back_populates="approvals",
    )

    request: Mapped["Request | None"] = relationship(
        "Request",
        back_populates="approvals",
    )

    approver: Mapped["User"] = relationship(
        "User",
        foreign_keys=[approver_id],
        back_populates="approvals",
    )