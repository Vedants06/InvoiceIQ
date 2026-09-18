"""Pydantic schemas for anomalies (verified, evidence-backed findings)."""

import uuid

from pydantic import BaseModel, ConfigDict

from app.models.enums import AnomalySeverity


class AnomalyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: str
    severity: AnomalySeverity
    title: str
    description: str
    points: int
    evidence: dict
