"""Tests for the CSV session loader."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from gridmind.inputs.csv_loader import load_sessions_from_csv


def _write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


_VALID_ROW = {
    "session_id": "s001",
    "charger_id": "c001",
    "arrival_time": "2026-06-01T18:00:00+00:00",
    "departure_time": "2026-06-02T08:00:00+00:00",
    "initial_soc": "30.0",
    "target_soc": "80.0",
    "battery_capacity_kwh": "60.0",
    "max_charge_rate_w": "7360.0",
}


def test_load_sessions_from_csv_valid(tmp_path: Path) -> None:
    csv_file = tmp_path / "sessions.csv"
    _write_csv(csv_file, [_VALID_ROW])
    sessions = load_sessions_from_csv(csv_file)
    assert len(sessions) == 1
    assert sessions[0].session_id == "s001"
    assert sessions[0].charger_id == "c001"


def test_load_sessions_from_csv_multiple_rows(tmp_path: Path) -> None:
    csv_file = tmp_path / "sessions.csv"
    row2 = {**_VALID_ROW, "session_id": "s002", "charger_id": "c002"}
    _write_csv(csv_file, [_VALID_ROW, row2])
    sessions = load_sessions_from_csv(csv_file)
    assert len(sessions) == 2
    assert sessions[1].session_id == "s002"


def test_load_sessions_from_csv_optional_min_charge_rate(tmp_path: Path) -> None:
    csv_file = tmp_path / "sessions.csv"
    row = {**_VALID_ROW, "min_charge_rate_w": "1000.0"}
    _write_csv(csv_file, [row])
    sessions = load_sessions_from_csv(csv_file)
    assert sessions[0].min_charge_rate_w == 1000.0


def test_load_sessions_from_csv_optional_charging_efficiency(tmp_path: Path) -> None:
    csv_file = tmp_path / "sessions.csv"
    row = {**_VALID_ROW, "charging_efficiency": "0.92"}
    _write_csv(csv_file, [row])
    sessions = load_sessions_from_csv(csv_file)
    assert sessions[0].charging_efficiency == pytest.approx(0.92)


def test_load_sessions_from_csv_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_sessions_from_csv(tmp_path / "nonexistent.csv")


def test_load_sessions_from_csv_bad_float_raises(tmp_path: Path) -> None:
    csv_file = tmp_path / "bad.csv"
    _write_csv(
        csv_file,
        [
            {
                **_VALID_ROW,
                "initial_soc": "not-a-float",
            }
        ],
    )
    with pytest.raises(ValueError, match="Row 2"):
        load_sessions_from_csv(csv_file)


def test_load_sessions_from_csv_missing_required_column_raises(
    tmp_path: Path,
) -> None:
    csv_file = tmp_path / "missing_col.csv"
    row = {k: v for k, v in _VALID_ROW.items() if k != "session_id"}
    _write_csv(csv_file, [row])
    with pytest.raises(ValueError, match="Row 2"):
        load_sessions_from_csv(csv_file)
