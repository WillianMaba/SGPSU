from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.system import System
    from app.models.system_feature import SystemFeature


class SystemModule(Base):
    __tablename__ = "system_modules"

    __table_args__ = (
        UniqueConstraint(
            "system_id",
            "name",
            name="uq_system_modules_system_name",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    system_id: Mapped[int] = mapped_column(
        ForeignKey("systems.id"),
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

    system: Mapped["System"] = relationship(
        "System",
        back_populates="modules",
    )

    features: Mapped[list["SystemFeature"]] = relationship(
        "SystemFeature",
        back_populates="module",
    )