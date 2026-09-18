"""Deterministic risk scoring (PRD §23, §24).

Score = min(sum(anomaly points), 100). Classification bands are calibrated
so the PRD demo scenarios land correctly (PRD §42: timesheet-only anomaly =
25 points = MEDIUM):
  0–24 LOW · 25–59 MEDIUM · 60–79 HIGH · 80–100 CRITICAL

The frontend never computes the score.
"""

from app.models.enums import RiskLevel
from app.schemas.analysis import AnomalyResult


def classify(score: int) -> RiskLevel:
    if score >= 80:
        return RiskLevel.CRITICAL
    if score >= 60:
        return RiskLevel.HIGH
    if score >= 25:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def score_anomalies(anomalies: list[AnomalyResult]) -> tuple[int, RiskLevel]:
    total = min(sum(a.points for a in anomalies), 100)
    return total, classify(total)
