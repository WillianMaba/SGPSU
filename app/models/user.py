from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from app.models.sector import Sector
from app.models.profile import Profile

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    
    email: Mapped[str]= mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )
    
    password_hash: Mapped[str] = mapped_column(
        String(255),
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
    
    sector_id: Mapped[int] = mapped_column(
        ForeignKey("sectors.id"),
        nullable=False,
    )
    
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id"),
        nullable=False,
    )
    
    sector: Mapped["Sector"] = relationship(
        "Sector",
        back_populates="users",
    )
    
    profile: Mapped["Profile"] = relationship(
        "Profile",
        back_populates="users",
    )