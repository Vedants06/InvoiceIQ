"""Pydantic schemas for human review decisions."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ReviewDecision


class ReviewRequest(BaseModel):
    decision: ReviewDecision
    # Required when rejecting (validated in the API layer, PRD §28)
    reason: str | None = Field(default=None, max_length=2000)


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    decision: ReviewDecision
    reason: str | None = None
    reviewed_at: datetime
