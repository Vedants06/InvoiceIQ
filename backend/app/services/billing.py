"""Helpers to derive billed hours / hourly rate from structured line items.

Deterministic: the AI only extracts numbers; the backend derives these.
"""

from decimal import Decimal


def derive_billing(line_items: list[dict] | None) -> tuple[Decimal | None, Decimal | None]:
    """Return (billed_hours, effective_hourly_rate) from line items.

    Hours   = sum of quantities on lines that carry a quantity
    Rate    = highest unit price among those lines (the billed hourly rate)

    Returns (None, None) when no line items carry quantities (e.g. a
    fixed-price invoice with no hourly breakdown).
    """
    if not line_items:
        return None, None

    hours = Decimal("0")
    rate: Decimal | None = None
    found_quantity = False

    for item in line_items:
        qty = item.get("quantity")
        if qty is None:
            continue
        found_quantity = True
        hours += Decimal(str(qty))
        unit_price = item.get("unit_price")
        if unit_price is not None:
            price = Decimal(str(unit_price))
            rate = price if rate is None else max(rate, price)

    if not found_quantity:
        return None, None
    return hours.quantize(Decimal("0.01")), rate.quantize(Decimal("0.01")) if rate is not None else None
