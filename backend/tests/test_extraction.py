"""Extraction service tests (PRD §14, §15).

The AI client is mocked so tests are deterministic and offline; Pydantic
validation of the structured output is still exercised.
"""

from unittest.mock import patch

import pytest

from app.schemas.extraction import ContractExtraction, InvoiceExtraction
from app.services import extraction_service


def _invoice_model(**over) -> InvoiceExtraction:
    data = dict(
        invoice_number="INV-1042",
        vendor_name="Acme Technologies",
        invoice_date="2026-08-20",
        due_date="2026-09-20",
        currency="usd",
        subtotal=9000,
        tax=0,
        total=9000,
        line_items=[{"description": "Software Development", "quantity": 120,
                     "unit_price": 75, "amount": 9000}],
    )
    data.update(over)
    return InvoiceExtraction(**data)


def _contract_model(**over) -> ContractExtraction:
    data = dict(
        vendor_name="Acme Technologies",
        contract_start="2026-01-01",
        contract_end="2026-12-31",
        hourly_rate=50,
        max_hours=100,
        max_amount=5000,
        currency="USD",
        payment_terms="Net 30",
    )
    data.update(over)
    return ContractExtraction(**data)


def test_invoice_pydantic_validates_and_normalizes():
    m = _invoice_model()
    assert m.currency == "USD"          # normalized uppercase
    assert m.invoice_date is not None   # ISO date parsed
    assert m.total == 9000
    assert len(m.line_items) == 1


def test_invoice_date_us_format():
    m = _invoice_model(invoice_date="08/20/2026")
    assert m.invoice_date is not None
    assert m.invoice_date.year == 2026 and m.invoice_date.month == 8


def test_invoice_bad_currency_becomes_none():
    m = _invoice_model(currency="dollars")
    assert m.currency is None


def test_contract_pydantic_validates():
    m = _contract_model()
    assert m.hourly_rate == 50
    assert m.max_hours == 100
    assert m.max_amount == 5000
    assert m.contract_start is not None


def test_invoice_hours_and_rate_derived(db_session, tmp_path):
    from tests.helpers import make_pdf

    from app.models import Invoice, Document
    from app.models.enums import DocumentType

    pdf = make_pdf(["INVOICE INV-1042", "Acme Technologies", "Total 9000"],
                   str(tmp_path / "inv.pdf"))
    invoice = Invoice()
    db_session.add(invoice)
    db_session.flush()
    db_session.add(Document(invoice_id=invoice.id,
                            document_type=DocumentType.INVOICE,
                            file_name="inv.pdf", file_path=pdf))
    db_session.commit()

    with patch.object(extraction_service.ai_client, "extract_structured",
                      return_value=_invoice_model()):
        facts = extraction_service.extract_and_persist_invoice(db_session, invoice)
    db_session.commit()

    db_session.refresh(invoice)
    assert invoice.vendor_name == "Acme Technologies"
    assert float(invoice.total) == 9000.0
    assert facts.hours == 120.0
    assert facts.hourly_rate == 75.0


def test_invoice_missing_required_fields_raises(db_session, tmp_path):
    from tests.helpers import make_pdf

    from app.models import Invoice, Document
    from app.models.enums import DocumentType

    pdf = make_pdf(["blank invoice"], str(tmp_path / "inv.pdf"))
    invoice = Invoice()
    db_session.add(invoice)
    db_session.flush()
    db_session.add(Document(invoice_id=invoice.id,
                            document_type=DocumentType.INVOICE,
                            file_name="inv.pdf", file_path=pdf))
    db_session.commit()

    # total missing -> cannot reliably extract
    bad = _invoice_model(total=None)
    with patch.object(extraction_service.ai_client, "extract_structured",
                      return_value=bad):
        with pytest.raises(extraction_service.ExtractionError):
            extraction_service.extract_and_persist_invoice(db_session, invoice)


def test_contract_extraction_persists(db_session, tmp_path):
    from tests.helpers import make_pdf

    from app.models import Contract, Invoice, Document
    from app.models.enums import DocumentType

    pdf = make_pdf(["MASTER SERVICES AGREEMENT", "Acme Technologies",
                    "Rate $50/hr"], str(tmp_path / "c.pdf"))
    invoice = Invoice()
    db_session.add(invoice)
    db_session.flush()
    db_session.add(Document(invoice_id=invoice.id,
                            document_type=DocumentType.CONTRACT,
                            file_name="c.pdf", file_path=pdf))
    db_session.commit()

    with patch.object(extraction_service.ai_client, "extract_structured",
                      return_value=_contract_model()):
        extraction_service.extract_and_persist_contract(db_session, invoice)
    db_session.commit()

    contract = db_session.query(Contract).filter_by(invoice_id=invoice.id).one()
    assert contract.vendor_name == "Acme Technologies"
    assert float(contract.hourly_rate) == 50.0
    assert float(contract.max_amount) == 5000.0


def test_ai_unavailable_raises_extraction_error(db_session, tmp_path):
    from app.ai.client import AIUnavailableError
    from tests.helpers import make_pdf

    from app.models import Invoice, Document
    from app.models.enums import DocumentType

    pdf = make_pdf(["invoice"], str(tmp_path / "inv.pdf"))
    invoice = Invoice()
    db_session.add(invoice)
    db_session.flush()
    db_session.add(Document(invoice_id=invoice.id,
                            document_type=DocumentType.INVOICE,
                            file_name="inv.pdf", file_path=pdf))
    db_session.commit()

    with patch.object(extraction_service.ai_client, "extract_structured",
                      side_effect=AIUnavailableError("not configured")):
        with pytest.raises(extraction_service.ExtractionError) as exc:
            extraction_service.extract_and_persist_invoice(db_session, invoice)
        assert "not configured" in str(exc.value)


def test_image_invoice_uses_vision_path(db_session, tmp_path):
    """PNG invoices go through the image/vision call, not PDF text."""
    import app.services.document_service as doc_service

    from app.models import Invoice, Document
    from app.models.enums import DocumentType

    png = tmp_path / "inv.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 64)  # minimal png-ish bytes
    invoice = Invoice()
    db_session.add(invoice)
    db_session.flush()
    db_session.add(Document(invoice_id=invoice.id,
                            document_type=DocumentType.INVOICE,
                            file_name="inv.png", file_path=str(png)))
    db_session.commit()

    captured = {}

    def fake_extract(model, system, user, image_base64=None, image_media_type="image/png"):
        captured["image"] = image_base64
        captured["media"] = image_media_type
        return _invoice_model()

    with patch.object(extraction_service.ai_client, "extract_structured",
                      side_effect=fake_extract):
        extraction_service.extract_and_persist_invoice(db_session, invoice)

    assert captured["image"] is not None
    assert captured["media"] == "image/png"
