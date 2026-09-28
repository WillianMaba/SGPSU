from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.process import Process
    from app.models.user import User


class ProcessDocument(Base):
    __tablename__ = "process_documents"

    __table_args__ = (
        UniqueConstraint(
            "process_id",
            "document_id",
            name="uq_process_documents_process_document",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    process_id: Mapped[int] = mapped_column(
        ForeignKey("processes.id"),
        nullable=False,
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id"),
        nullable=False,
    )

    linked_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    process: Mapped["Process"] = relationship(
        "Process",
        back_populates="documents",
    )

    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="processes",
    )

    linked_by: Mapped["User"] = relationship(
        "User",
        foreign_keys=[linked_by_id],
        back_populates="linked_process_documents",
    )