"""Dashboard stats endpoint (PRD §11)."""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Invoice
from app.models.enums import BusinessStatus, ProcessingStatus, RiskLevel
from app.schemas.invoice import InvoiceSummary

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)) -> dict:
    completed = ProcessingStatus.COMPLETED

    total_processed = (
        db.query(func.count(Invoice.id))
        .filter(Invoice.processing_status == completed)
        .scalar()
    )
    pending_review = (
        db.query(func.count(Invoice.id))
        .filter(
            Invoice.processing_status == completed,
            Invoice.status == BusinessStatus.PENDING_REVIEW,
        )
        .scalar()
    )
    approved = (
        db.query(func.count(Invoice.id))
        .filter(Invoice.status == BusinessStatus.APPROVED)
        .scalar()
    )
    rejected = (
        db.query(func.count(Invoice.id))
        .filter(Invoice.status == BusinessStatus.REJECTED)
        .scalar()
    )
    high_risk = (
        db.query(func.count(Invoice.id))
        .filter(Invoice.risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL]))
        .scalar()
    )
    avg_risk = (
        db.query(func.avg(Invoice.risk_score))
        .filter(Invoice.risk_score.isnot(None))
        .scalar()
    )

    # Risk-level distribution for the dashboard chart
    risk_rows = (
        db.query(Invoice.risk_level, func.count(Invoice.id))
        .filter(Invoice.risk_level.isnot(None))
        .group_by(Invoice.risk_level)
        .all()
    )
    risk_distribution = {level.value: count for level, count in risk_rows}
    for level in RiskLevel:
        risk_distribution.setdefault(level.value, 0)

    recent_stmt = (
        select(Invoice)
        .order_by(Invoice.created_at.desc())
        .limit(6)
        .options(selectinload(Invoice.timesheet))
    )
    recent = list(db.scalars(recent_stmt).all())
    for inv in recent:
        inv.has_timesheet = inv.timesheet is not None  # type: ignore[attr-defined]

    return {
        "total_processed": total_processed,
        "pending_review": pending_review,
        "approved": approved,
        "rejected": rejected,
        "high_risk": high_risk,
        "average_risk_score": round(float(avg_risk), 1) if avg_risk is not None else None,
        "risk_distribution": risk_distribution,
        "recent": [InvoiceSummary.model_validate(inv) for inv in recent],
    }
