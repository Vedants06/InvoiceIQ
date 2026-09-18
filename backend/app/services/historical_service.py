"""Historical vendor analysis (P1 — PRD §19).

Compares the current invoice against the vendor's previously COMPLETED
invoices to detect an unusual amount. Deterministic, like all verification.
Currency is never converted — only same-currency history is considered.

Returns structured stats for display and, when the amount deviates sharply
above the vendor's historical average, an UNUSUAL_AMOUNT anomaly.
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import Contract, Invoice
from app.models.enums import AnomalySeverity, ProcessingStatus
from app.schemas.analysis import AnomalyResult
from app.services.billing import derive_billing

# Flag when the current total is at least 50% above the historical average.
UNUSUAL_DEVIATION_THRESHOLD = 50.0


@dataclass
class HistoricalStats:
    count: int
    average_amount: float
    max_amount: float
    min_amount: float
    current_amount: float
    deviation_percent: float
    average_hours: float | None

    def as_dict(self) -> dict:
        return {
            "prior_invoice_count": self.count,
            "average_amount": round(self.average_amount, 2),
            "max_amount": round(self.max_amount, 2),
            "min_amount": round(self.min_amount, 2),
            "current_amount": round(self.current_amount, 2),
            "deviation_percent": round(self.deviation_percent, 1),
            "average_hours": round(self.average_hours, 2)
            if self.average_hours is not None
            else None,
        }


def analyze_history(
    db: Session, invoice: Invoice, contract: Contract
) -> tuple[HistoricalStats | None, AnomalyResult | None]:
    """Return (stats, anomaly) for the vendor's history; (None, None) if no
    comparable history exists."""
    if not invoice.total or not invoice.vendor_name or not invoice.currency:
        return None, None

    prior = (
        db.query(Invoice)
        .filter(
            Invoice.id != invoice.id,
            Invoice.vendor_name.ilike(invoice.vendor_name),
            Invoice.processing_status == ProcessingStatus.COMPLETED,
            Invoice.currency == invoice.currency,
            Invoice.total.isnot(None),
        )
        .all()
    )
    if not prior:
        return None, None

    amounts = [float(i.total) for i in prior]
    average_amount = sum(amounts) / len(amounts)
    current_amount = float(invoice.total)
    deviation = (
        (current_amount - average_amount) / average_amount * 100
        if average_amount
        else 0.0
    )

    hours = [h for h in (derive_billing(i.line_items)[0] for i in prior) if h is not None]
    average_hours = float(sum(hours) / len(hours)) if hours else None

    stats = HistoricalStats(
        count=len(prior),
        average_amount=average_amount,
        max_amount=max(amounts),
        min_amount=min(amounts),
        current_amount=current_amount,
        deviation_percent=deviation,
        average_hours=average_hours,
    )

    anomaly = None
    if deviation >= UNUSUAL_DEVIATION_THRESHOLD:
        anomaly = AnomalyResult(
            type="UNUSUAL_AMOUNT",
            severity=AnomalySeverity.MEDIUM,
            title="Invoice amount unusually high for this vendor",
            description=(
                f"Total of {current_amount:,.2f} is {deviation:+.0f}% versus the "
                f"vendor's historical average of {average_amount:,.2f} across "
                f"{len(prior)} prior invoice(s)."
            ),
            points=15,
            evidence={
                "current_amount": round(current_amount, 2),
                "average_amount": round(average_amount, 2),
                "deviation_percent": round(deviation, 1),
                "prior_invoice_count": len(prior),
                "currency": invoice.currency,
            },
        )

    return stats, anomaly
