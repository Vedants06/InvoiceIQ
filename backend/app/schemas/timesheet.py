"""Pydantic schemas for timesheet data."""

from pydantic import BaseModel, ConfigDict


class TimesheetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    vendor_name: str | None = None
    total_hours: float
    file_name: str
