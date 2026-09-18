"""CSV export endpoint tests (P2, PRD §48)."""


def test_export_demo_critical_csv(client):
    body = client.post("/api/demo/critical").json()
    iid = body["id"]
    r = client.get(f"/api/invoices/{iid}/export")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    assert "attachment" in r.headers["content-disposition"]

    text = r.text
    # Deterministic analysis data is present.
    assert "RATE_MISMATCH" in text
    assert "CRITICAL" in text
    assert "90" in text
    assert "Verification checks" in text
    assert "Anomalies" in text
    # No fraud language.
    assert "fraud" not in text.lower()


def test_export_unknown_404(client):
    r = client.get("/api/invoices/00000000-0000-0000-0000-000000000000/export")
    assert r.status_code == 404
