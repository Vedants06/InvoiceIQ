"""Enumerations shared across models.

Stored as VARCHAR (native_enum=False) so the same schema works on SQLite and
PostgreSQL without database-level enum types.
"""

import enum


class BusinessStatus(str, enum.Enum):
    """Lifecycle status of an invoice (PRD §30)."""

    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ProcessingStatus(str, enum.Enum):
    """Pipeline status (PRD §30)."""

    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DocumentType(str, enum.Enum):
    INVOICE = "INVOICE"
    CONTRACT = "CONTRACT"
    TIMESHEET = "TIMESHEET"


class ReviewDecision(str, enum.Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class AnomalySeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
