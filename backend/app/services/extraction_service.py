"""AI document extraction service (PRD §14, §15, §36).

Flow per document:
  1. Read the stored file (PDF -> text via PyMuPDF; image -> base64 vision).
  2. Call the LLM with Structured Outputs.
  3. Validate the response with Pydantic (already enforced by parse()).
  4. Require a minimum set of fields; otherwise the document is considered
     unparseable rather than silently producing empty data.
  5. Persist the verified, structured facts onto the ORM row.

The LLM NEVER computes risk, comparisons, or totals — that is deterministic
backend code.
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.ai import prompts
from app.ai.client import AIUnavailableError, ai_client
from app.models import Contract, Invoice
from app.schemas.extraction import (
    ContractExtraction,
    InvoiceExtraction,
    dec,
)
from app.services import document_service


class ExtractionError(Exception):
    """Raised when required information cannot be reliably extracted."""


def extraction_coverage(invoice: "Invoice", contract: "Contract") -> float:
    """Deterministic fraction (0-1) of expected fields successfully extracted.

    This is a field-presence measure computed by the backend — NOT an AI
    confidence score (PRD §47: extraction confidence). It tells the reviewer
    how complete the structured extraction was.
    """
    def present(value) -> bool:
        if value is None:
            return False
        if isinstance(value, (list, str)):
            return len(value) > 0
        return True

    invoice_fields = [
        invoice.invoice_number, invoice.vendor_name, invoice.invoice_date,
        invoice.due_date, invoice.currency, invoice.subtotal, invoice.tax,
        invoice.total, invoice.line_items,
    ]
    contract_fields = [
        contract.vendor_name if contract else None,
        contract.start_date if contract else None,
        contract.end_date if contract else None,
        contract.hourly_rate if contract else None,
        contract.max_hours if contract else None,
        contract.max_amount if contract else None,
        contract.currency if contract else None,
    ]
    fields = invoice_fields + contract_fields
    present_count = sum(1 for f in fields if present(f))
    return round(present_count / len(fields), 2)


@dataclass
class InvoiceFacts:
    """Aggregated invoice facts used by the verification stage."""

    hours: float | None = None
    hourly_rate: float | None = None


def _extract_invoice_model(file_path: str) -> InvoiceExtraction:
    if document_service.is_image_file(file_path):
        image_b64 = document_service.read_image_base64(file_path)
        media_type = document_service.image_media_type(file_path)
        result = ai_client.extract_structured(
            InvoiceExtraction,
            prompts.INVOICE_SYSTEM,
            prompts.INVOICE_USER.format(document_text="[see attached image]"),
            image_base64=image_b64,
            image_media_type=media_type,
        )
    else:
        text = document_service.read_document_text(file_path)
        result = ai_client.extract_structured(
            InvoiceExtraction,
            prompts.INVOICE_SYSTEM,
            prompts.INVOICE_USER.format(document_text=text),
        )
    return result


def _extract_contract_model(file_path: str) -> ContractExtraction:
    text = document_service.read_document_text(file_path)
    return ai_client.extract_structured(
        ContractExtraction,
        prompts.CONTRACT_SYSTEM,
        prompts.CONTRACT_USER.format(document_text=text),
    )


def _document_path(db: Session, invoice_id, document_type) -> str | None:
    from app.models import Document

    doc = (
        db.query(Document)
        .filter(
            Document.invoice_id == invoice_id,
            Document.document_type == document_type,
        )
        .order_by(Document.created_at.desc())
        .first()
    )
    return doc.file_path if doc else None


def extract_and_persist_invoice(db: Session, invoice: Invoice) -> InvoiceFacts:
    """Extract invoice fields and persist them onto the invoice row.

    Raises ExtractionError if AI is unavailable, the file is unreadable, or
    essential fields (vendor / total) could not be extracted.
    """
    from app.models.enums import DocumentType

    file_path = _document_path(db, invoice.id, DocumentType.INVOICE)
    if not file_path:
        raise ExtractionError("Invoice document not found.")

    try:
        extracted = _extract_invoice_model(file_path)
    except document_service.DocumentParseError as exc:
        raise ExtractionError(
            "We couldn't read the invoice document. Please try a supported PDF, PNG or JPG."
        ) from exc
    except AIUnavailableError as exc:
        # Re-raise so the pipeline can surface a 503 / demo-mode fallback.
        raise ExtractionError(str(exc)) from exc

    if not extracted.vendor_name or extracted.total is None:
        raise ExtractionError(
            "We couldn't reliably extract the required information from the invoice. "
            "Please review the document and try again."
        )

    invoice.invoice_number = extracted.invoice_number
    invoice.vendor_name = extracted.vendor_name
    invoice.invoice_date = extracted.invoice_date
    invoice.due_date = extracted.due_date
    invoice.currency = extracted.currency
    invoice.subtotal = dec(extracted.subtotal)
    invoice.tax = dec(extracted.tax)
    invoice.total = dec(extracted.total)
    invoice.line_items = [item.model_dump() for item in extracted.line_items]

    # Deterministically derive billed hours and effective hourly rate from
    # structured line items (the AI only reads numbers; it does not decide).
    hours = None
    rate = None
    quantity_items = [li for li in extracted.line_items if li.quantity is not None]
    if quantity_items:
        hours = round(sum(li.quantity or 0 for li in quantity_items), 2)
        priced = [li.unit_price for li in quantity_items if li.unit_price is not None]
        if priced:
            rate = round(max(priced), 2)  # effective billed hourly rate

    return InvoiceFacts(hours=hours, hourly_rate=rate)


def extract_and_persist_contract(db: Session, invoice: Invoice) -> None:
    """Extract contract terms and persist them onto the contract row."""
    from app.models.enums import DocumentType

    file_path = _document_path(db, invoice.id, DocumentType.CONTRACT)
    if not file_path:
        raise ExtractionError("Contract document not found.")

    try:
        extracted = _extract_contract_model(file_path)
    except document_service.DocumentParseError as exc:
        raise ExtractionError(
            "We couldn't read the contract document. Please upload a supported PDF."
        ) from exc
    except AIUnavailableError as exc:
        raise ExtractionError(str(exc)) from exc

    if not extracted.vendor_name or extracted.hourly_rate is None:
        raise ExtractionError(
            "We couldn't reliably extract the required contract terms "
            "(vendor and hourly rate). Please review the document and try again."
        )

    contract = (
        db.query(Contract).filter(Contract.invoice_id == invoice.id).one_or_none()
    )
    if contract is None:
        contract = Contract(invoice_id=invoice.id)
        db.add(contract)

    contract.vendor_name = extracted.vendor_name
    contract.start_date = extracted.contract_start
    contract.end_date = extracted.contract_end
    contract.hourly_rate = dec(extracted.hourly_rate)
    contract.max_hours = dec(extracted.max_hours)
    contract.max_amount = dec(extracted.max_amount)
    contract.currency = extracted.currency
    contract.payment_terms = extracted.payment_terms
