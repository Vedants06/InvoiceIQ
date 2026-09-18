"""Pydantic schemas for contract data."""

from datetime import date

from pydantic import BaseModel, ConfigDict


class ContractOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    vendor_name: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    hourly_rate: float | None = None
    max_hours: float | None = None
    max_amount: float | None = None
    currency: str | None = None
    payment_terms: str | None = None
