"""Pydantic models that validate AI structured outputs (PRD §14, §15, §36).

Raw LLM output is NEVER trusted: every response is parsed against these
models before it enters the pipeline. The models also double as the OpenAI
Structured Outputs response_format schema.
"""

import re
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

_CURRENCY_CODE_RE = re.compile(r"^[A-Z]{3}$")


def parse_date_lenient(value: str | None) -> date | None:
    """Accept ISO (2026-08-20) or US-style (08/20/2026, 8/20/26) dates."""
    if not value:
        return None
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%d-%m-%Y"):
        try:
            from datetime import datetime

            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


class LineItemExtraction(BaseModel):
    description: str | None = None
    quantity: float | None = None
    unit_price: float | None = None
    amount: float | None = None

    @field_validator("description", mode="before")
    @classmethod
    def _blank_to_none(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v


class InvoiceExtraction(BaseModel):
    """Validated shape of an extracted invoice (PRD §14)."""

    invoice_number: str | None = None
    vendor_name: str | None = None
    invoice_date: date | None = None
    due_date: date | None = None
    currency: str | None = None
    subtotal: float | None = None
    tax: float | None = None
    total: float | None = None
    line_items: list[LineItemExtraction] = Field(default_factory=list)

    @field_validator("invoice_date", "due_date", mode="before")
    @classmethod
    def _parse_dates(cls, v):
        return parse_date_lenient(v) if isinstance(v, str) else v

    @field_validator("currency", mode="before")
    @classmethod
    def _normalize_currency(cls, v):
        if isinstance(v, str):
            code = v.strip().upper()
            return code if _CURRENCY_CODE_RE.match(code) else None
        return None

    @field_validator("vendor_name", "invoice_number", mode="before")
    @classmethod
    def _strip_text(cls, v):
        if isinstance(v, str):
            v = v.strip()
            return v or None
        return v


class ContractExtraction(BaseModel):
    """Validated shape of an extracted contract (PRD §15).

    Only the fields needed for verification are extracted.
    """

    vendor_name: str | None = None
    contract_start: date | None = None
    contract_end: date | None = None
    hourly_rate: float | None = None
    max_hours: float | None = None
    max_amount: float | None = None
    currency: str | None = None
    payment_terms: str | None = None

    @field_validator("contract_start", "contract_end", mode="before")
    @classmethod
    def _parse_dates(cls, v):
        return parse_date_lenient(v) if isinstance(v, str) else v

    @field_validator("currency", mode="before")
    @classmethod
    def _normalize_currency(cls, v):
        if isinstance(v, str):
            code = v.strip().upper()
            return code if _CURRENCY_CODE_RE.match(code) else None
        return None

    @field_validator("vendor_name", "payment_terms", mode="before")
    @classmethod
    def _strip_text(cls, v):
        if isinstance(v, str):
            v = v.strip()
            return v or None
        return v


def dec(value: float | Decimal | None) -> Decimal | None:
    """Convert an extracted float to a 2-decimal Decimal for persistence."""
    if value is None:
        return None
    return Decimal(str(round(float(value), 2)))
