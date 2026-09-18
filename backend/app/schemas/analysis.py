"""Schemas for verification results and the analysis pipeline (PRD §20, §21)."""

from enum import Enum

from pydantic import BaseModel

from app.models.enums import AnomalySeverity, RiskLevel


class CheckStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    NOT_PERFORMED = "NOT_PERFORMED"


class CheckResult(BaseModel):
    """One row of the Verification Summary (PRD §20).

    Missing evidence is NOT_PERFORMED, never a pass (PRD §18, rule 14).
    """

    key: str
    label: str
    status: CheckStatus
    detail: str = ""

    def to_storage(self) -> dict:
        return {
            "key": self.key,
            "label": self.label,
            "status": self.status.value,
            "detail": self.detail,
        }


class AnomalyResult(BaseModel):
    type: str
    severity: AnomalySeverity
    title: str
    description: str
    points: int
    evidence: dict


class AnalysisResult(BaseModel):
    """Output of the deterministic analysis stage."""

    checks: list[CheckResult]
    anomalies: list[AnomalyResult]
    risk_score: int
    risk_level: RiskLevel
