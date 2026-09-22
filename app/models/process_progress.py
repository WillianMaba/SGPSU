from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.process import Process
    from app.models.user import User


class ProcessProgress(Base):
    __tablename__ = "process_progress"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    process_id: Mapped[int] = mapped_column(
        ForeignKey("processes.id"),
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    process: Mapped["Process"] = relationship(
        "Process",
        back_populates="progress_entries",
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="process_progress_entries",
    )