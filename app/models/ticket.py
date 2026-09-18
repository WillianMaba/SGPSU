from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.ticket_status import TicketStatus
    from app.models.ticket_priority import TicketPriority
    from app.models.ticket_category import TicketCategory


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status_id: Mapped[int] = mapped_column(
        ForeignKey("ticket_statuses.id"),
        nullable=False,
    )

    priority_id: Mapped[int] = mapped_column(
        ForeignKey("ticket_priorities.id"),
        nullable=False,
    )

    category_id: Mapped[int] = mapped_column(
        ForeignKey("ticket_categories.id"),
        nullable=False,
    )

    requester_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
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
    
    status: Mapped["TicketStatus"] = relationship(
        "TicketStatus",
        back_populates="tickets",
    )

    priority: Mapped["TicketPriority"] = relationship(
        "TicketPriority",
        back_populates="tickets",
    )

    category: Mapped["TicketCategory"] = relationship(
        "TicketCategory",
        back_populates="tickets",
    )

    requester: Mapped["User"] = relationship(
        "User",
        foreign_keys=[requester_id],
        back_populates="requested_tickets",
    )

    assignee: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[assignee_id],
        back_populates="assigned_tickets",
    )