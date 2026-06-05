"""Write FleetSchedule and EVChargingSchedule results to JSON files."""

from __future__ import annotations

from pathlib import Path

from ..models.schedule import FleetSchedule


def write_fleet_results(fleet_schedule: FleetSchedule, path: Path) -> None:
    """
    Write a FleetSchedule to a JSON file.

    Args:
        fleet_schedule: The fleet schedule to write.
        path: Output file path (created if it doesn't exist).
    """
    path.write_text(fleet_schedule.model_dump_json(indent=2))
