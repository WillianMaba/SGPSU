from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.system_module import SystemModule


class SystemFeature(Base):
    __tablename__ = "system_features"

    __table_args__ = (
        UniqueConstraint(
            "module_id",
            "name",
            name="uq_system_features_module_name",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    module_id: Mapped[int] = mapped_column(
        ForeignKey("system_modules.id"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    module: Mapped["SystemModule"] = relationship(
        "SystemModule",
        back_populates="features",
    )