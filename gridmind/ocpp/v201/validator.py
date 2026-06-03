"""
Structural validator for OCPP 2.0.1 SetChargingProfile.req payloads.

OCPP 2.0.1 JSON schemas are not publicly distributed, so this performs
structural checks rather than full JSON Schema validation.
"""

from __future__ import annotations

from typing import Any


def validate_set_charging_profile_request(request: dict[str, Any]) -> list[str]:
    """
    Structurally validate an OCPP 2.0.1 SetChargingProfile.req dict.

    Returns:
        List of error strings. Empty = valid.
    """
    errors: list[str] = []

    if "evseId" not in request:
        errors.append("Missing required field: evseId")
    if "chargingProfile" not in request:
        errors.append("Missing required field: chargingProfile")
        return errors

    profile = request["chargingProfile"]
    if "chargingSchedule" not in profile or not profile["chargingSchedule"]:
        errors.append("chargingProfile.chargingSchedule must be a non-empty list")
        return errors

    schedule = profile["chargingSchedule"][0]
    if "chargingSchedulePeriod" not in schedule:
        errors.append("chargingSchedule[0].chargingSchedulePeriod is required")
    else:
        starts = [p.get("startPeriod", -1) for p in schedule["chargingSchedulePeriod"]]
        if starts != sorted(starts):
            errors.append(
                "chargingSchedulePeriod startPeriod values must be in ascending order"
            )

    return errors
