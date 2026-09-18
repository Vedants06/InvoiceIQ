"""Invoice API endpoints (PRD §34).

Implemented in this step:
  POST /api/invoices/upload   — receive invoice + contract (+ optional
                                timesheet), store files, create records
  GET  /api/invoices          — list with optional filters
  GET  /api/invoices/{id}     — full invoice detail

The analyze and review endpoints are added by later steps.
"""

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Contract, Document, Invoice
from app.models.enums import BusinessStatus, DocumentType, RiskLevel
from app.schemas.invoice import InvoiceDetail, InvoiceSummary, UploadResponse
from app.services import document_service

router = APIRouter(prefix="/api/invoices", tags=["invoices"])


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_invoice(
    invoice: UploadFile = File(...),
    contract: UploadFile | None = File(None),
    timesheet: UploadFile | None = File(None),
    db: Session = Depends(get_db),
) -> UploadResponse:
    if contract is None or not contract.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contract information is required for full verification.",
        )

    invoice_row = Invoice()
    db.add(invoice_row)
    db.flush()  # assign invoice_row.id

    try:
        # 1. Invoice file
        invoice_path, invoice_name, invoice_mime = document_service.save_upload(
            invoice_row.id, DocumentType.INVOICE, invoice
        )
        db.add(
            Document(
                invoice_id=invoice_row.id,
                document_type=DocumentType.INVOICE,
                file_name=invoice_name,
                file_path=invoice_path,
                mime_type=invoice_mime,
            )
        )

        # 2. Contract file
        contract_path, contract_name, contract_mime = document_service.save_upload(
            invoice_row.id, DocumentType.CONTRACT, contract
        )
        db.add(
            Document(
                invoice_id=invoice_row.id,
                document_type=DocumentType.CONTRACT,
                file_name=contract_name,
                file_path=contract_path,
                mime_type=contract_mime,
            )
        )
        # Placeholder contract row linked to this invoice; extracted fields are
        # populated during analysis.
        db.add(Contract(invoice_id=invoice_row.id))

        # 3. Optional timesheet
        has_timesheet = bool(timesheet and timesheet.filename)
        if has_timesheet:
            ts_path, ts_name, ts_mime = document_service.save_upload(
                invoice_row.id, DocumentType.TIMESHEET, timesheet
            )
            db.add(
                Document(
                    invoice_id=invoice_row.id,
                    document_type=DocumentType.TIMESHEET,
                    file_name=ts_name,
                    file_path=ts_path,
                    mime_type=ts_mime,
                )
            )

        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to process this file. Please try again.",
        )

    return UploadResponse(
        invoice_id=invoice_row.id,
        status="uploaded",
        has_timesheet=has_timesheet,
    )


@router.get("", response_model=list[InvoiceSummary])
def list_invoices(
    status_filter: BusinessStatus | None = None,
    risk_level: RiskLevel | None = None,
    vendor: str | None = None,
    db: Session = Depends(get_db),
) -> list[Invoice]:
    stmt = (
        select(Invoice)
        .order_by(Invoice.created_at.desc())
        .options(selectinload(Invoice.timesheet))
    )
    if status_filter is not None:
        stmt = stmt.where(Invoice.status == status_filter)
    if risk_level is not None:
        stmt = stmt.where(Invoice.risk_level == risk_level)
    if vendor:
        stmt = stmt.where(Invoice.vendor_name.ilike(f"%{vendor}%"))

    invoices = list(db.scalars(stmt).all())
    # Attach the computed has_timesheet flag for the summary schema
    for inv in invoices:
        inv.has_timesheet = inv.timesheet is not None  # type: ignore[attr-defined]
    return invoices


@router.get("/{invoice_id}", response_model=InvoiceDetail)
def get_invoice(
    invoice_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> Invoice:
    stmt = (
        select(Invoice)
        .where(Invoice.id == invoice_id)
        .options(
            selectinload(Invoice.contract),
            selectinload(Invoice.timesheet),
            selectinload(Invoice.documents),
            selectinload(Invoice.anomalies),
            selectinload(Invoice.review),
        )
    )
    invoice = db.scalars(stmt).first()
    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found."
        )
    return invoice
