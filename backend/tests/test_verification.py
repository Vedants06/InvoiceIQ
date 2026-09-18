"""Verification engine tests (PRD §17)."""

from datetime import date
from decimal import Decimal

from app.models import Contract, Invoice
from app.schemas.analysis import CheckStatus
from app.services import validation_service


def _invoice(**kw) -> Invoice:
    defaults = dict(
        vendor_name="Acme Technologies",
        currency="USD",
        invoice_date=date(2026, 8, 20),
        subtotal=Decimal("9000.00"),
        tax=Decimal("0"),
        total=Decimal("9000.00"),
        line_items=[{"description": "Software Development", "quantity": 120,
                     "unit_price": 75, "amount": 9000}],
    )
    defaults.update(kw)
    return Invoice(**defaults)


def _contract(**kw) -> Contract:
    defaults = dict(
        vendor_name="Acme Technologies",
        currency="USD",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        hourly_rate=Decimal("50.00"),
        max_hours=Decimal("100"),
        max_amount=Decimal("5000.00"),
    )
    defaults.update(kw)
    return Contract(**defaults)


def _by_key(checks, key):
    return next(c for c in checks if c.key == key)


def test_clean_invoice_passes_all():
    invoice = _invoice(
        subtotal=Decimal("4000"), tax=Decimal("0"), total=Decimal("4000"),
        line_items=[{"description": "Dev", "quantity": 80, "unit_price": 50, "amount": 4000}],
    )
    contract = _contract(max_hours=Decimal("80"), max_amount=Decimal("4000"))
    checks = validation_service.run_checks(invoice, contract)

    expected_passes = {"vendor", "contract_period", "currency", "rate",
                       "hours", "amount", "arithmetic"}
    for key in expected_passes:
        assert _by_key(checks, key).status == CheckStatus.PASSED, key


def test_critical_invoice_fails_rate_hours_amount():
    invoice = _invoice()
    contract = _contract()
    checks = validation_service.run_checks(invoice, contract)

    assert _by_key(checks, "vendor").status == CheckStatus.PASSED
    assert _by_key(checks, "contract_period").status == CheckStatus.PASSED
    assert _by_key(checks, "rate").status == CheckStatus.FAILED
    assert _by_key(checks, "hours").status == CheckStatus.FAILED
    assert _by_key(checks, "amount").status == CheckStatus.FAILED
    assert _by_key(checks, "arithmetic").status == CheckStatus.PASSED


def test_vendor_mismatch():
    checks = validation_service.run_checks(
        _invoice(vendor_name="Acme Technologies"),
        _contract(vendor_name="Globex Corp"),
    )
    check = _by_key(checks, "vendor")
    assert check.status == CheckStatus.FAILED
    assert "does not match" in check.detail


def test_outside_contract_period():
    checks = validation_service.run_checks(
        _invoice(invoice_date=date(2027, 1, 15)),
        _contract(start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)),
    )
    assert _by_key(checks, "contract_period").status == CheckStatus.FAILED


def test_currency_mismatch_marks_money_checks_not_performed():
    invoice = _invoice(currency="EUR")
    contract = _contract(currency="USD")
    checks = validation_service.run_checks(invoice, contract)

    assert _by_key(checks, "currency").status == CheckStatus.FAILED
    # No currency conversion: monetary comparisons are unavailable, not failed
    assert _by_key(checks, "rate").status == CheckStatus.NOT_PERFORMED
    assert _by_key(checks, "amount").status == CheckStatus.NOT_PERFORMED


def test_calculation_mismatch_line_item():
    invoice = _invoice(
        line_items=[{"description": "Dev", "quantity": 120, "unit_price": 75,
                     "amount": 5000}],  # 120*75 = 9000
        subtotal=Decimal("5000"), tax=Decimal("0"), total=Decimal("5000"),
    )
    checks = validation_service.run_checks(invoice, _contract())
    assert _by_key(checks, "arithmetic").status == CheckStatus.FAILED


def test_calculation_mismatch_total():
    invoice = _invoice(
        line_items=[{"description": "Dev", "quantity": 10, "unit_price": 100,
                     "amount": 1000}],
        subtotal=Decimal("1000"), tax=Decimal("200"), total=Decimal("1000"),
    )  # subtotal + tax = 1200 != 1000
    checks = validation_service.run_checks(invoice, _contract(max_amount=Decimal("9999")))
    assert _by_key(checks, "arithmetic").status == CheckStatus.FAILED


def test_calculation_not_verifiable_when_no_structure():
    invoice = _invoice(line_items=[], subtotal=None, total=Decimal("500"))
    checks = validation_service.run_checks(invoice, _contract())
    assert _by_key(checks, "arithmetic").status == CheckStatus.NOT_PERFORMED


def test_tax_allowed_in_arithmetic():
    # subtotal + tax == total should pass (no false positive)
    invoice = _invoice(
        line_items=[{"description": "Dev", "quantity": 8, "unit_price": 100,
                     "amount": 800}],
        subtotal=Decimal("800"), tax=Decimal("80"), total=Decimal("880"),
    )
    checks = validation_service.run_checks(invoice, _contract(max_amount=Decimal("9999")))
    assert _by_key(checks, "arithmetic").status == CheckStatus.PASSED


def test_missing_dates_not_performed():
    invoice = _invoice(invoice_date=None)
    contract = _contract(start_date=None, end_date=None)
    checks = validation_service.run_checks(invoice, contract)
    assert _by_key(checks, "contract_period").status == CheckStatus.NOT_PERFORMED


def test_billing_within_limits_passes():
    invoice = _invoice(
        line_items=[{"description": "Dev", "quantity": 60, "unit_price": 45,
                     "amount": 2700}],
        subtotal=Decimal("2700"), tax=Decimal("0"), total=Decimal("2700"),
    )
    # rate 45 <= 50, hours 60 <= 100, amount 2700 <= 5000
    checks = validation_service.run_checks(invoice, _contract())
    assert _by_key(checks, "rate").status == CheckStatus.PASSED
    assert _by_key(checks, "hours").status == CheckStatus.PASSED
    assert _by_key(checks, "amount").status == CheckStatus.PASSED
