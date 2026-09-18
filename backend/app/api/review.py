"""Human review endpoint (PRD §28, §34).

POST /api/invoices/{id}/review records an approve/reject decision. Rejection
requires a reason. No payment is ever executed — InvoiceIQ only records the
human decision.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Invoice, Review
from app.models.enums import (
    BusinessStatus,
    ProcessingStatus,
    ReviewDecision,
)
from app.schemas.invoice import InvoiceDetail
from app.schemas.review import ReviewRequest

router = APIRouter(prefix="/api/invoices", tags=["review"])


def _load(db: Session, invoice_id: uuid.UUID) -> Invoice | None:
    return (
        db.query(Invoice)
        .filter(Invoice.id == invoice_id)
        .options(
            selectinload(Invoice.contract),
            selectinload(Invoice.timesheet),
            selectinload(Invoice.documents),
            selectinload(Invoice.anomalies),
            selectinload(Invoice.review),
        )
        .first()
    )


@router.post("/{invoice_id}/review", response_model=InvoiceDetail)
def review_invoice(
    invoice_id: uuid.UUID,
    body: ReviewRequest,
    db: Session = Depends(get_db),
) -> Invoice:
    invoice = _load(db, invoice_id)
    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found."
        )

    if invoice.processing_status != ProcessingStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Analysis must complete before the invoice can be reviewed.",
        )

    if invoice.review is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invoice has already been reviewed.",
        )

    if body.decision == ReviewDecision.REJECTED and not (body.reason and body.reason.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A reason is required when rejecting an invoice.",
        )

    decision = (
        BusinessStatus.APPROVED
        if body.decision == ReviewDecision.APPROVED
        else BusinessStatus.REJECTED
    )
    invoice.status = decision
    db.add(
        Review(
            invoice_id=invoice.id,
            decision=body.decision,
            reason=body.reason.strip() if body.reason else None,
        )
    )
    db.commit()
    return _load(db, invoice_id)
