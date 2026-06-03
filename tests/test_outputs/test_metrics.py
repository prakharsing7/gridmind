import csv
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path

from gridmind.models.schedule import EVChargingSchedule, FleetSchedule, SchedulePeriod
from gridmind.outputs.csv_writer import write_schedule_csv
from gridmind.outputs.json_writer import write_fleet_results
from gridmind.outputs.metrics import compute_fleet_metrics

BASE = datetime(2026, 6, 1, 18, 0, 0, tzinfo=UTC)


def _make_fleet_schedule() -> FleetSchedule:
    period = SchedulePeriod(
        start=BASE, end=BASE + timedelta(hours=5), power_w=7360.0, price_per_kwh=0.25
    )
    ev = EVChargingSchedule(
        session_id="s001",
        charger_id="c001",
        periods=[period],
        total_energy_kwh=36.8,
        final_soc=80.0,
        total_cost=9.2,
        target_soc_met=True,
        feasible=True,
        solver_status="optimal",
        optimised_at=BASE,
        optimisation_duration_ms=50.0,
    )
    return FleetSchedule(
        site_id="site-001",
        sessions=[ev],
        total_energy_kwh=36.8,
        total_cost=9.2,
        peak_demand_w=7360.0,
        avg_demand_w=5000.0,
        feeder_limit_respected=True,
        all_sessions_feasible=True,
        demand_response_met=True,
        optimised_at=BASE,
        optimisation_duration_ms=100.0,
        solver="CLARABEL",
        num_variables=56,
        num_constraints=114,
    )


def test_compute_fleet_metrics_keys() -> None:
    fs = _make_fleet_schedule()
    metrics = compute_fleet_metrics(fs)
    assert "total_energy_kwh" in metrics
    assert "total_cost" in metrics
    assert "peak_demand_kw" in metrics
    assert "num_sessions" in metrics
    assert "all_feasible" in metrics


def test_compute_fleet_metrics_values() -> None:
    fs = _make_fleet_schedule()
    metrics = compute_fleet_metrics(fs)
    assert metrics["total_energy_kwh"] == 36.8
    assert abs(metrics["peak_demand_kw"] - 7.36) < 0.01
    assert metrics["num_sessions"] == 1


def test_write_fleet_results(tmp_path: Path) -> None:
    fs = _make_fleet_schedule()
    output_file = tmp_path / "results.json"
    write_fleet_results(fs, output_file)
    data = json.loads(output_file.read_text())
    assert "site_id" in data
    assert data["site_id"] == "site-001"


def test_write_schedule_csv(tmp_path: Path) -> None:
    fs = _make_fleet_schedule()
    output_file = tmp_path / "schedule.csv"
    write_schedule_csv(fs.sessions, output_file)
    rows = list(csv.DictReader(output_file.open()))
    assert len(rows) > 0
    assert "session_id" in rows[0]
    assert "power_w" in rows[0]
