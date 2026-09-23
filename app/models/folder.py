from datetime import datetime
from sqlalchemy import (
    Boolean,
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
    from app.models.file import File
    from app.models.repository import Repository


class Folder(Base):
    __tablename__ = "folders"

    __table_args__ = (
        Index(
            "uq_folders_root_name",
            "repository_id",
            "name",
            unique=True,
            postgresql_where=text("parent_folder_id IS NULL"),
        ),
        Index(
            "uq_folders_child_name",
            "repository_id",
            "parent_folder_id",
            "name",
            unique=True,
            postgresql_where=text("parent_folder_id IS NOT NULL"),
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

    parent_folder_id: Mapped[int | None] = mapped_column(
        ForeignKey("folders.id"),
        nullable=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
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
        back_populates="folders",
    )

    parent: Mapped["Folder | None"] = relationship(
        "Folder",
        remote_side=[id],
        back_populates="children",
    )

    children: Mapped[list["Folder"]] = relationship(
        "Folder",
        back_populates="parent",
    )

    files: Mapped[list["File"]] = relationship(
        "File",
        back_populates="folder",
    )