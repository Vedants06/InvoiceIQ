"""AI explanation of verified findings (PRD §25, §36).

Only deterministic, backend-verified facts are sent to the LLM. The AI may
not invent anomalies, numbers, evidence, contract clauses, or fraud claims,
and it never states a risk score. If generation fails for any reason, the
analysis still succeeds — the explanation is simply marked unavailable.
"""

from app.ai.client import AIUnavailableError, ai_client
from app.models import Contract, Invoice, Timesheet
from app.schemas.analysis import AnomalyResult, CheckResult
from app.services.billing import derive_billing

SYSTEM_PROMPT = """You are a finance review assistant for an invoice
verification platform. You summarize findings that have ALREADY been
determined by the backend verification engine.

Rules:
- Use ONLY the facts supplied by the backend. Do not invent numbers,
  anomalies, contract clauses, or evidence.
- Do not use the word "fraud". Say "risk indicators", "inconsistencies",
  or "unsupported billing".
- Do not state or invent a numeric risk score.
- Be concise and professional (3-5 sentences). State whether manual review
  is required and end with that recommendation.
- If there are no failed checks, say the invoice appears consistent with
  the contract and timesheet and is recommended for approval."""


def _money(value) -> str:
    return "not stated" if value is None else f"{float(value):,.2f}"


def build_facts_prompt(
    invoice: Invoice,
    contract: Contract,
    timesheet: Timesheet | None,
    checks: list[CheckResult],
    anomalies: list[AnomalyResult],
) -> str:
    billed_hours, billed_rate = derive_billing(invoice.line_items)
    failed = [c for c in checks if c.status.value == "FAILED"]
    not_performed = [c for c in checks if c.status.value == "NOT_PERFORMED"]

    lines = [
        "Verified findings for invoice review:",
        f"- Invoice number: {invoice.invoice_number or 'unknown'}",
        f"- Invoice vendor: {invoice.vendor_name or 'unknown'}",
        f"- Contract vendor: {contract.vendor_name or 'unknown'}",
        f"- Invoice total: {_money(invoice.total)} {invoice.currency or ''}".rstrip(),
        f"- Contract maximum amount: {_money(contract.max_amount)} {contract.currency or ''}".rstrip(),
        f"- Billed rate: {_money(billed_rate)}/hr; Contract rate: {_money(contract.hourly_rate)}/hr",
        f"- Billed hours: {_money(billed_hours)}; Contract max hours: {_money(contract.max_hours)}",
        f"- Timesheet recorded hours: {_money(timesheet.total_hours) if timesheet else 'no timesheet provided'}",
        "",
        f"- Failed checks ({len(failed)}):",
    ]
    for c in failed:
        lines.append(f"  * {c.label}: {c.detail}")
    if not_performed:
        lines.append(f"- Checks not performed: {', '.join(c.label for c in not_performed)}")
    lines.append("")
    lines.append(
        "Write a short assessment for the human reviewer based ONLY on these findings."
    )
    return "\n".join(lines)


def generate_explanation(
    invoice: Invoice,
    contract: Contract,
    timesheet: Timesheet | None,
    checks: list[CheckResult],
    anomalies: list[AnomalyResult],
) -> tuple[str, bool]:
    """Return (explanation_text, available). Never raises."""
    if not ai_client.is_configured:
        return "", False

    prompt = build_facts_prompt(invoice, contract, timesheet, checks, anomalies)
    try:
        text = ai_client.generate_text(SYSTEM_PROMPT, prompt)
    except AIUnavailableError:
        return "", False
    return text, True
