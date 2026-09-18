"""Anomaly engine (PRD §21).

Turns failed deterministic checks into anomaly records with structured
evidence sourced entirely from backend data. Each anomaly type contributes
its weight at most once per invoice (also enforced by a DB constraint).

The AI never generates anomalies or evidence.
"""

from app.models import Contract, Invoice, Timesheet
from app.models.enums import AnomalySeverity
from app.schemas.analysis import AnomalyResult, CheckResult, CheckStatus
from app.services.billing import derive_billing

# Weights per PRD §23
WEIGHTS = {
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

_CHECK_TO_ANOMALY = {
    "vendor": "VENDOR_MISMATCH",
    "rate": "RATE_MISMATCH",
    "hours": "EXCESSIVE_HOURS",
    "amount": "CONTRACT_AMOUNT_EXCEEDED",
    "timesheet": "TIMESHEET_MISMATCH",
    "arithmetic": "CALCULATION_MISMATCH",
    "contract_period": "OUTSIDE_CONTRACT_PERIOD",
    "currency": "CURRENCY_MISMATCH",
}

_TITLES = {
    "VENDOR_MISMATCH": "Invoice vendor does not match contract",
    "RATE_MISMATCH": "Hourly rate exceeds contract",
    "EXCESSIVE_HOURS": "Billed hours exceed contract limit",
    "CONTRACT_AMOUNT_EXCEEDED": "Invoice total exceeds contract maximum",
    "TIMESHEET_MISMATCH": "Billed hours not supported by timesheet",
    "CALCULATION_MISMATCH": "Invoice calculations are inconsistent",
    "OUTSIDE_CONTRACT_PERIOD": "Invoice date outside contract period",
    "CURRENCY_MISMATCH": "Invoice and contract currencies differ",
    "UNUSUAL_AMOUNT": "Invoice amount is unusually high",
}

HIGH_SEVERITY_ANOMALIES = {
    "VENDOR_MISMATCH",
    "CONTRACT_AMOUNT_EXCEEDED",
    "TIMESHEET_MISMATCH",
}


def build_anomalies(
    invoice: Invoice,
    contract: Contract,
    timesheet: Timesheet | None,
    checks: list[CheckResult],
) -> list[AnomalyResult]:
    billed_hours, billed_rate = derive_billing(invoice.line_items)
    anomalies: list[AnomalyResult] = []

    for check in checks:
        if check.status != CheckStatus.FAILED:
            continue
        anomaly_type = _CHECK_TO_ANOMALY.get(check.key)
        if anomaly_type is None:
            continue
        evidence = _evidence_for(
            anomaly_type, invoice, contract, timesheet, billed_hours, billed_rate
        )
        anomalies.append(
            AnomalyResult(
                type=anomaly_type,
                severity=(
                    AnomalySeverity.HIGH
                    if anomaly_type in HIGH_SEVERITY_ANOMALIES
                    else AnomalySeverity.MEDIUM
                ),
                title=_TITLES[anomaly_type],
                description=check.detail,
                points=WEIGHTS[anomaly_type],
                evidence=evidence,
            )
        )

    # Deterministic order: highest points first
    anomalies.sort(key=lambda a: a.points, reverse=True)
    return anomalies


def _num(value) -> float | None:
    return None if value is None else float(value)


def _evidence_for(anomaly_type, invoice, contract, timesheet,
                  billed_hours, billed_rate) -> dict:
    currency = invoice.currency or contract.currency or ""

    if anomaly_type == "VENDOR_MISMATCH":
        return {"invoice_vendor": invoice.vendor_name, "contract_vendor": contract.vendor_name}

    if anomaly_type == "RATE_MISMATCH":
        evidence = {
            "invoice_rate": _num(billed_rate),
            "contract_rate": _num(contract.hourly_rate),
        }
        if billed_rate and contract.hourly_rate:
            evidence["difference_percent"] = round(
                float((billed_rate - contract.hourly_rate) / contract.hourly_rate * 100), 1
            )
        evidence["currency"] = currency
        return evidence

    if anomaly_type == "EXCESSIVE_HOURS":
        return {
            "invoice_hours": _num(billed_hours),
            "contract_max_hours": _num(contract.max_hours),
            "excess_hours": _num(billed_hours - contract.max_hours)
            if billed_hours is not None and contract.max_hours is not None
            else None,
        }

    if anomaly_type == "CONTRACT_AMOUNT_EXCEEDED":
        return {
            "invoice_total": _num(invoice.total),
            "contract_max_amount": _num(contract.max_amount),
            "excess_amount": _num(invoice.total - contract.max_amount)
            if invoice.total is not None and contract.max_amount is not None
            else None,
            "currency": currency,
        }

    if anomaly_type == "TIMESHEET_MISMATCH":
        recorded = timesheet.total_hours if timesheet else None
        return {
            "invoice_hours": _num(billed_hours),
            "timesheet_hours": _num(recorded),
            "unsupported_hours": _num(billed_hours - recorded)
            if billed_hours is not None and recorded is not None
            else None,
        }

    if anomaly_type == "CALCULATION_MISMATCH":
        return {
            "subtotal": _num(invoice.subtotal),
            "tax": _num(invoice.tax),
            "total": _num(invoice.total),
            "line_items": invoice.line_items or [],
        }

    if anomaly_type == "OUTSIDE_CONTRACT_PERIOD":
        return {
            "invoice_date": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
            "contract_start": contract.start_date.isoformat() if contract.start_date else None,
            "contract_end": contract.end_date.isoformat() if contract.end_date else None,
        }

    if anomaly_type == "CURRENCY_MISMATCH":
        return {"invoice_currency": invoice.currency, "contract_currency": contract.currency}

    if anomaly_type == "UNUSUAL_AMOUNT":
        return {"invoice_total": _num(invoice.total), "currency": currency}

    return {}
