"""Database model tests (PRD §30)."""

from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Anomaly, Contract, Document, Invoice, Review, Timesheet
from app.models.enums import (
    AnomalySeverity,
    BusinessStatus,
    DocumentType,
    ProcessingStatus,
    ReviewDecision,
    RiskLevel,
)


def _make_invoice(session, **kwargs) -> Invoice:
    invoice = Invoice(
        invoice_number=kwargs.pop("invoice_number", "INV-1042"),
        vendor_name=kwargs.pop("vendor_name", "Acme Technologies"),
        currency=kwargs.pop("currency", "USD"),
        total=kwargs.pop("total", Decimal("9000.00")),
        line_items=kwargs.pop("line_items", []),
        **kwargs,
    )
    session.add(invoice)
    session.commit()
    session.refresh(invoice)
    return invoice


def test_invoice_defaults(db_session):
    invoice = _make_invoice(db_session)
    assert invoice.status == BusinessStatus.PENDING_REVIEW
    assert invoice.processing_status == ProcessingStatus.UPLOADED
    assert invoice.risk_score is None
    assert invoice.risk_level is None
    assert invoice.created_at is not None


def test_all_six_tables_created(db_session):
    from sqlalchemy import inspect

    from app.database import Base

    names = set(inspect(db_session.bind).get_table_names())
    assert {
        "invoices",
        "contracts",
        "timesheets",
        "documents",
        "anomalies",
        "reviews",
    } <= names
    # sanity: model count matches metadata
    assert len(Base.metadata.tables) >= 6


def test_invoice_relationships(db_session):
    invoice = _make_invoice(db_session)

    contract = Contract(
        invoice_id=invoice.id,
        vendor_name="Acme Technologies",
        hourly_rate=Decimal("50.00"),
        max_hours=Decimal("100"),
        max_amount=Decimal("5000.00"),
        currency="USD",
    )
    timesheet = Timesheet(
        invoice_id=invoice.id,
        total_hours=Decimal("95"),
        file_name="timesheet.csv",
    )
    document = Document(
        invoice_id=invoice.id,
        document_type=DocumentType.INVOICE,
        file_name="invoice.pdf",
        file_path="/tmp/invoice.pdf",
        mime_type="application/pdf",
    )
    review = Review(
        invoice_id=invoice.id,
        decision=ReviewDecision.APPROVED,
        reason="Verified manually",
    )
    db_session.add_all([contract, timesheet, document, review])
    db_session.commit()

    db_session.refresh(invoice)
    assert invoice.contract.hourly_rate == Decimal("50.00")
    assert invoice.timesheet.total_hours == Decimal("95")
    assert len(invoice.documents) == 1
    assert invoice.review.decision == ReviewDecision.APPROVED


def test_anomaly_unique_per_invoice(db_session):
    invoice = _make_invoice(db_session)

    def rate_anomaly():
        return Anomaly(
            invoice_id=invoice.id,
            type="RATE_MISMATCH",
            severity=AnomalySeverity.HIGH,
            title="Hourly rate exceeds contract",
            description="Invoice charges $75/hour; contract specifies $50/hour.",
            points=20,
            evidence={"invoice_rate": 75, "contract_rate": 50},
        )

    db_session.add(rate_anomaly())
    db_session.commit()

    db_session.add(rate_anomaly())  # same type for same invoice
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_different_anomaly_types_allowed(db_session):
    invoice = _make_invoice(db_session)
    for atype, points in [("RATE_MISMATCH", 20), ("EXCESSIVE_HOURS", 20)]:
        db_session.add(
            Anomaly(
                invoice_id=invoice.id,
                type=atype,
                severity=AnomalySeverity.HIGH,
                title=atype,
                description=atype,
                points=points,
                evidence={},
            )
        )
    db_session.commit()
    db_session.refresh(invoice)
    assert len(invoice.anomalies) == 2
    # ordered by points desc (both equal here) — assert score math instead
    total = sum(a.points for a in invoice.anomalies)
    assert total == 40


def test_risk_level_enum_persists(db_session):
    invoice = _make_invoice(db_session, risk_score=90, risk_level=RiskLevel.CRITICAL)
    db_session.commit()
    fetched = db_session.get(Invoice, invoice.id)
    assert fetched.risk_level == RiskLevel.CRITICAL
    assert fetched.risk_score == 90


def test_cascade_delete(db_session):
    invoice = _make_invoice(db_session)
    db_session.add(
        Anomaly(
            invoice_id=invoice.id,
            type="VENDOR_MISMATCH",
            severity=AnomalySeverity.HIGH,
            title="t",
            description="d",
            points=30,
            evidence={},
        )
    )
    db_session.commit()

    db_session.delete(invoice)
    db_session.commit()
    assert db_session.query(Anomaly).count() == 0
    assert db_session.query(Invoice).count() == 0
