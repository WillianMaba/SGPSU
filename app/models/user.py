from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from app.models.sector import Sector
from app.models.profile import Profile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.ticket import Ticket
    from app.models.ticket_comment import TicketComment
    from app.models.ticket_attachment import TicketAttachment
    from app.models.ticket_history import TicketHistory
    from app.models.process import Process
    from app.models.process_progress import ProcessProgress
    from app.models.process_stage import ProcessStage
    from app.models.task import Task
    from app.models.document import Document
    from app.models.document_version import DocumentVersion
    from app.models.file import File
    from app.models.file_version import FileVersion

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
    
    requested_tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket",
        foreign_keys="Ticket.requester_id",
        back_populates="requester",
    )

    assigned_tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket",
        foreign_keys="Ticket.assignee_id",
        back_populates="assignee",
    )
    
    ticket_comments: Mapped[list["TicketComment"]] = relationship(
        "TicketComment",    
    back_populates="user",
    )
    
    ticket_attachments: Mapped[list["TicketAttachment"]] = relationship(
        "TicketAttachment",
        back_populates="user",
    )
    
    ticket_history: Mapped[list["TicketHistory"]] = relationship(
        "TicketHistory",
        back_populates="user",
    )
    
    created_processes: Mapped[list["Process"]] = relationship(
    "Process",
    foreign_keys="Process.created_by_id",
    back_populates="created_by",
    )

    responsible_processes: Mapped[list["Process"]] = relationship(
        "Process",
        foreign_keys="Process.responsible_id",
        back_populates="responsible",
    )

    process_stages: Mapped[list["ProcessStage"]] = relationship(
        "ProcessStage",
        foreign_keys="ProcessStage.responsible_id",
        back_populates="responsible",
    )

    process_progress_entries: Mapped[list["ProcessProgress"]] = relationship(
        "ProcessProgress",
        back_populates="user",
    )

    assigned_tasks: Mapped[list["Task"]] = relationship(
        "Task",
        foreign_keys="Task.assigned_to_id",
        back_populates="assigned_to",
    )
    
    created_documents: Mapped[list["Document"]] = relationship(
        "Document",
        foreign_keys="Document.created_by_id",
        back_populates="created_by",
    )

    created_document_versions: Mapped[list["DocumentVersion"]] = relationship(
        "DocumentVersion",
        foreign_keys="DocumentVersion.created_by_id",
        back_populates="created_by",
    )

    created_files: Mapped[list["File"]] = relationship(
        "File",
        foreign_keys="File.created_by_id",
        back_populates="created_by",
    )

    created_file_versions: Mapped[list["FileVersion"]] = relationship(
        "FileVersion",
        foreign_keys="FileVersion.created_by_id",
        back_populates="created_by",
    )