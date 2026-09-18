"""Review & dashboard stats endpoint tests (PRD §28, §11)."""

from unittest.mock import patch

from app.schemas.extraction import ContractExtraction, InvoiceExtraction
from app.services import extraction_service
from tests.helpers import make_pdf


def _fake_extract(model, system, user, **kwargs):
    if model is ContractExtraction:
        return ContractExtraction(
            vendor_name="Acme Technologies", contract_start="2026-01-01",
            contract_end="2026-12-31", hourly_rate=50, max_hours=100,
            max_amount=5000, currency="USD",
        )
    return InvoiceExtraction(
        invoice_number="INV-1042", vendor_name="Acme Technologies",
        invoice_date="2026-08-20", due_date="2026-09-20", currency="USD",
        subtotal=9000, tax=0, total=9000,
        line_items=[{"description": "Dev", "quantity": 120,
                     "unit_price": 75, "amount": 9000}],
    )


def _analyzed_invoice(client, tmp_path, include_timesheet=True, tag=""):
    inv = make_pdf(["INVOICE INV-1042", "Acme", "Total 9000"], str(tmp_path / f"i{tag}.pdf"))
    con = make_pdf(["AGREEMENT", "Acme", "Rate 50"], str(tmp_path / f"c{tag}.pdf"))
    files = {
        "invoice": ("i.pdf", open(inv, "rb"), "application/pdf"),
        "contract": ("c.pdf", open(con, "rb"), "application/pdf"),
    }
    if include_timesheet:
        ts = tmp_path / f"t{tag}.csv"
        ts.write_text("Employee,Date,Hours\nJohn,2026-08-01,95\n")
        files["timesheet"] = ("t.csv", open(ts, "rb"), "text/csv")
    up = client.post("/api/invoices/upload", files=files)
    for f in files.values():
        f[1].close()
    invoice_id = up.json()["invoice_id"]
    with patch.object(extraction_service.ai_client, "extract_structured",
                      side_effect=_fake_extract):
        r = client.post(f"/api/invoices/{invoice_id}/analyze")
    assert r.status_code == 200
    return invoice_id


def test_approve_invoice(client, tmp_path):
    invoice_id = _analyzed_invoice(client, tmp_path)
    r = client.post(f"/api/invoices/{invoice_id}/review",
                    json={"decision": "APPROVED", "reason": "Verified manually"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "APPROVED"
    assert body["review"]["decision"] == "APPROVED"
    assert body["review"]["reason"] == "Verified manually"
    assert body["review"]["reviewed_at"] is not None


def test_reject_requires_reason(client, tmp_path):
    invoice_id = _analyzed_invoice(client, tmp_path)
    r = client.post(f"/api/invoices/{invoice_id}/review", json={"decision": "REJECTED"})
    assert r.status_code == 400
    assert "reason" in r.json()["detail"].lower()


def test_reject_with_reason(client, tmp_path):
    invoice_id = _analyzed_invoice(client, tmp_path)
    r = client.post(f"/api/invoices/{invoice_id}/review",
                    json={"decision": "REJECTED", "reason": "Rate does not match contract."})
    assert r.status_code == 200
    assert r.json()["status"] == "REJECTED"


def test_double_review_rejected(client, tmp_path):
    invoice_id = _analyzed_invoice(client, tmp_path)
    client.post(f"/api/invoices/{invoice_id}/review", json={"decision": "APPROVED"})
    r = client.post(f"/api/invoices/{invoice_id}/review",
                    json={"decision": "REJECTED", "reason": "changed mind"})
    assert r.status_code == 400
    assert "already" in r.json()["detail"].lower()


def test_review_before_analysis_rejected(client, tmp_path):
    inv = make_pdf(["INVOICE", "Acme"], str(tmp_path / "i.pdf"))
    con = make_pdf(["AGREEMENT", "Acme"], str(tmp_path / "c.pdf"))
    with open(inv, "rb") as a, open(con, "rb") as b:
        up = client.post("/api/invoices/upload",
                         files={"invoice": ("i.pdf", a, "application/pdf"),
                                "contract": ("c.pdf", b, "application/pdf")})
    invoice_id = up.json()["invoice_id"]
    r = client.post(f"/api/invoices/{invoice_id}/review", json={"decision": "APPROVED"})
    assert r.status_code == 400


def test_review_unknown_invoice_404(client):
    r = client.post("/api/invoices/00000000-0000-0000-0000-000000000000/review",
                    json={"decision": "APPROVED"})
    assert r.status_code == 404


def test_stats_counts_and_recent(client, tmp_path):
    # Two analyzed (critical) invoices; approve one.
    id1 = _analyzed_invoice(client, tmp_path, tag="1")
    _ = _analyzed_invoice(client, tmp_path, tag="2")
    client.post(f"/api/invoices/{id1}/review", json={"decision": "APPROVED"})

    stats = client.get("/api/stats").json()
    assert stats["total_processed"] == 2
    assert stats["pending_review"] == 1
    assert stats["approved"] == 1
    assert stats["high_risk"] == 2          # both are CRITICAL (score 90)
    assert stats["average_risk_score"] == 90.0
    assert stats["risk_distribution"]["CRITICAL"] == 2
    assert stats["risk_distribution"]["LOW"] == 0
    assert len(stats["recent"]) == 2


def test_stats_empty(client):
    stats = client.get("/api/stats").json()
    assert stats["total_processed"] == 0
    assert stats["average_risk_score"] is None
    assert stats["risk_distribution"] == {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    assert stats["recent"] == []
