"""
Build OCPP 2.0.1-compliant SetChargingProfile.req payloads.

Key differences from OCPP 1.6:
- Top-level key is "evseId" (not "connectorId")
- chargingSchedule is a list (not a single object)
- transactionId is a string (not int)
- startPeriod semantics unchanged: seconds from startSchedule
"""

from __future__ import annotations

from datetime import UTC, datetime
import json
import logging

from ...constants import OCPP16_MAX_PERIODS_PER_PROFILE
from ...exceptions import OCPPEncodingError
from ...models.schedule import EVChargingSchedule

logger = logging.getLogger(__name__)


def build_set_charging_profile_request(
    schedule: EVChargingSchedule,
    evse_id: int = 1,
    profile_id: int = 1,
    stack_level: int = 0,
    transaction_id: str | None = None,
) -> dict:
    """
    Convert an EVChargingSchedule to an OCPP 2.0.1 SetChargingProfile.req dict.

    Raises:
        OCPPEncodingError: If the schedule cannot be encoded.
    """
    if not schedule.periods:
        raise OCPPEncodingError(
            f"Schedule {schedule.session_id} has no periods — cannot encode"
        )

    schedule_start = schedule.periods[0].start
    if schedule_start.tzinfo is None:
        raise OCPPEncodingError("Schedule periods must have timezone-aware datetimes")

    periods = []
    for period in schedule.periods:
        start_seconds = int((period.start - schedule_start).total_seconds())
        periods.append(
            {
                "startPeriod": max(0, start_seconds),
                "limit": round(period.power_w, 1),
            }
        )
    periods.sort(key=lambda p: p["startPeriod"])

    if len(periods) > OCPP16_MAX_PERIODS_PER_PROFILE:
        raise OCPPEncodingError(
            f"Schedule has {len(periods)} periods, "
            f"exceeding maximum of {OCPP16_MAX_PERIODS_PER_PROFILE}."
        )

    duration_seconds = int((schedule.periods[-1].end - schedule_start).total_seconds())
    charging_schedule = {
        "id": 1,
        "startSchedule": _fmt_dt(schedule_start),
        "duration": duration_seconds,
        "chargingRateUnit": "W",
        "chargingSchedulePeriod": periods,
    }
    charging_profile: dict = {
        "id": profile_id,
        "stackLevel": stack_level,
        "chargingProfilePurpose": "TxDefaultProfile",
        "chargingProfileKind": "Absolute",
        "validFrom": _fmt_dt(schedule_start),
        "validTo": _fmt_dt(schedule.periods[-1].end),
        "chargingSchedule": [charging_schedule],
    }
    if transaction_id is not None:
        charging_profile["transactionId"] = transaction_id

    return {"evseId": evse_id, "chargingProfile": charging_profile}


def to_json(request: dict, indent: int = 2) -> str:
    """Serialise OCPP 2.0.1 request dict to JSON string."""
    return json.dumps(request, indent=indent)


def _fmt_dt(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
