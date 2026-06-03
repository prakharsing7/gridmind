"""Synthetic session and config generators for testing and CLI examples."""

from __future__ import annotations

from typing import Any


def generate_example_config(config_type: str) -> dict[str, Any]:
    """
    Generate a template config dict for the given type.

    Args:
        config_type: One of 'single-ev' or 'fleet'.

    Returns:
        Dict ready for JSON serialisation and use as CLI --config input.

    Raises:
        ValueError: If config_type is not recognised.
    """
    if config_type == "single-ev":
        return {
            "type": "single_ev",
            "session": {
                "session_id": "demo-session-001",
                "charger_id": "charger-001",
                "arrival_time": "2026-06-01T18:00:00+00:00",
                "departure_time": "2026-06-02T08:00:00+00:00",
                "initial_soc": 30.0,
                "target_soc": 80.0,
                "battery_capacity_kwh": 60.0,
                "max_charge_rate_w": 7360.0,
            },
            "price_signal": {
                "periods": [
                    {
                        "start": "2026-06-01T18:00:00+00:00",
                        "end": "2026-06-01T23:00:00+00:00",
                        "price": 0.35,
                    },
                    {
                        "start": "2026-06-01T23:00:00+00:00",
                        "end": "2026-06-02T08:00:00+00:00",
                        "price": 0.10,
                    },
                ],
                "currency": "EUR",
                "unit": "EUR/kWh",
            },
        }
    elif config_type == "fleet":
        return {
            "type": "fleet",
            "site_config": {
                "site_id": "demo-fleet-site",
                "chargers": [
                    {"charger_id": "CHARGER-01", "max_power_w": 7360.0},
                    {"charger_id": "CHARGER-02", "max_power_w": 7360.0},
                    {"charger_id": "CHARGER-03", "max_power_w": 11000.0},
                ],
                "grid": {"max_site_power_w": 22000.0},
                "flat_rate_price": 0.25,
                "optimisation_interval_minutes": 15,
            },
            "sessions": [
                {
                    "session_id": "s001",
                    "charger_id": "CHARGER-01",
                    "arrival_time": "2026-06-01T17:00:00+00:00",
                    "departure_time": "2026-06-02T08:00:00+00:00",
                    "initial_soc": 25.0,
                    "target_soc": 80.0,
                    "battery_capacity_kwh": 60.0,
                    "max_charge_rate_w": 7360.0,
                },
                {
                    "session_id": "s002",
                    "charger_id": "CHARGER-02",
                    "arrival_time": "2026-06-01T19:00:00+00:00",
                    "departure_time": "2026-06-02T07:00:00+00:00",
                    "initial_soc": 45.0,
                    "target_soc": 90.0,
                    "battery_capacity_kwh": 77.0,
                    "max_charge_rate_w": 7360.0,
                },
                {
                    "session_id": "s003",
                    "charger_id": "CHARGER-03",
                    "arrival_time": "2026-06-01T18:30:00+00:00",
                    "departure_time": "2026-06-02T09:00:00+00:00",
                    "initial_soc": 10.0,
                    "target_soc": 80.0,
                    "battery_capacity_kwh": 82.0,
                    "max_charge_rate_w": 11000.0,
                },
            ],
        }
    else:
        raise ValueError(
            f"Unknown config type: '{config_type}'. Use 'single-ev' or 'fleet'."
        )
