"""Demo mode tests (PRD §40–§43).

Demo scenarios run through the SAME deterministic pipeline and response
structure as real analysis, and must produce the PRD-specified outcomes.
"""

def test_demo_clean(client):
    r = client.post("/api/demo/clean")
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["processing_status"] == "COMPLETED"
    assert body["risk_score"] == 0
    assert body["risk_level"] == "LOW"
    assert body["anomalies"] == []
    assert body["explanation_available"] is True
    assert body["explanation"]  # deterministic fallback text
    # all checks present; none failed
    for check in body["verification_checks"]:
        assert check["status"] != "FAILED"
    assert body["timesheet"] is not None
    assert float(body["timesheet"]["total_hours"]) == 80.0


def test_demo_critical(client):
    body = client.post("/api/demo/critical").json()
    assert body["risk_score"] == 90
    assert body["risk_level"] == "CRITICAL"
    types = {a["type"] for a in body["anomalies"]}
    assert types == {
        "RATE_MISMATCH",
        "EXCESSIVE_HOURS",
        "CONTRACT_AMOUNT_EXCEEDED",
        "TIMESHEET_MISMATCH",
    }
    # evidence present for every anomaly
    for a in body["anomalies"]:
        assert a["evidence"]
    ts = next(a for a in body["anomalies"] if a["type"] == "TIMESHEET_MISMATCH")
    assert ts["evidence"]["unsupported_hours"] == 25.0


def test_demo_timesheet_anomaly(client):
    body = client.post("/api/demo/timesheet").json()
    assert body["risk_score"] == 25
    assert body["risk_level"] == "MEDIUM"
    types = {a["type"] for a in body["anomalies"]}
    assert types == {"TIMESHEET_MISMATCH"}
    ts = body["anomalies"][0]
    assert ts["evidence"]["invoice_hours"] == 100
    assert ts["evidence"]["timesheet_hours"] == 82
    # invoice vs contract checks still pass
    checks = {c["key"]: c["status"] for c in body["verification_checks"]}
    assert checks["rate"] == "PASSED"
    assert checks["hours"] == "PASSED"


def test_demo_unknown_scenario(client):
    r = client.post("/api/demo/nope")
    assert r.status_code == 400


def test_demo_invoice_is_reviewable(client):
    """Demo invoices support the full human-review workflow."""
    body = client.post("/api/demo/critical").json()
    iid = body["id"]
    r = client.post(f"/api/invoices/{iid}/review",
                    json={"decision": "REJECTED", "reason": "Rate does not match contract."})
    assert r.status_code == 200
    assert r.json()["status"] == "REJECTED"

    stats = client.get("/api/stats").json()
    assert stats["total_processed"] == 1
    assert stats["rejected"] == 1
    assert stats["high_risk"] == 1


def test_demo_appears_in_list_and_queue(client):
    client.post("/api/demo/clean")
    client.post("/api/demo/critical")
    invoices = client.get("/api/invoices").json()
    assert len(invoices) == 2

    queue = client.get("/api/invoices?status=PENDING_REVIEW").json()
    # clean + critical both start pending review
    assert len(queue) == 2
