"""Historical vendor analysis tests (PRD §19)."""

from datetime import date
from decimal import Decimal

from app.models import Contract, Invoice
from app.models.enums import ProcessingStatus
from app.services import historical_service


def _invoice(total: float, vendor: str = "Acme", currency: str = "USD",
             hours: float | None = 40, processed: bool = True) -> Invoice:
    inv = Invoice(
        vendor_name=vendor,
        currency=currency,
        total=Decimal(str(total)),
        subtotal=Decimal(str(total)),
        tax=Decimal("0"),
        invoice_date=date(2026, 8, 20),
        line_items=[{"description": "Dev", "quantity": hours, "unit_price": 50,
                     "amount": total}]
        if hours is not None
        else [],
        processing_status=ProcessingStatus.COMPLETED if processed else ProcessingStatus.UPLOADED,
    )
    return inv


def _contract() -> Contract:
    return Contract(
        vendor_name="Acme", currency="USD",
        start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
        hourly_rate=Decimal("50"), max_hours=Decimal("1000"),
        max_amount=Decimal("100000"),
    )


def test_no_history_returns_none(db_session):
    current = _invoice(5200)
    db_session.add(current)
    db_session.commit()
    stats, anomaly = historical_service.analyze_history(db_session, current, _contract())
    assert stats is None
    assert anomaly is None


def test_stable_invoice_no_anomaly(db_session):
    # Two prior invoices averaging ~5200; current similar.
    for total in (5000, 5400):
        db_session.add(_invoice(total))
    current = _invoice(5200)
    db_session.add(current)
    db_session.commit()
    stats, anomaly = historical_service.analyze_history(db_session, current, _contract())
    assert stats is not None
    assert stats.count == 2
    assert stats.average_amount == 5200.0
    assert anomaly is None


def test_unusual_amount_triggers(db_session):
    # History around 5200 average; a 12,400 invoice deviates ~+138% (PRD §19).
    for total in (5000, 5400):
        db_session.add(_invoice(total))
    current = _invoice(12400)
    db_session.add(current)
    db_session.commit()
    stats, anomaly = historical_service.analyze_history(db_session, current, _contract())
    assert anomaly is not None
    assert anomaly.type == "UNUSUAL_AMOUNT"
    assert anomaly.points == 15
    assert anomaly.evidence["deviation_percent"] > 50
    assert anomaly.evidence["prior_invoice_count"] == 2
    assert stats.deviation_percent > 100


def test_below_average_no_anomaly(db_session):
    db_session.add(_invoice(5000))
    db_session.add(_invoice(5400))
    current = _invoice(3000)  # cheaper than average
    db_session.add(current)
    db_session.commit()
    _, anomaly = historical_service.analyze_history(db_session, current, _contract())
    assert anomaly is None


def test_currency_isolation(db_session):
    # EUR history must not be compared to a USD invoice (no conversion).
    db_session.add(_invoice(5000, currency="EUR"))
    current = _invoice(900000, currency="USD")  # huge in USD
    db_session.add(current)
    db_session.commit()
    stats, _ = historical_service.analyze_history(db_session, current, _contract())
    assert stats is None


def test_only_completed_invoices_count(db_session):
    db_session.add(_invoice(5000, processed=False))  # uploaded, not analyzed
    current = _invoice(12000)
    db_session.add(current)
    db_session.commit()
    stats, anomaly = historical_service.analyze_history(db_session, current, _contract())
    assert stats is None
    assert anomaly is None
