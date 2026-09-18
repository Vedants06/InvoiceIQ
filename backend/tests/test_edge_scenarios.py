"""End-to-end edge-case scenarios (PRD §54): currency mismatch, arithmetic
mismatch — run through the full analyze pipeline with a mocked AI."""

from unittest.mock import patch

from app.schemas.extraction import ContractExtraction, InvoiceExtraction
from app.services import extraction_service
from tests.helpers import make_pdf


def _upload(client, tmp_path, tag):
    inv = make_pdf(["INVOICE"], str(tmp_path / f"i{tag}.pdf"))
    con = make_pdf(["CONTRACT"], str(tmp_path / f"c{tag}.pdf"))
    with open(inv, "rb") as a, open(con, "rb") as b:
        up = client.post(
            "/api/invoices/upload",
            files={"invoice": ("i.pdf", a, "application/pdf"),
                   "contract": ("c.pdf", b, "application/pdf")},
        )
    assert up.status_code == 201, up.text
    return up.json()["invoice_id"]


def _analyze(client, iid, invoice_extraction, contract_extraction):
    def fake(model, system, user, **kwargs):
        return contract_extraction if model is ContractExtraction else invoice_extraction

    with patch.object(extraction_service.ai_client, "extract_structured", side_effect=fake):
        return client.post(f"/api/invoices/{iid}/analyze")


def test_currency_mismatch_marks_money_checks_not_performed(client, tmp_path):
    """PRD §17.3/§17.6: no currency conversion — monetary comparisons become
    unavailable rather than incorrectly performed."""
    invoice_ext = InvoiceExtraction(
        invoice_number="INV-EUR", vendor_name="Acme",
        invoice_date="2026-08-20", currency="EUR",
        subtotal=6000, tax=0, total=6000,
        line_items=[{"description": "Dev", "quantity": 80, "unit_price": 75,
                     "amount": 6000}],
    )
    contract_ext = ContractExtraction(
        vendor_name="Acme", contract_start="2026-01-01", contract_end="2026-12-31",
        hourly_rate=50, max_hours=100, max_amount=5000, currency="USD",
    )
    iid = _upload(client, tmp_path, "cur")
    resp = _analyze(client, iid, invoice_ext, contract_ext)
    assert resp.status_code == 200, resp.text
    body = resp.json()

    types = {a["type"] for a in body["anomalies"]}
    assert "CURRENCY_MISMATCH" in types
    # No conversion: rate/amount comparisons must NOT be reported as anomalies
    assert "RATE_MISMATCH" not in types
    assert "CONTRACT_AMOUNT_EXCEEDED" not in types
    # And their checks are NOT_PERFORMED, not failed
    checks = {c["key"]: c["status"] for c in body["verification_checks"]}
    assert checks["currency"] == "FAILED"
    assert checks["rate"] == "NOT_PERFORMED"
    assert checks["amount"] == "NOT_PERFORMED"
    # Currency mismatch alone = 20 points
    assert body["risk_score"] == 20


def test_arithmetic_mismatch_detected(client, tmp_path):
    """PRD §17.7: qty x unit price != line amount flags CALCULATION_MISMATCH."""
    invoice_ext = InvoiceExtraction(
        invoice_number="INV-CALC", vendor_name="Acme",
        invoice_date="2026-08-20", currency="USD",
        subtotal=500, tax=0, total=500,
        line_items=[{"description": "Dev", "quantity": 10, "unit_price": 100,
                     "amount": 500}],  # 10*100 = 1000, not 500
    )
    contract_ext = ContractExtraction(
        vendor_name="Acme", contract_start="2026-01-01", contract_end="2026-12-31",
        hourly_rate=100, max_hours=1000, max_amount=100000, currency="USD",
    )
    iid = _upload(client, tmp_path, "calc")
    resp = _analyze(client, iid, invoice_ext, contract_ext)
    assert resp.status_code == 200, resp.text
    body = resp.json()

    types = {a["type"] for a in body["anomalies"]}
    assert "CALCULATION_MISMATCH" in types
    calc = next(a for a in body["anomalies"] if a["type"] == "CALCULATION_MISMATCH")
    assert calc["points"] == 15
    assert calc["evidence"]
    assert body["risk_score"] == 15
    checks = {c["key"]: c["status"] for c in body["verification_checks"]}
    assert checks["arithmetic"] == "FAILED"


def test_valid_arithmetic_with_tax_passes(client, tmp_path):
    """Tax must not cause a false arithmetic failure (PRD §17.7)."""
    invoice_ext = InvoiceExtraction(
        invoice_number="INV-TAX", vendor_name="Acme",
        invoice_date="2026-08-20", currency="USD",
        subtotal=1000, tax=200, total=1200,
        line_items=[{"description": "Dev", "quantity": 10, "unit_price": 100,
                     "amount": 1000}],
    )
    contract_ext = ContractExtraction(
        vendor_name="Acme", contract_start="2026-01-01", contract_end="2026-12-31",
        hourly_rate=100, max_hours=1000, max_amount=100000, currency="USD",
    )
    iid = _upload(client, tmp_path, "tax")
    resp = _analyze(client, iid, invoice_ext, contract_ext)
    body = resp.json()
    checks = {c["key"]: c["status"] for c in body["verification_checks"]}
    assert checks["arithmetic"] == "PASSED"
    assert "CALCULATION_MISMATCH" not in {a["type"] for a in body["anomalies"]}
