"""Timesheet model (PRD §30).

Only the deterministic total (sum of recorded hours, PRD §16) is persisted
alongside the uploaded file metadata — raw rows are not stored.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Timesheet(Base):
    __tablename__ = "timesheets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    vendor_name: Mapped[str | None] = mapped_column(String(255))
    total_hours: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    invoice: Mapped["Invoice"] = relationship(back_populates="timesheet")  # noqa: F821
