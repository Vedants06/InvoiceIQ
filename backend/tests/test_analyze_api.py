"""Analyze pipeline endpoint tests (PRD §32, §34).

Uses real text PDFs and a mocked AI client so the full pipeline —
extraction -> verification -> reconciliation -> anomalies -> risk ->
explanation — runs deterministically offline.
"""

from contextlib import ExitStack
from unittest.mock import PropertyMock, patch

from app.schemas.extraction import ContractExtraction, InvoiceExtraction
from app.services import extraction_service
from tests.helpers import make_pdf


def _fake_extract(model, system, user, **kwargs):
    if model is ContractExtraction:
        return ContractExtraction(
            vendor_name="Acme Technologies",
            contract_start="2026-01-01",
            contract_end="2026-12-31",
            hourly_rate=50,
            max_hours=100,
            max_amount=5000,
            currency="USD",
            payment_terms="Net 30",
        )
    return InvoiceExtraction(
        invoice_number="INV-1042",
        vendor_name="Acme Technologies",
        invoice_date="2026-08-20",
        due_date="2026-09-20",
        currency="USD",
        subtotal=9000,
        tax=0,
        total=9000,
        line_items=[{"description": "Software Development", "quantity": 120,
                     "unit_price": 75, "amount": 9000}],
    )


def _upload(client, tmp_path, hours_csv="55\n40"):
    inv_pdf = make_pdf(["INVOICE INV-1042", "Acme Technologies", "Total due 9000"],
                       str(tmp_path / "inv.pdf"))
    con_pdf = make_pdf(["AGREEMENT", "Acme Technologies", "Hourly rate 50",
                        "Maximum hours 100", "Maximum amount 5000"],
                       str(tmp_path / "con.pdf"))
    files = {
        "invoice": ("inv.pdf", open(inv_pdf, "rb"), "application/pdf"),
        "contract": ("con.pdf", open(con_pdf, "rb"), "application/pdf"),
    }
    if hours_csv is not None:
        ts = tmp_path / "ts.csv"
        ts.write_text(f"Employee,Date,Hours\nJohn,2026-08-01,{hours_csv.splitlines()[0]}\n"
                      f"Sarah,2026-08-02,{hours_csv.splitlines()[1]}\n")
        files["timesheet"] = ("ts.csv", open(ts, "rb"), "text/csv")
    resp = client.post("/api/invoices/upload", files=files)
    for f in files.values():
        f[1].close()
    assert resp.status_code == 201, resp.text
    return resp.json()["invoice_id"]


def test_critical_scenario_pipeline(client, tmp_path):
    """Scenario 2: rate + hours + amount + timesheet -> 90 CRITICAL."""
    invoice_id = _upload(client, tmp_path, hours_csv="55\n40")  # 95 recorded
    with patch.object(extraction_service.ai_client, "extract_structured",
                      side_effect=_fake_extract):
        resp = client.post(f"/api/invoices/{invoice_id}/analyze")
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["processing_status"] == "COMPLETED"
    assert body["risk_score"] == 90
    assert body["risk_level"] == "CRITICAL"

    anomaly_types = {a["type"] for a in body["anomalies"]}
    assert anomaly_types == {
        "RATE_MISMATCH", "EXCESSIVE_HOURS",
        "CONTRACT_AMOUNT_EXCEEDED", "TIMESHEET_MISMATCH",
    }
    # Every anomaly carries structured evidence
    for a in body["anomalies"]:
        assert a["evidence"]
    # Rate anomaly evidence shows the two rates
    rate = next(a for a in body["anomalies"] if a["type"] == "RATE_MISMATCH")
    assert rate["evidence"]["invoice_rate"] == 75
    assert rate["evidence"]["contract_rate"] == 50

    # Verification summary includes all checks; timesheet failed
    checks = {c["key"]: c["status"] for c in body["verification_checks"]}
    assert checks["vendor"] == "PASSED"
    assert checks["rate"] == "FAILED"
    assert checks["timesheet"] == "FAILED"
    assert checks["arithmetic"] == "PASSED"
    # Deterministic extraction coverage (field-presence measure)
    assert body["extraction_coverage"] is not None
    assert 0.0 < body["extraction_coverage"] <= 1.0


def test_missing_timesheet_is_not_performed_not_pass(client, tmp_path):
    invoice_id = _upload(client, tmp_path, hours_csv=None)
    with patch.object(extraction_service.ai_client, "extract_structured",
                      side_effect=_fake_extract):
        resp = client.post(f"/api/invoices/{invoice_id}/analyze")
    body = resp.json()
    checks = {c["key"]: c["status"] for c in body["verification_checks"]}
    assert checks["timesheet"] == "NOT_PERFORMED"
    assert body["timesheet"] is None
    # No timesheet anomaly (missing evidence != finding)
    assert "TIMESHEET_MISMATCH" not in {a["type"] for a in body["anomalies"]}


def test_explanation_unavailable_when_ai_not_configured(client, tmp_path):
    """AI explanation failure must not fail the analysis (PRD §25)."""
    invoice_id = _upload(client, tmp_path)
    with patch.object(extraction_service.ai_client, "extract_structured",
                      side_effect=_fake_extract):
        resp = client.post(f"/api/invoices/{invoice_id}/analyze")
    body = resp.json()
    assert resp.status_code == 200
    assert body["explanation_available"] is False
    assert body["explanation"] is None
    # Deterministic results are still present
    assert body["risk_score"] == 90


def _patch_ai_explanation(text=None, failure=False):
    """Patches for the shared AIClient singleton used by both services."""
    from app.ai.client import AIClient, AIUnavailableError

    def fake_text(system, prompt):
        if failure:
            raise AIUnavailableError("boom")
        return text or "Manual review is required: multiple inconsistencies were found."

    return [
        patch.object(AIClient, "is_configured", new_callable=PropertyMock,
                     return_value=True),
        patch("app.services.extraction_service.ai_client.extract_structured",
              side_effect=_fake_extract),
        patch("app.services.explanation_service.ai_client.generate_text",
              side_effect=fake_text),
    ]


def test_explanation_generated_when_ai_available(client, tmp_path):
    invoice_id = _upload(client, tmp_path)
    with ExitStack() as stack:
        for p in _patch_ai_explanation():
            stack.enter_context(p)
        resp = client.post(f"/api/invoices/{invoice_id}/analyze")
    body = resp.json()
    assert resp.status_code == 200
    assert body["explanation_available"] is True
    assert "Manual review" in body["explanation"]


def test_explanation_generation_failure_still_succeeds(client, tmp_path):
    invoice_id = _upload(client, tmp_path)
    with ExitStack() as stack:
        for p in _patch_ai_explanation(failure=True):
            stack.enter_context(p)
        resp = client.post(f"/api/invoices/{invoice_id}/analyze")
    body = resp.json()
    assert resp.status_code == 200
    assert body["explanation_available"] is False
    assert body["risk_score"] == 90


def test_ai_unavailable_returns_503(client, tmp_path):
    from app.ai.client import AIUnavailableError

    invoice_id = _upload(client, tmp_path)
    with patch.object(extraction_service.ai_client, "extract_structured",
                      side_effect=AIUnavailableError("not configured")):
        resp = client.post(f"/api/invoices/{invoice_id}/analyze")
    assert resp.status_code == 503
    detail = client.get(f"/api/invoices/{invoice_id}").json()
    assert detail["processing_status"] == "FAILED"


def test_unknown_invoice_404(client):
    resp = client.post("/api/invoices/00000000-0000-0000-0000-000000000000/analyze")
    assert resp.status_code == 404
