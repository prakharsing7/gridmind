"""Compute summary metrics from FleetSchedule results."""

from __future__ import annotations

from typing import Any

from ..models.schedule import FleetSchedule


def compute_fleet_metrics(fleet_schedule: FleetSchedule) -> dict[str, Any]:
    """
    Compute a summary metrics dict from a FleetSchedule.

    Returns:
        Dict with keys: total_energy_kwh, total_cost, peak_demand_kw,
        avg_demand_kw, num_sessions, all_feasible, feeder_limit_respected,
        demand_response_met, optimisation_duration_ms, solver.
    """
    return {
        "total_energy_kwh": fleet_schedule.total_energy_kwh,
        "total_cost": fleet_schedule.total_cost,
        "peak_demand_kw": fleet_schedule.peak_demand_w / 1000.0,
        "avg_demand_kw": fleet_schedule.avg_demand_w / 1000.0,
        "num_sessions": len(fleet_schedule.sessions),
        "all_feasible": fleet_schedule.all_sessions_feasible,
        "feeder_limit_respected": fleet_schedule.feeder_limit_respected,
        "demand_response_met": fleet_schedule.demand_response_met,
        "optimisation_duration_ms": fleet_schedule.optimisation_duration_ms,
        "solver": fleet_schedule.solver,
    }
