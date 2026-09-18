"""Invoice analysis endpoint (PRD §32, §34).

POST /api/invoices/{id}/analyze runs the pipeline:

    parse -> AI extraction -> schema validation -> timesheet parsing
    -> deterministic verification -> timesheet reconciliation
    -> anomaly detection -> risk scoring -> persist -> AI explanation

The AI is used only for extraction and explanation; all decisions are
deterministic. If explanation generation fails the analysis still succeeds
(explanation_available = false).
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Anomaly, Contract, Document, Invoice, Timesheet
from app.models.enums import DocumentType, ProcessingStatus
from app.schemas.invoice import InvoiceDetail
from app.services import (
    anomaly_service,
    explanation_service,
    extraction_service,
    historical_service,
    reconciliation_service,
    risk_service,
    timesheet_service,
    validation_service,
)
from app.services.billing import derive_billing

router = APIRouter(prefix="/api/invoices", tags=["analysis"])


def _load_invoice(db: Session, invoice_id: uuid.UUID) -> Invoice | None:
    stmt = (
        db.query(Invoice)
        .filter(Invoice.id == invoice_id)
        .options(
            selectinload(Invoice.contract),
            selectinload(Invoice.timesheet),
            selectinload(Invoice.documents),
            selectinload(Invoice.anomalies),
            selectinload(Invoice.review),
        )
    )
    return stmt.first()


@router.post("/{invoice_id}/analyze", response_model=InvoiceDetail)
def analyze_invoice(
    invoice_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> Invoice:
    invoice = _load_invoice(db, invoice_id)
    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found."
        )

    invoice.processing_status = ProcessingStatus.PROCESSING
    db.commit()

    def _fail(message: str, code: int) -> None:
        invoice.processing_status = ProcessingStatus.FAILED
        db.commit()
        raise HTTPException(status_code=code, detail=message)

    # --- 2-6. AI extraction (invoice + contract), Pydantic-validated ------
    try:
        extraction_service.extract_and_persist_invoice(db, invoice)
        extraction_service.extract_and_persist_contract(db, invoice)
        db.commit()
    except extraction_service.ExtractionError as exc:
        message = str(exc)
        code = (
            status.HTTP_503_SERVICE_UNAVAILABLE
            if "not configured" in message or "AI request failed" in message
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        db.rollback()
        _fail(message, code)

    db.refresh(invoice)
    contract: Contract = invoice.contract

    # --- 7. Timesheet parsing (deterministic, optional) -------------------
    timesheet: Timesheet | None = None
    ts_doc = (
        db.query(Document)
        .filter(
            Document.invoice_id == invoice.id,
            Document.document_type == DocumentType.TIMESHEET,
        )
        .order_by(Document.created_at.desc())
        .first()
    )
    if ts_doc is not None:
        try:
            result = timesheet_service.persist_timesheet(
                db, invoice.id, ts_doc.file_path, ts_doc.file_name
            )
            db.commit()
            db.refresh(invoice)
            timesheet = invoice.timesheet
        except timesheet_service.TimesheetError as exc:
            db.rollback()
            _fail(str(exc), status.HTTP_422_UNPROCESSABLE_ENTITY)

    # --- 8. Deterministic verification ------------------------------------
    billed_hours, _ = derive_billing(invoice.line_items)
    checks = validation_service.run_checks(invoice, contract)

    # --- 9. Timesheet reconciliation --------------------------------------
    checks.append(reconciliation_service.reconcile(invoice, timesheet, billed_hours))

    # --- 10-11. Anomalies + deterministic risk score ----------------------
    anomaly_results = anomaly_service.build_anomalies(
        invoice, contract, timesheet, checks
    )

    # Historical vendor analysis (P1, PRD §19) — may add UNUSUAL_AMOUNT
    historical_stats, history_anomaly = historical_service.analyze_history(
        db, invoice, contract
    )
    if history_anomaly is not None:
        anomaly_results.append(history_anomaly)
        anomaly_results.sort(key=lambda a: a.points, reverse=True)

    risk_score, risk_level = risk_service.score_anomalies(anomaly_results)

    # --- Persist ----------------------------------------------------------
    db.query(Anomaly).filter(Anomaly.invoice_id == invoice.id).delete()
    for a in anomaly_results:
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
    invoice.historical = historical_stats.as_dict() if historical_stats else None
    invoice.extraction_coverage = extraction_service.extraction_coverage(invoice, contract)
    invoice.risk_score = risk_score
    invoice.risk_level = risk_level

    # --- 12. AI explanation (best-effort; never fails the analysis) -------
    explanation, available = explanation_service.generate_explanation(
        invoice, contract, timesheet, checks, anomaly_results
    )
    invoice.explanation = explanation or None
    invoice.explanation_available = available

    invoice.processing_status = ProcessingStatus.COMPLETED
    db.commit()

    return _load_invoice(db, invoice_id)
