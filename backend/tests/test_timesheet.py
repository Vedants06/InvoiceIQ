"""Deterministic timesheet parsing tests (PRD §16)."""

import pytest

from app.services import timesheet_service


def test_csv_total_hours(tmp_path):
    csv_path = tmp_path / "ts.csv"
    csv_path.write_text(
        "Employee,Date,Hours,Rate,Description\n"
        "John,2026-08-01,40,50,Dev\n"
        "Sarah,2026-08-01,32,50,QA\n"
        "Alex,2026-08-02,23,50,Support\n"
    )
    result = timesheet_service.parse_timesheet(str(csv_path))
    assert result.total_hours == 95.0
    assert result.record_count == 3


def test_xlsx_total_hours(tmp_path):
    pandas = pytest.importorskip("pandas")
    xlsx_path = tmp_path / "ts.xlsx"
    pandas.DataFrame(
        {
            "Employee": ["John", "Sarah"],
            "Date": ["2026-08-01", "2026-08-02"],
            "Hours": [40, 42.5],
            "Rate": [50, 50],
        }
    ).to_excel(xlsx_path, index=False, engine="openpyxl")

    result = timesheet_service.parse_timesheet(str(xlsx_path))
    assert result.total_hours == 82.5
    assert result.record_count == 2


def test_case_insensitive_and_spaced_columns(tmp_path):
    csv_path = tmp_path / "ts.csv"
    csv_path.write_text("Employee Name,Date,Total Hours\nA,2026-08-01,8\nB,2026-08-02,7\n")
    result = timesheet_service.parse_timesheet(str(csv_path))
    assert result.total_hours == 15.0


def test_missing_required_column(tmp_path):
    csv_path = tmp_path / "ts.csv"
    csv_path.write_text("Employee,Hours\nJohn,40\n")  # Date missing
    with pytest.raises(timesheet_service.TimesheetError) as exc:
        timesheet_service.parse_timesheet(str(csv_path))
    assert "Date" in str(exc.value)


def test_invalid_hours_ignored(tmp_path):
    csv_path = tmp_path / "ts.csv"
    csv_path.write_text(
        "Employee,Date,Hours\n"
        "John,2026-08-01,8\n"
        "Bad,2026-08-02,not-a-number\n"
        "Zero,2026-08-03,0\n"
        "Sarah,2026-08-04,7\n"
    )
    result = timesheet_service.parse_timesheet(str(csv_path))
    assert result.total_hours == 15.0
    assert result.record_count == 2


def test_unsupported_extension(tmp_path):
    path = tmp_path / "ts.txt"
    path.write_text("Employee,Date,Hours\nA,2026-08-01,8\n")
    with pytest.raises(timesheet_service.TimesheetError):
        timesheet_service.parse_timesheet(str(path))


def test_empty_hours_raises(tmp_path):
    csv_path = tmp_path / "ts.csv"
    csv_path.write_text("Employee,Date,Hours\nJohn,2026-08-01,\n")
    with pytest.raises(timesheet_service.TimesheetError):
        timesheet_service.parse_timesheet(str(csv_path))
