from datetime import datetime
from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.file_access import FileAccess
    from app.models.folder_access import FolderAccess
    from app.models.repository_access import RepositoryAccess

class Sector(Base):
    __tablename__ = "sectors"
    
    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        unique=True,
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
    
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="sector",
    )
    
    repository_accesses: Mapped[list["RepositoryAccess"]] = relationship(
        "RepositoryAccess",
        foreign_keys="RepositoryAccess.sector_id",
        back_populates="sector",
    )

    folder_accesses: Mapped[list["FolderAccess"]] = relationship(
        "FolderAccess",
        foreign_keys="FolderAccess.sector_id",
        back_populates="sector",
    )

    file_accesses: Mapped[list["FileAccess"]] = relationship(
        "FileAccess",
        foreign_keys="FileAccess.sector_id",
        back_populates="sector",
    )