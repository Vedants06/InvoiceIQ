"""Deterministic demo scenarios (PRD §40–§43).

Demo mode builds fully-analyzed invoices through the SAME data structures and
response shape as real analysis (Invoice + Contract + Timesheet + checks +
anomalies + risk + explanation) so the frontend renders identical UI. It
requires no AI and no document upload — guaranteeing the hackathon flow works
even when the AI API, network, or document parsing fails.
"""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session, selectinload

from app.models import Anomaly, Contract, Document, Invoice, Timesheet
from app.models.enums import (
    BusinessStatus,
    DocumentType,
    ProcessingStatus,
)
from app.services import (
    anomaly_service,
    explanation_service,
    extraction_service,
    historical_service,
    reconciliation_service,
    risk_service,
    validation_service,
)
from app.services.billing import derive_billing

DEMO_SCENARIOS = ("clean", "critical", "timesheet")


def _line_items(hours: float, rate: float) -> list[dict]:
    amount = round(hours * rate, 2)
    return [
        {
            "description": "Professional Services — Software Development",
            "quantity": hours,
            "unit_price": rate,
            "amount": amount,
        }
    ]


def _make_invoice(number: str, vendor: str, hours: float, rate: float,
                  currency: str, inv_date: date) -> Invoice:
    total = Decimal(str(round(hours * rate, 2)))
    return Invoice(
        invoice_number=number,
        vendor_name=vendor,
        invoice_date=inv_date,
        due_date=inv_date,
        currency=currency,
        subtotal=total,
        tax=Decimal("0"),
        total=total,
        line_items=_line_items(hours, rate),
        status=BusinessStatus.PENDING_REVIEW,
        processing_status=ProcessingStatus.COMPLETED,
    )


def _document(invoice_id, document_type: DocumentType, name: str) -> Document:
    return Document(
        invoice_id=invoice_id,
        document_type=document_type,
        file_name=name,
        file_path=f"demo://{name}",
        mime_type=None,
    )


def _build(db: Session, invoice: Invoice, contract: Contract,
           timesheet: Timesheet | None, documents: list[Document],
           demo_explanation: str) -> Invoice:
    db.add(invoice)
    db.flush()

    contract.invoice_id = invoice.id
    db.add(contract)
    for doc in documents:
        doc.invoice_id = invoice.id
        db.add(doc)
    if timesheet is not None:
        timesheet.invoice_id = invoice.id
        db.add(timesheet)

    # Run the SAME deterministic pipeline as live analysis
    billed_hours, _ = derive_billing(invoice.line_items)
    checks = validation_service.run_checks(invoice, contract)
    checks.append(reconciliation_service.reconcile(invoice, timesheet, billed_hours))
    anomalies = anomaly_service.build_anomalies(invoice, contract, timesheet, checks)
    score, level = risk_service.score_anomalies(anomalies)

    for a in anomalies:
        db.add(
            Anomaly(
                invoice_id=invoice.id,
                type=a.type,
                severity=a.severity,
                title=a.title,
                description=a.description,
                points=a.points,
                evidence=a.evidence,
            )
        )

    invoice.verification_checks = [c.to_storage() for c in checks]
    # Demos intentionally have no prior history — keep the canonical scores.
    invoice.historical = None
    invoice.extraction_coverage = extraction_service.extraction_coverage(invoice, contract)
    invoice.risk_score = score
    invoice.risk_level = level

    # Explanation: use the AI if configured, otherwise a deterministic
    # fallback written from the verified findings (never invents evidence).
    explanation, available = explanation_service.generate_explanation(
        invoice, contract, timesheet, checks, anomalies
    )
    invoice.explanation = explanation or demo_explanation
    invoice.explanation_available = True  # deterministic fallback always available

    db.commit()

    return (
        db.query(Invoice)
        .filter(Invoice.id == invoice.id)
        .options(
            selectinload(Invoice.contract),
            selectinload(Invoice.timesheet),
            selectinload(Invoice.documents),
            selectinload(Invoice.anomalies),
            selectinload(Invoice.review),
        )
        .one()
    )


def create_demo(db: Session, scenario: str) -> Invoice:
    if scenario not in DEMO_SCENARIOS:
        raise ValueError(f"Unknown demo scenario: {scenario}")

    suffix = uuid.uuid4().hex[:6]

    if scenario == "clean":
        # PRD §40: rate $50, 80 hours, total $4,000; timesheet 80 -> risk 0 LOW
        invoice = _make_invoice(
            f"DEMO-{suffix}", "BrightPath Consulting", 80, 50, "USD",
            date(2026, 7, 15),
        )
        contract = Contract(
            vendor_name="BrightPath Consulting",
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
            hourly_rate=Decimal("50"), max_hours=Decimal("80"),
            max_amount=Decimal("4000"), currency="USD", payment_terms="Net 30",
        )
        timesheet = Timesheet(total_hours=Decimal("80"), file_name="timesheet_july.csv")
        docs = [
            _document(None, DocumentType.INVOICE, "invoice_clean.pdf"),
            _document(None, DocumentType.CONTRACT, "contract_brightpath.pdf"),
            _document(None, DocumentType.TIMESHEET, "timesheet_july.csv"),
        ]
        explanation = (
            "The invoice is consistent with the contract and the submitted "
            "timesheet: the billed rate matches the contracted rate, billed "
            "hours are within the contractual limit, the total is within the "
            "contract maximum, and all billed hours are supported by the "
            "timesheet. The invoice appears safe to approve."
        )

    elif scenario == "critical":
        # PRD §41: rate $75, 120 hours, total $9,000 vs contract $50/100/$5,000;
        # timesheet 95 -> 90 CRITICAL
        invoice = _make_invoice(
            f"DEMO-{suffix}", "Acme Technologies", 120, 75, "USD",
            date(2026, 8, 20),
        )
        contract = Contract(
            vendor_name="Acme Technologies",
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
            hourly_rate=Decimal("50"), max_hours=Decimal("100"),
            max_amount=Decimal("5000"), currency="USD", payment_terms="Net 30",
        )
        timesheet = Timesheet(total_hours=Decimal("95"), file_name="timesheet_aug.csv")
        docs = [
            _document(None, DocumentType.INVOICE, "invoice_critical.pdf"),
            _document(None, DocumentType.CONTRACT, "contract_acme.pdf"),
            _document(None, DocumentType.TIMESHEET, "timesheet_aug.csv"),
        ]
        explanation = (
            "This invoice requires manual review before payment. The billed "
            "rate of $75/hour exceeds the contracted $50/hour, the 120 billed "
            "hours exceed the contractual maximum of 100, the $9,000 total "
            "exceeds the $5,000 contract maximum, and 25 billed hours are not "
            "supported by the submitted timesheet (95 hours recorded). "
            "Multiple high-weight risk indicators are present."
        )

    else:  # timesheet — PRD §42
        # rate $60 matches, 100 hours within limit, but timesheet shows 82
        # -> TIMESHEET_MISMATCH only, 25 MEDIUM
        invoice = _make_invoice(
            f"DEMO-{suffix}", "Nova Solutions", 100, 60, "USD",
            date(2026, 8, 10),
        )
        contract = Contract(
            vendor_name="Nova Solutions",
            start_date=date(2026, 2, 1), end_date=date(2027, 1, 31),
            hourly_rate=Decimal("60"), max_hours=Decimal("100"),
            max_amount=Decimal("6000"), currency="USD", payment_terms="Net 45",
        )
        timesheet = Timesheet(total_hours=Decimal("82"), file_name="timesheet_nova.csv")
        docs = [
            _document(None, DocumentType.INVOICE, "invoice_timesheet.pdf"),
            _document(None, DocumentType.CONTRACT, "contract_nova.pdf"),
            _document(None, DocumentType.TIMESHEET, "timesheet_nova.csv"),
        ]
        explanation = (
            "The invoice matches the contracted rate and stays within "
            "contractual limits, but 18 billed hours are not supported by the "
            "submitted timesheet (100 hours billed vs 82 hours recorded). This "
            "single inconsistency should be reconciled with the vendor before "
            "approval; review is recommended."
        )

    return _build(db, invoice, contract, timesheet, docs, explanation)
