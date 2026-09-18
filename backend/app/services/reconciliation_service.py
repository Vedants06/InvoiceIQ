"""Timesheet reconciliation (PRD §18) — deterministic, NO LLM.

Compares billed hours (invoice) against recorded hours (timesheet). With no
timesheet the check is NOT_PERFORMED — never a pass.
"""

from decimal import Decimal

from app.models import Invoice, Timesheet
from app.schemas.analysis import CheckResult, CheckStatus

# Small tolerance for rounding between systems
HOURS_TOL = Decimal("0.01")


def reconcile(invoice: Invoice, timesheet: Timesheet | None,
              billed_hours: Decimal | None) -> CheckResult:
    if timesheet is None:
        return CheckResult(
            key="timesheet",
            label="Timesheet",
            status=CheckStatus.NOT_PERFORMED,
            detail="No timesheet was provided. Timesheet reconciliation could not be performed.",
        )

    recorded = timesheet.total_hours
    if billed_hours is None:
        return CheckResult(
            key="timesheet",
            label="Timesheet",
            status=CheckStatus.NOT_PERFORMED,
            detail="Invoice has no hourly quantities to reconcile against the timesheet.",
        )

    unsupported = billed_hours - recorded
    if unsupported > HOURS_TOL:
        return CheckResult(
            key="timesheet",
            label="Timesheet",
            status=CheckStatus.FAILED,
            detail=(
                f"{unsupported.quantize(Decimal('0.01')):g} billed hours are not "
                f"supported by the submitted timesheet "
                f"({billed_hours:g} billed vs {recorded:g} recorded)."
            ),
        )

    return CheckResult(
        key="timesheet",
        label="Timesheet",
        status=CheckStatus.PASSED,
        detail=f"All {billed_hours:g} billed hours are supported by {recorded:g} recorded hours.",
    )
