"""
Load EV sessions from a CSV file.

CSV columns (case-insensitive):
    session_id, charger_id, arrival_time, departure_time,
    initial_soc, target_soc, battery_capacity_kwh, max_charge_rate_w,
    min_charge_rate_w (optional), charging_efficiency (optional)
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from ..models.session import EVSession


def load_sessions_from_csv(path: Path) -> list[EVSession]:
    """
    Parse a CSV file into a list of EVSession objects.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If a required column is missing or a row is invalid.
    """
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    sessions: list[EVSession] = []
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):
            lower_row = {k.strip().lower(): v.strip() for k, v in row.items()}
            try:
                kwargs: dict[str, Any] = {
                    "session_id": lower_row["session_id"],
                    "charger_id": lower_row["charger_id"],
                    "arrival_time": lower_row["arrival_time"],
                    "departure_time": lower_row["departure_time"],
                    "initial_soc": float(lower_row["initial_soc"]),
                    "battery_capacity_kwh": float(lower_row["battery_capacity_kwh"]),
                    "max_charge_rate_w": float(lower_row["max_charge_rate_w"]),
                }
                if lower_row.get("target_soc"):
                    kwargs["target_soc"] = float(lower_row["target_soc"])
                if lower_row.get("min_charge_rate_w"):
                    kwargs["min_charge_rate_w"] = float(lower_row["min_charge_rate_w"])
                if lower_row.get("charging_efficiency"):
                    kwargs["charging_efficiency"] = float(
                        lower_row["charging_efficiency"]
                    )
                sessions.append(EVSession.model_validate(kwargs))
            except (KeyError, ValueError) as e:
                raise ValueError(f"Row {row_num} in {path}: {e}") from e

    return sessions
