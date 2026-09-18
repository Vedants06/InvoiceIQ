"""Contract model (PRD §30).

The PRD table does not include invoice_id; we add it as a pragmatic MVP link
because each analysis pairs one uploaded contract with one invoice, and a
vendor-name join would be unreliable (a vendor mismatch is itself an anomaly).
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    vendor_name: Mapped[str | None] = mapped_column(String(255))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    hourly_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    max_hours: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    max_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str | None] = mapped_column(String(3))
    payment_terms: Mapped[str | None] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    invoice: Mapped["Invoice"] = relationship(back_populates="contract")  # noqa: F821
