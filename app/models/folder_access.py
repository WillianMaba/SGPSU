from datetime import datetime
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.folder import Folder
    from app.models.profile import Profile
    from app.models.sector import Sector
    from app.models.user import User


class FolderAccess(Base):
    __tablename__ = "folder_access"

    __table_args__ = (
        CheckConstraint(
            "num_nonnulls(user_id, profile_id, sector_id) = 1",
            name="ck_folder_access_subject",
        ),
        CheckConstraint(
            "permission IN ('READ', 'WRITE', 'MODIFY', 'DELETE', 'ADMIN')",
            name="ck_folder_access_permission",
        ),
        CheckConstraint(
            "effect IN ('ALLOW', 'DENY')",
            name="ck_folder_access_effect",
        ),
        Index(
            "uq_folder_access_user_perm",
            "folder_id",
            "user_id",
            "permission",
            unique=True,
            postgresql_where=text("user_id IS NOT NULL"),
        ),
        Index(
            "uq_folder_access_profile_perm",
            "folder_id",
            "profile_id",
            "permission",
            unique=True,
            postgresql_where=text("profile_id IS NOT NULL"),
        ),
        Index(
            "uq_folder_access_sector_perm",
            "folder_id",
            "sector_id",
            "permission",
            unique=True,
            postgresql_where=text("sector_id IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    folder_id: Mapped[int] = mapped_column(
        ForeignKey("folders.id"),
        nullable=False,
    )

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("profiles.id"),
        nullable=True,
    )

    sector_id: Mapped[int | None] = mapped_column(
        ForeignKey("sectors.id"),
        nullable=True,
    )

    permission: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    effect: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    folder: Mapped["Folder"] = relationship(
        "Folder",
        back_populates="access_rules",
    )

    user: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="folder_accesses",
    )

    profile: Mapped["Profile | None"] = relationship(
        "Profile",
        foreign_keys=[profile_id],
        back_populates="folder_accesses",
    )

    sector: Mapped["Sector | None"] = relationship(
        "Sector",
        foreign_keys=[sector_id],
        back_populates="folder_accesses",
    )