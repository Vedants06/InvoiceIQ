"""Anomaly + risk scoring tests (PRD §21–§24), incl. the three demo scenarios."""

from datetime import date
from decimal import Decimal

from app.models import Contract, Invoice, Timesheet
from app.models.enums import AnomalySeverity, RiskLevel
from app.schemas.analysis import AnomalyResult, CheckResult, CheckStatus
from app.services import anomaly_service, risk_service, validation_service
from app.services.billing import derive_billing
from app.services import reconciliation_service


# --- risk_service unit tests ---------------------------------------------

def _anomaly(type_, points):
    return AnomalyResult(
        type=type_, severity=AnomalySeverity.HIGH, title=type_,
        description=type_, points=points, evidence={},
    )


def test_risk_classification_bands():
    assert risk_service.classify(0) == RiskLevel.LOW
    assert risk_service.classify(24) == RiskLevel.LOW
    assert risk_service.classify(25) == RiskLevel.MEDIUM   # PRD §42: 25 = MEDIUM
    assert risk_service.classify(59) == RiskLevel.MEDIUM
    assert risk_service.classify(60) == RiskLevel.HIGH
    assert risk_service.classify(79) == RiskLevel.HIGH
    assert risk_service.classify(80) == RiskLevel.CRITICAL
    assert risk_service.classify(100) == RiskLevel.CRITICAL


def test_score_caps_at_100():
    anomalies = [_anomaly("VENDOR_MISMATCH", 30), _anomaly("RATE_MISMATCH", 20),
                 _anomaly("EXCESSIVE_HOURS", 20), _anomaly("CONTRACT_AMOUNT_EXCEEDED", 25),
                 _anomaly("TIMESHEET_MISMATCH", 25)]  # sums to 120
    score, level = risk_service.score_anomalies(anomalies)
    assert score == 100
    assert level == RiskLevel.CRITICAL


def test_weights_match_prd():
    assert anomaly_service.WEIGHTS == {
        "VENDOR_MISMATCH": 30,
        "RATE_MISMATCH": 20,
        "EXCESSIVE_HOURS": 20,
        "CONTRACT_AMOUNT_EXCEEDED": 25,
        "TIMESHEET_MISMATCH": 25,
        "CALCULATION_MISMATCH": 15,
        "OUTSIDE_CONTRACT_PERIOD": 20,
        "CURRENCY_MISMATCH": 20,
        "UNUSUAL_AMOUNT": 15,
    }


# --- end-to-end scenario tests -------------------------------------------

def _run(invoice, contract, timesheet):
    checks = validation_service.run_checks(invoice, contract)
    hours, _ = derive_billing(invoice.line_items)
    checks.append(reconciliation_service.reconcile(invoice, timesheet, hours))
    anomalies = anomaly_service.build_anomalies(invoice, contract, timesheet, checks)
    score, level = risk_service.score_anomalies(anomalies)
    return checks, anomalies, score, level


def _clean_invoice():
    invoice = Invoice(
        vendor_name="Acme", currency="USD", invoice_date=date(2026, 6, 1),
        subtotal=Decimal("4000"), tax=Decimal("0"), total=Decimal("4000"),
        line_items=[{"description": "Dev", "quantity": 80, "unit_price": 50,
                     "amount": 4000}],
    )
    contract = Contract(
        vendor_name="Acme", currency="USD",
        start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
        hourly_rate=Decimal("50"), max_hours=Decimal("80"),
        max_amount=Decimal("4000"),
    )
    timesheet = Timesheet(total_hours=Decimal("80"), file_name="ts.csv")
    return invoice, contract, timesheet


def test_scenario_1_clean_invoice():
    checks, anomalies, score, level = _run(*_clean_invoice())
    failed = [c for c in checks if c.status == CheckStatus.FAILED]
    assert failed == []
    assert anomalies == []
    assert score == 0
    assert level == RiskLevel.LOW


def test_scenario_2_critical_invoice():
    invoice = Invoice(
        vendor_name="Acme", currency="USD", invoice_date=date(2026, 8, 20),
        subtotal=Decimal("9000"), tax=Decimal("0"), total=Decimal("9000"),
        line_items=[{"description": "Dev", "quantity": 120, "unit_price": 75,
                     "amount": 9000}],
    )
    contract = Contract(
        vendor_name="Acme", currency="USD",
        start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
        hourly_rate=Decimal("50"), max_hours=Decimal("100"),
        max_amount=Decimal("5000"),
    )
    timesheet = Timesheet(total_hours=Decimal("95"), file_name="ts.csv")

    checks, anomalies, score, level = _run(invoice, contract, timesheet)

    types = {a.type for a in anomalies}
    assert types == {
        "RATE_MISMATCH",
        "EXCESSIVE_HOURS",
        "CONTRACT_AMOUNT_EXCEEDED",
        "TIMESHEET_MISMATCH",
    }
    assert score == 90          # 20 + 20 + 25 + 25
    assert level == RiskLevel.CRITICAL


def test_scenario_3_hidden_timesheet_anomaly():
    invoice = Invoice(
        vendor_name="Acme", currency="USD", invoice_date=date(2026, 8, 20),
        subtotal=Decimal("6000"), tax=Decimal("0"), total=Decimal("6000"),
        line_items=[{"description": "Dev", "quantity": 100, "unit_price": 60,
                     "amount": 6000}],
    )
    contract = Contract(
        vendor_name="Acme", currency="USD",
        start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
        hourly_rate=Decimal("60"), max_hours=Decimal("100"),
        max_amount=None,
    )
    timesheet = Timesheet(total_hours=Decimal("82"), file_name="ts.csv")

    checks, anomalies, score, level = _run(invoice, contract, timesheet)

    types = {a.type for a in anomalies}
    assert types == {"TIMESHEET_MISMATCH"}
    assert score == 25
    assert level == RiskLevel.MEDIUM
    # evidence carries the three-source comparison
    ts_anomaly = next(a for a in anomalies if a.type == "TIMESHEET_MISMATCH")
    assert ts_anomaly.evidence["invoice_hours"] == 100
    assert ts_anomaly.evidence["timesheet_hours"] == 82
    assert ts_anomaly.evidence["unsupported_hours"] == 18


def test_every_anomaly_has_evidence():
    invoice = Invoice(
        vendor_name="Globex", currency="EUR", invoice_date=date(2027, 1, 1),
        subtotal=Decimal("9000"), tax=Decimal("0"), total=Decimal("9000"),
        line_items=[{"description": "Dev", "quantity": 120, "unit_price": 75,
                     "amount": 1}],  # bad arithmetic too
    )
    contract = Contract(
        vendor_name="Acme", currency="USD",
        start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
        hourly_rate=Decimal("50"), max_hours=Decimal("100"),
        max_amount=Decimal("5000"),
    )
    timesheet = Timesheet(total_hours=Decimal("10"), file_name="ts.csv")

    _, anomalies, _, _ = _run(invoice, contract, timesheet)
    for a in anomalies:
        assert isinstance(a.evidence, dict)
        assert a.evidence, f"{a.type} must carry evidence"
        assert a.points == anomaly_service.WEIGHTS[a.type]


def test_no_anomaly_type_duplicated():
    # The engine yields each anomaly type at most once per invoice
    invoice = Invoice(
        vendor_name="Acme", currency="USD", invoice_date=date(2026, 6, 1),
        subtotal=Decimal("9000"), tax=Decimal("0"), total=Decimal("9000"),
        line_items=[{"description": "Dev", "quantity": 120, "unit_price": 75,
                     "amount": 9000}],
    )
    contract = Contract(
        vendor_name="Acme", currency="USD",
        start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
        hourly_rate=Decimal("50"), max_hours=Decimal("100"),
        max_amount=Decimal("5000"),
    )
    _, anomalies, _, _ = _run(invoice, contract, None)
    types = [a.type for a in anomalies]
    assert len(types) == len(set(types))
