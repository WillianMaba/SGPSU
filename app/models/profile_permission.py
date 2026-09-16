from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey 
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class ProfilePermission(Base):
    __tablename__ = "profile_permissions"
    
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id"),
        primary_key=True,
    )
    
    permission_id: Mapped[int] = mapped_column(
        ForeignKey("permissions.id"),
        primary_key=True,
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
    