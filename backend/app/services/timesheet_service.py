"""Timesheet processing (PRD §16, §9.3) — fully deterministic, NO LLM.

Reads CSV or XLSX with expected columns Employee, Date, Hours, Rate,
Description (Employee, Date, Hours mandatory), sums the recorded hours,
and persists the total onto the timesheet row.
"""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

import re

import pandas as pd
from sqlalchemy.orm import Session

from app.models import Timesheet


class TimesheetError(Exception):
    """Raised when a timesheet file cannot be parsed or lacks required data."""


REQUIRED_COLUMNS = {"employee", "date", "hours"}


def _norm(col: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(col).lower())


def _canonical(norm_col: str) -> str | None:
    """Map a normalized column name to a canonical required field."""
    if "hour" in norm_col or norm_col in ("hrs", "hr"):
        return "hours"
    if "date" in norm_col or norm_col == "day":
        return "date"
    if "employee" in norm_col or norm_col in (
        "name",
        "resource",
        "consultant",
        "staff",
        "worker",
        "person",
    ):
        return "employee"
    return None


@dataclass
class TimesheetResult:
    total_hours: float
    record_count: int


def _read_dataframe(file_path: str) -> pd.DataFrame:
    lower = file_path.lower()
    if lower.endswith(".csv"):
        return pd.read_csv(file_path)
    if lower.endswith(".xlsx"):
        return pd.read_excel(file_path, engine="openpyxl")
    raise TimesheetError(
        "Timesheet must be a supported CSV or XLSX file."
    )


def parse_timesheet(file_path: str) -> TimesheetResult:
    """Parse a timesheet file and return the total recorded hours."""
    try:
        df = _read_dataframe(file_path)
    except TimesheetError:
        raise
    except Exception as exc:
        raise TimesheetError(
            "We couldn't read the timesheet. Please check the file and try again."
        ) from exc

    # Normalize common column aliases ("Total Hours", "Employee Name", ...)
    rename = {}
    seen: set[str] = set()
    for col in df.columns:
        canonical = _canonical(_norm(col))
        if canonical and canonical not in seen:
            rename[col] = canonical
            seen.add(canonical)
    df = df.rename(columns=rename)

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise TimesheetError(
            "The timesheet is missing required columns: "
            + ", ".join(sorted(m.capitalize() for m in missing))
            + "."
        )

    # Coerce Hours to numeric; invalid/blank rows are dropped deterministically.
    hours = pd.to_numeric(df["hours"], errors="coerce")
    valid_hours = hours[(hours.notna()) & (hours > 0)]
    if valid_hours.empty:
        raise TimesheetError(
            "The timesheet contains no valid recorded hours."
        )

    total = Decimal("0")
    for value in valid_hours:
        try:
            total += Decimal(str(round(float(value), 2)))
        except (InvalidOperation, ValueError):
            continue

    return TimesheetResult(
        total_hours=float(total.quantize(Decimal("0.01"))),
        record_count=int(valid_hours.shape[0]),
    )


def persist_timesheet(
    db: Session, invoice_id, file_path: str, file_name: str
) -> TimesheetResult:
    """Parse and persist the deterministic timesheet total for an invoice."""
    result = parse_timesheet(file_path)

    timesheet = (
        db.query(Timesheet).filter(Timesheet.invoice_id == invoice_id).one_or_none()
    )
    if timesheet is None:
        timesheet = Timesheet(invoice_id=invoice_id, file_name=file_name)
        db.add(timesheet)

    timesheet.total_hours = Decimal(str(result.total_hours))
    timesheet.file_name = file_name
    return result
