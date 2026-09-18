"""End-to-end historical analysis via the API (PRD §19)."""

from unittest.mock import patch

from app.schemas.extraction import ContractExtraction, InvoiceExtraction
from app.services import extraction_service
from tests.helpers import make_pdf


def _fake_extract(total=5000):
    def _f(model, system, user, **kwargs):
        if model is ContractExtraction:
            return ContractExtraction(
                vendor_name="Acme Technologies", contract_start="2026-01-01",
                contract_end="2026-12-31", hourly_rate=50, max_hours=1000,
                max_amount=100000, currency="USD",
            )
        return InvoiceExtraction(
            invoice_number="INV-1", vendor_name="Acme Technologies",
            invoice_date="2026-08-20", due_date="2026-09-20", currency="USD",
            subtotal=total, tax=0, total=total,
            line_items=[{"description": "Dev", "quantity": total / 50,
                         "unit_price": 50, "amount": total}],
        )
    return _f


def _upload_and_analyze(client, tmp_path, total, tag):
    inv = make_pdf(["INVOICE Acme"], str(tmp_path / f"i{tag}.pdf"))
    con = make_pdf(["CONTRACT Acme"], str(tmp_path / f"c{tag}.pdf"))
    with open(inv, "rb") as a, open(con, "rb") as b:
        up = client.post(
            "/api/invoices/upload",
            files={"invoice": ("i.pdf", a, "application/pdf"),
                   "contract": ("c.pdf", b, "application/pdf")},
        )
    iid = up.json()["invoice_id"]
    with patch.object(extraction_service.ai_client, "extract_structured",
                      side_effect=_fake_extract(total)):
        r = client.post(f"/api/invoices/{iid}/analyze")
    assert r.status_code == 200
    return r.json()


def test_third_large_invoice_flags_unusual_amount(client, tmp_path):
    # Two normal ~5,000 invoices build history...
    _upload_and_analyze(client, tmp_path, 5000, "1")
    _upload_and_analyze(client, tmp_path, 5400, "2")
    # ...then a 12,000 invoice for the same vendor.
    result = _upload_and_analyze(client, tmp_path, 12000, "3")

    types = {a["type"] for a in result["anomalies"]}
    assert "UNUSUAL_AMOUNT" in types
    assert result["historical"] is not None
    assert result["historical"]["prior_invoice_count"] == 2
    assert result["historical"]["average_amount"] == 5200.0


def test_first_invoices_have_no_historical_anomaly(client, tmp_path):
    result = _upload_and_analyze(client, tmp_path, 12000, "1")
    assert "UNUSUAL_AMOUNT" not in {a["type"] for a in result["anomalies"]}
    assert result["historical"] is None
