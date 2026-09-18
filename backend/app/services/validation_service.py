"""Deterministic verification engine (PRD §17).

Every comparison is performed by backend code — never by the LLM. Each check
returns a CheckResult for the Verification Summary. Checks that cannot be
evaluated because evidence is missing are NOT_PERFORMED (never a pass).
"""

from decimal import Decimal

from app.models import Contract, Invoice
from app.schemas.analysis import CheckResult, CheckStatus
from app.services.billing import derive_billing

# Relative tolerance for money/rate comparisons (rounding on printed figures)
MONEY_TOL = Decimal("0.01")
CALC_TOL = Decimal("0.02")  # line-item qty*price vs amount
TOTAL_TOL = Decimal("0.05")  # subtotal+tax vs total


def _status(condition: bool) -> CheckStatus:
    return CheckStatus.PASSED if condition else CheckStatus.FAILED


def _within(actual: Decimal, expected: Decimal, tol: Decimal) -> bool:
    if expected == 0:
        return abs(actual) <= tol
    return abs(actual - expected) <= abs(expected) * tol


def run_checks(invoice: Invoice, contract: Contract) -> list[CheckResult]:
    """Run all invoice-vs-contract deterministic checks (PRD §17.1–§17.7)."""
    inv_currency = invoice.currency
    con_currency = contract.currency
    billed_hours, billed_rate = derive_billing(invoice.line_items)

    checks: list[CheckResult] = []

    # 17.1 Vendor -----------------------------------------------------------
    checks.append(_check_vendor(invoice.vendor_name, contract.vendor_name))

    # 17.2 Contract period --------------------------------------------------
    checks.append(
        _check_contract_period(invoice.invoice_date, contract.start_date, contract.end_date)
    )

    # 17.3 Currency ---------------------------------------------------------
    currency_check = _check_currency(inv_currency, con_currency)
    checks.append(currency_check)
    currencies_match = currency_check.status == CheckStatus.PASSED

    # 17.4 Rate (only comparable when currencies match) ---------------------
    checks.append(
        _check_rate(billed_rate, contract.hourly_rate, currencies_match)
    )

    # 17.5 Hours ------------------------------------------------------------
    checks.append(_check_hours(billed_hours, contract.max_hours))

    # 17.6 Amount (only comparable when currencies match) -------------------
    checks.append(
        _check_amount(invoice.total, contract.max_amount, currencies_match)
    )

    # 17.7 Arithmetic -------------------------------------------------------
    checks.append(_check_arithmetic(invoice))

    return checks


def _check_vendor(invoice_vendor: str | None, contract_vendor: str | None) -> CheckResult:
    if not invoice_vendor or not contract_vendor:
        return CheckResult(
            key="vendor", label="Vendor", status=CheckStatus.NOT_PERFORMED,
            detail="Vendor could not be determined on invoice or contract.",
        )
    matched = invoice_vendor.strip().lower() == contract_vendor.strip().lower()
    return CheckResult(
        key="vendor",
        label="Vendor",
        status=_status(matched),
        detail=(
            "Matched"
            if matched
            else f"Invoice vendor '{invoice_vendor}' does not match contract vendor '{contract_vendor}'."
        ),
    )


def _check_contract_period(invoice_date, start, end) -> CheckResult:
    if invoice_date is None or start is None or end is None:
        return CheckResult(
            key="contract_period", label="Contract Period",
            status=CheckStatus.NOT_PERFORMED,
            detail="Contract period or invoice date could not be determined.",
        )
    in_period = start <= invoice_date <= end
    return CheckResult(
        key="contract_period",
        label="Contract Period",
        status=_status(in_period),
        detail=(
            f"Invoice date {invoice_date.isoformat()} is within "
            f"{start.isoformat()} – {end.isoformat()}."
            if in_period
            else f"Invoice date {invoice_date.isoformat()} is outside the contract "
                 f"period {start.isoformat()} – {end.isoformat()}."
        ),
    )


def _check_currency(inv: str | None, con: str | None) -> CheckResult:
    if not inv or not con:
        return CheckResult(
            key="currency", label="Currency", status=CheckStatus.NOT_PERFORMED,
            detail="Currency could not be determined on invoice or contract.",
        )
    matched = inv.upper() == con.upper()
    return CheckResult(
        key="currency",
        label="Currency",
        status=_status(matched),
        detail=(
            f"Both documents use {inv.upper()}."
            if matched
            else f"Invoice currency {inv.upper()} does not match contract currency {con.upper()}."
        ),
    )


def _monetary_unavailable(currencies_match: bool) -> bool:
    return not currencies_match


def _check_rate(billed_rate, contract_rate, currencies_match: bool) -> CheckResult:
    if _monetary_unavailable(currencies_match):
        return CheckResult(
            key="rate", label="Hourly Rate", status=CheckStatus.NOT_PERFORMED,
            detail="Currencies differ; monetary rate comparison unavailable (no conversion performed).",
        )
    if billed_rate is None or contract_rate is None:
        return CheckResult(
            key="rate", label="Hourly Rate", status=CheckStatus.NOT_PERFORMED,
            detail="Billed or contracted rate could not be determined.",
        )
    over = billed_rate > contract_rate and not _within(billed_rate, contract_rate, MONEY_TOL)
    if over:
        pct = ((billed_rate - contract_rate) / contract_rate * 100).quantize(Decimal("0.1"))
        detail = (
            f"Invoice charges {billed_rate}/hr while the contract specifies "
            f"{contract_rate}/hr (+{pct}%)."
        )
    else:
        detail = f"Billed rate {billed_rate}/hr is within the contracted {contract_rate}/hr."
    return CheckResult(key="rate", label="Hourly Rate", status=_status(not over), detail=detail)


def _check_hours(billed_hours, max_hours) -> CheckResult:
    if billed_hours is None:
        return CheckResult(
            key="hours", label="Billed Hours", status=CheckStatus.NOT_PERFORMED,
            detail="No hourly quantities found on the invoice.",
        )
    if max_hours is None:
        return CheckResult(
            key="hours", label="Billed Hours", status=CheckStatus.NOT_PERFORMED,
            detail="Contract maximum hours could not be determined.",
        )
    exceeded = billed_hours > max_hours
    return CheckResult(
        key="hours",
        label="Billed Hours",
        status=_status(not exceeded),
        detail=(
            f"{billed_hours:g} billed hours exceed the contractual maximum of {max_hours:g}."
            if exceeded
            else f"{billed_hours:g} billed hours are within the {max_hours:g} hour limit."
        ),
    )


def _check_amount(invoice_total, max_amount, currencies_match: bool) -> CheckResult:
    if _monetary_unavailable(currencies_match):
        return CheckResult(
            key="amount", label="Contract Amount", status=CheckStatus.NOT_PERFORMED,
            detail="Currencies differ; contract amount comparison unavailable (no conversion performed).",
        )
    if invoice_total is None or max_amount is None:
        return CheckResult(
            key="amount", label="Contract Amount", status=CheckStatus.NOT_PERFORMED,
            detail="Invoice total or contract maximum amount could not be determined.",
        )
    exceeded = invoice_total > max_amount and not _within(invoice_total, max_amount, MONEY_TOL)
    return CheckResult(
        key="amount",
        label="Contract Amount",
        status=_status(not exceeded),
        detail=(
            f"Invoice total {invoice_total} exceeds the contractual maximum of {max_amount}."
            if exceeded
            else f"Invoice total {invoice_total} is within the maximum {max_amount}."
        ),
    )


def _check_arithmetic(invoice: Invoice) -> CheckResult:
    line_items = invoice.line_items or []
    errors: list[str] = []
    verified_any = False

    # Line-level: quantity * unit_price == amount
    for idx, item in enumerate(line_items, start=1):
        qty = item.get("quantity")
        price = item.get("unit_price")
        amount = item.get("amount")
        if qty is not None and price is not None and amount is not None:
            verified_any = True
            expected = Decimal(str(qty)) * Decimal(str(price))
            if not _within(Decimal(str(amount)), expected, CALC_TOL):
                desc = item.get("description") or f"line {idx}"
                errors.append(
                    f"{desc}: {qty:g} x {price} = {expected.quantize(Decimal('0.01'))}, "
                    f"but line amount is {amount}."
                )

    # Total: subtotal + tax == total
    if invoice.subtotal is not None and invoice.total is not None:
        verified_any = True
        tax = invoice.tax if invoice.tax is not None else Decimal("0")
        expected_total = invoice.subtotal + tax
        if not _within(invoice.total, expected_total, TOTAL_TOL):
            errors.append(
                f"Subtotal {invoice.subtotal} + tax {tax} = "
                f"{expected_total.quantize(Decimal('0.01'))}, but total is {invoice.total}."
            )

    if errors:
        return CheckResult(
            key="arithmetic", label="Arithmetic", status=CheckStatus.FAILED,
            detail=" ".join(errors),
        )
    if not verified_any:
        return CheckResult(
            key="arithmetic", label="Arithmetic", status=CheckStatus.NOT_PERFORMED,
            detail="Calculations could not be reliably verified from the extracted structure.",
        )
    return CheckResult(
        key="arithmetic", label="Arithmetic", status=CheckStatus.PASSED,
        detail="Line items and totals are arithmetically consistent.",
    )
