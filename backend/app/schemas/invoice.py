"""Pydantic schemas for invoice API responses."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.enums import BusinessStatus, ProcessingStatus, RiskLevel
from app.schemas.anomaly import AnomalyOut
from app.schemas.contract import ContractOut
from app.schemas.document import DocumentOut
from app.schemas.review import ReviewOut
from app.schemas.timesheet import TimesheetOut


class LineItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    description: str | None = None
    quantity: float | None = None
    unit_price: float | None = None
    amount: float | None = None


class UploadResponse(BaseModel):
    invoice_id: uuid.UUID
    status: str
    has_timesheet: bool


class InvoiceSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    invoice_number: str | None = None
    vendor_name: str | None = None
    invoice_date: date | None = None
    currency: str | None = None
    total: float | None = None
    status: BusinessStatus
    processing_status: ProcessingStatus
    risk_score: int | None = None
    risk_level: RiskLevel | None = None
    created_at: datetime
    has_timesheet: bool = False


class InvoiceDetail(BaseModel):
    """Full invoice view (PRD §34 GET /api/invoices/{id}).

    Analysis fields (contract/timesheet/anomalies/checks/explanation) are
    populated by later pipeline steps; they default to empty here.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    invoice_number: str | None = None
    vendor_name: str | None = None
    invoice_date: date | None = None
    due_date: date | None = None
    currency: str | None = None
    subtotal: float | None = None
    tax: float | None = None
    total: float | None = None
    line_items: list[LineItemOut] = []

    status: BusinessStatus
    processing_status: ProcessingStatus
    risk_score: int | None = None
    risk_level: RiskLevel | None = None

    verification_checks: list | None = None
    extraction_coverage: float | None = None
    historical: dict | None = None
    explanation: str | None = None
    explanation_available: bool = False

    created_at: datetime
    updated_at: datetime

    contract: ContractOut | None = None
    timesheet: TimesheetOut | None = None
    documents: list[DocumentOut] = []
    anomalies: list[AnomalyOut] = []
    review: ReviewOut | None = None

    @field_validator("line_items", "documents", "anomalies", mode="before")
    @classmethod
    def _none_to_list(cls, value):
        """Pre-extraction rows store NULL for list columns; coerce to []."""
        return value or []
