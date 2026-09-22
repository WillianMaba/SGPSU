from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.process_progress import ProcessProgress
    from app.models.process_stage import ProcessStage
    from app.models.process_status import ProcessStatus
    from app.models.process_type import ProcessType
    from app.models.task import Task
    from app.models.user import User


class Process(Base):
    __tablename__ = "processes"

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

    process_type_id: Mapped[int] = mapped_column(
        ForeignKey("process_types.id"),
        nullable=False,
    )

    status_id: Mapped[int] = mapped_column(
        ForeignKey("process_statuses.id"),
        nullable=False,
    )

    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    responsible_id: Mapped[int | None] = mapped_column(
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

    process_type: Mapped["ProcessType"] = relationship(
        "ProcessType",
        back_populates="processes",
    )

    status: Mapped["ProcessStatus"] = relationship(
        "ProcessStatus",
        back_populates="processes",
    )

    created_by: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by_id],
        back_populates="created_processes",
    )

    responsible: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[responsible_id],
        back_populates="responsible_processes",
    )

    stages: Mapped[list["ProcessStage"]] = relationship(
        "ProcessStage",
        back_populates="process",
    )

    progress_entries: Mapped[list["ProcessProgress"]] = relationship(
        "ProcessProgress",
        back_populates="process",
    )

    tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="process",
    )