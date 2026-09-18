"""CSV export (P2, PRD §48) — deterministic analysis data only."""

import csv
import io
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Invoice

router = APIRouter(prefix="/api/invoices", tags=["export"])


@router.get("/{invoice_id}/export")
def export_invoice(invoice_id: uuid.UUID, db: Session = Depends(get_db)) -> Response:
    invoice = (
        db.query(Invoice)
        .filter(Invoice.id == invoice_id)
        .options(
            selectinload(Invoice.contract),
            selectinload(Invoice.timesheet),
            selectinload(Invoice.anomalies),
        )
        .first()
    )
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Invoice not found.")

    buffer = io.StringIO()
    writer = csv.writer(buffer)

    writer.writerow(["InvoiceIQ Analysis Export"])
    writer.writerow([])
    writer.writerow(["Section", "Field", "Value"])
    writer.writerow(["Invoice", "Invoice number", invoice.invoice_number or ""])
    writer.writerow(["Invoice", "Vendor", invoice.vendor_name or ""])
    writer.writerow(["Invoice", "Invoice date", invoice.invoice_date or ""])
    writer.writerow(["Invoice", "Currency", invoice.currency or ""])
    writer.writerow(["Invoice", "Subtotal", invoice.subtotal or ""])
    writer.writerow(["Invoice", "Tax", invoice.tax or ""])
    writer.writerow(["Invoice", "Total", invoice.total or ""])
    writer.writerow(["Invoice", "Business status", invoice.status.value])
    writer.writerow(["Invoice", "Risk score", invoice.risk_score if invoice.risk_score is not None else ""])
    writer.writerow(["Invoice", "Risk level", invoice.risk_level.value if invoice.risk_level else ""])
    writer.writerow(["Invoice", "Extraction coverage", invoice.extraction_coverage or ""])

    if invoice.contract:
        c = invoice.contract
        writer.writerow(["Contract", "Vendor", c.vendor_name or ""])
        writer.writerow(["Contract", "Period", f"{c.start_date or ''} to {c.end_date or ''}"])
        writer.writerow(["Contract", "Hourly rate", c.hourly_rate or ""])
        writer.writerow(["Contract", "Maximum hours", c.max_hours or ""])
        writer.writerow(["Contract", "Maximum amount", c.max_amount or ""])

    writer.writerow(["Timesheet", "Recorded hours",
                     invoice.timesheet.total_hours if invoice.timesheet else "Not provided"])

    writer.writerow([])
    writer.writerow(["Verification checks"])
    writer.writerow(["Check", "Status", "Detail"])
    for check in invoice.verification_checks or []:
        writer.writerow([check.get("label", ""), check.get("status", ""), check.get("detail", "")])

    writer.writerow([])
    writer.writerow(["Anomalies"])
    writer.writerow(["Type", "Severity", "Title", "Points", "Evidence"])
    for anomaly in invoice.anomalies:
        writer.writerow([
            anomaly.type,
            anomaly.severity.value,
            anomaly.title,
            anomaly.points,
            str(anomaly.evidence),
        ])

    filename = f"invoiceiq_{invoice.invoice_number or invoice_id}.csv"
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
