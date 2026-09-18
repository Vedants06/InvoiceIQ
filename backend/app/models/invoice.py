"""Invoice model (PRD §30).

An invoice row is created at upload time (processing_status=UPLOADED) and the
extracted fields are populated after AI extraction + verification.

Two pragmatic columns beyond the PRD table support the P0 workflow and are
stored as portable JSON:
  * line_items          — extracted invoice line items (needed for arithmetic
                          validation, PRD §17.7)
  * verification_checks — the deterministic check results that drive the
                          Verification Summary (PRD §20)
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

from .enums import BusinessStatus, ProcessingStatus, RiskLevel


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    # Extracted fields (nullable until extraction completes)
    invoice_number: Mapped[str | None] = mapped_column(String(100))
    vendor_name: Mapped[str | None] = mapped_column(String(255))
    invoice_date: Mapped[date | None] = mapped_column(Date)
    due_date: Mapped[date | None] = mapped_column(Date)
    currency: Mapped[str | None] = mapped_column(String(3))
    subtotal: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    tax: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    total: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    line_items: Mapped[list | None] = mapped_column(JSON)

    # Status
    status: Mapped[BusinessStatus] = mapped_column(
        Enum(BusinessStatus, native_enum=False, length=20),
        default=BusinessStatus.PENDING_REVIEW,
        nullable=False,
    )
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus, native_enum=False, length=20),
        default=ProcessingStatus.UPLOADED,
        nullable=False,
    )

    # Risk (computed deterministically by the backend)
    risk_score: Mapped[int | None] = mapped_column(Integer)
    risk_level: Mapped[RiskLevel | None] = mapped_column(
        Enum(RiskLevel, native_enum=False, length=10)
    )

    # Verification summary + AI explanation (PRD §20, §25)
    verification_checks: Mapped[list | None] = mapped_column(JSON)
    # Deterministic extraction coverage (P1): fraction of expected fields present
    extraction_coverage: Mapped[float | None] = mapped_column(Float)
    # Historical vendor stats (P1, PRD §19)
    historical: Mapped[dict | None] = mapped_column(JSON)
    explanation: Mapped[str | None] = mapped_column(Text)
    explanation_available: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    documents: Mapped[list["Document"]] = relationship(  # noqa: F821
        back_populates="invoice", cascade="all, delete-orphan"
    )
    contract: Mapped["Contract | None"] = relationship(  # noqa: F821
        back_populates="invoice", cascade="all, delete-orphan", uselist=False
    )
    timesheet: Mapped["Timesheet | None"] = relationship(  # noqa: F821
        back_populates="invoice", cascade="all, delete-orphan", uselist=False
    )
    anomalies: Mapped[list["Anomaly"]] = relationship(  # noqa: F821
        back_populates="invoice",
        cascade="all, delete-orphan",
        order_by="Anomaly.points.desc()",
    )
    review: Mapped["Review | None"] = relationship(  # noqa: F821
        back_populates="invoice", cascade="all, delete-orphan", uselist=False
    )
