"""Write FleetSchedule and EVChargingSchedule results to JSON files."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path

from ..models.schedule import FleetSchedule


def _serialise(obj: object) -> str:
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Cannot serialise {type(obj)}")


def write_fleet_results(fleet_schedule: FleetSchedule, path: Path) -> None:
    """
    Write a FleetSchedule to a JSON file.

    Args:
        fleet_schedule: The fleet schedule to write.
        path: Output file path (created if it doesn't exist).
    """
    data = fleet_schedule.model_dump()
    path.write_text(json.dumps(data, indent=2, default=_serialise))
