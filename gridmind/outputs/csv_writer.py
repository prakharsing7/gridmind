"""Write charging schedules to CSV files for analysis and research output."""

from __future__ import annotations

import csv
from pathlib import Path

from ..models.schedule import EVChargingSchedule


def write_schedule_csv(schedules: list[EVChargingSchedule], path: Path) -> None:
    """
    Write per-interval schedule data to a CSV file.

    Each row is one schedule period: session_id, charger_id, start, end,
    power_w, price_per_kwh, energy_kwh, cost.

    Args:
        schedules: List of EV charging schedules to write.
        path: Output file path.
    """
    fieldnames = [
        "session_id",
        "charger_id",
        "start",
        "end",
        "power_w",
        "price_per_kwh",
        "energy_kwh",
        "cost",
    ]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for sched in schedules:
            for period in sched.periods:
                writer.writerow(
                    {
                        "session_id": sched.session_id,
                        "charger_id": sched.charger_id,
                        "start": period.start.isoformat(),
                        "end": period.end.isoformat(),
                        "power_w": round(period.power_w, 2),
                        "price_per_kwh": period.price_per_kwh,
                        "energy_kwh": round(period.energy_kwh, 4),
                        "cost": (
                            round(period.cost, 4) if period.cost is not None else None
                        ),
                    }
                )
