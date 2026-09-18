"""Timesheet reconciliation tests (PRD §18)."""

from decimal import Decimal

from app.models import Invoice, Timesheet
from app.schemas.analysis import CheckStatus
from app.services import reconciliation_service


def _invoice_with_hours(hours: float) -> Invoice:
    return Invoice(
        vendor_name="Acme",
        line_items=[{"description": "Dev", "quantity": hours,
                     "unit_price": 50, "amount": hours * 50}],
    )


def _timesheet(hours: float) -> Timesheet:
    return Timesheet(total_hours=Decimal(str(hours)), file_name="ts.csv")


def test_missing_timesheet_is_not_performed():
    check = reconciliation_service.reconcile(
        _invoice_with_hours(100), None, Decimal("100")
    )
    assert check.status == CheckStatus.NOT_PERFORMED
    assert "could not be performed" in check.detail.lower()


def test_hours_supported_passes():
    check = reconciliation_service.reconcile(
        _invoice_with_hours(80), _timesheet(80), Decimal("80")
    )
    assert check.status == CheckStatus.PASSED


def test_unsupported_hours_fails():
    check = reconciliation_service.reconcile(
        _invoice_with_hours(100), _timesheet(82), Decimal("100")
    )
    assert check.status == CheckStatus.FAILED
    assert "18" in check.detail  # 100 - 82 unsupported hours
    assert "not supported" in check.detail


def test_critical_scenario_timesheet_mismatch():
    # 120 billed vs 95 recorded -> 25 unsupported
    check = reconciliation_service.reconcile(
        _invoice_with_hours(120), _timesheet(95), Decimal("120")
    )
    assert check.status == CheckStatus.FAILED
    assert "25" in check.detail


def test_timesheet_more_hours_than_billed_passes():
    check = reconciliation_service.reconcile(
        _invoice_with_hours(40), _timesheet(50), Decimal("40")
    )
    assert check.status == CheckStatus.PASSED


def test_no_billed_hours_not_performed():
    invoice = Invoice(vendor_name="Acme", line_items=[])
    check = reconciliation_service.reconcile(invoice, _timesheet(40), None)
    assert check.status == CheckStatus.NOT_PERFORMED
