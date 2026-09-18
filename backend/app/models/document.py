"""Document metadata model (PRD §30).

Tracks uploaded files stored on disk under the configured upload directory.
File contents are stored on disk, not in the database (PRD §38).
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

from .enums import DocumentType


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False
    )

    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, native_enum=False, length=20), nullable=False
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(100))

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    invoice: Mapped["Invoice"] = relationship(back_populates="documents")  # noqa: F821

    @property
    def is_demo(self) -> bool:
        """Demo documents have no real file on disk (demo:// pseudo-path)."""
        return self.file_path.startswith("demo://")
