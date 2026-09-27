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
    from app.models.repository import Repository
    from app.models.sector import Sector
    from app.models.user import User


class RepositoryAccess(Base):
    __tablename__ = "repository_access"

    __table_args__ = (
        CheckConstraint(
            "num_nonnulls(user_id, profile_id, sector_id) = 1",
            name="ck_repository_access_subject",
        ),
        CheckConstraint(
            "permission IN ('READ', 'WRITE', 'MODIFY', 'DELETE', 'ADMIN')",
            name="ck_repository_access_permission",
        ),
        CheckConstraint(
            "effect IN ('ALLOW', 'DENY')",
            name="ck_repository_access_effect",
        ),
        Index(
            "uq_repo_access_user_perm",
            "repository_id",
            "user_id",
            "permission",
            unique=True,
            postgresql_where=text("user_id IS NOT NULL"),
        ),
        Index(
            "uq_repo_access_profile_perm",
            "repository_id",
            "profile_id",
            "permission",
            unique=True,
            postgresql_where=text("profile_id IS NOT NULL"),
        ),
        Index(
            "uq_repo_access_sector_perm",
            "repository_id",
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

    repository_id: Mapped[int] = mapped_column(
        ForeignKey("file_repositories.id"),
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

    repository: Mapped["Repository"] = relationship(
        "Repository",
        back_populates="access_rules",
    )

    user: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="repository_accesses",
    )

    profile: Mapped["Profile | None"] = relationship(
        "Profile",
        foreign_keys=[profile_id],
        back_populates="repository_accesses",
    )

    sector: Mapped["Sector | None"] = relationship(
        "Sector",
        foreign_keys=[sector_id],
        back_populates="repository_accesses",
    )