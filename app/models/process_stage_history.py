from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.process_stage import ProcessStage
    from app.models.user import User


class ProcessStageHistory(Base):
    __tablename__ = "process_stage_history"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    process_stage_id: Mapped[int] = mapped_column(
        ForeignKey("process_stages.id"),
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    process_stage: Mapped["ProcessStage"] = relationship(
        "ProcessStage",
        back_populates="history_entries",
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="process_stage_history",
    )