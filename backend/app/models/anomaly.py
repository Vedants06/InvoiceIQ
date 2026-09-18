"""Anomaly model (PRD §21, §30).

Each anomaly type contributes its weight AT MOST ONCE per invoice, enforced by
a unique constraint on (invoice_id, type). Evidence is structured backend data
stored as JSON — the AI never invents evidence (PRD §22).
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

from .enums import AnomalySeverity


class Anomaly(Base):
    __tablename__ = "anomalies"
    __table_args__ = (
        UniqueConstraint("invoice_id", "type", name="uq_anomaly_invoice_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False
    )

    # Anomaly type code, e.g. RATE_MISMATCH (PRD §21)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[AnomalySeverity] = mapped_column(
        Enum(AnomalySeverity, native_enum=False, length=10), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    evidence: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    invoice: Mapped["Invoice"] = relationship(back_populates="anomalies")  # noqa: F821
