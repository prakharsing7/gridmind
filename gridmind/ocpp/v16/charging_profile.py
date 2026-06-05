"""
Build OCPP 1.6-compliant SetChargingProfile.req payloads from internal schedules.

Key OCPP 1.6 spec constraints (Section 5.14):
- Max 1024 ChargingSchedulePeriod per profile
- startPeriod values must be in ascending order
- startPeriod is seconds from startSchedule (NOT an absolute timestamp)
- limit values in Watts (chargingRateUnit = "W") or Amperes ("A")
"""

from __future__ import annotations

from datetime import UTC, datetime
import json
import logging

from ...constants import OCPP16_MAX_PERIODS_PER_PROFILE
from ...exceptions import OCPPEncodingError
from ...models.ocpp_types import (
    ChargingProfileKind,
    ChargingProfilePurpose,
    ChargingRateUnit,
    OCPP16ChargingProfile,
    OCPP16ChargingSchedule,
    OCPP16ChargingSchedulePeriod,
    OCPP16SetChargingProfileRequest,
)
from ...models.schedule import EVChargingSchedule

logger = logging.getLogger(__name__)


def build_set_charging_profile_request(
    schedule: EVChargingSchedule,
    connector_id: int = 1,
    profile_id: int = 1,
    stack_level: int = 0,
    transaction_id: int | None = None,
    charging_rate_unit: ChargingRateUnit = ChargingRateUnit.WATTS,
    purpose: ChargingProfilePurpose = ChargingProfilePurpose.TX_DEFAULT,
) -> OCPP16SetChargingProfileRequest:
    """
    Convert an EVChargingSchedule to an OCPP 1.6 SetChargingProfile.req.

    Raises:
        OCPPEncodingError: If the schedule has no periods or contains naive datetimes.
    """
    if not schedule.periods:
        raise OCPPEncodingError(
            f"Schedule {schedule.session_id} has no periods — cannot encode"
        )

    schedule_start = schedule.periods[0].start
    if schedule_start.tzinfo is None:
        raise OCPPEncodingError("Schedule periods must have timezone-aware datetimes")

    ocpp_periods = _build_ocpp_periods(schedule, schedule_start, charging_rate_unit)

    if len(ocpp_periods) > OCPP16_MAX_PERIODS_PER_PROFILE:
        raise OCPPEncodingError(
            f"Schedule has {len(ocpp_periods)} periods, exceeding OCPP 1.6 maximum of "
            f"{OCPP16_MAX_PERIODS_PER_PROFILE}. Increase interval_minutes to reduce periods."
        )

    duration_seconds = int((schedule.periods[-1].end - schedule_start).total_seconds())

    charging_schedule = OCPP16ChargingSchedule(
        duration=duration_seconds,
        startSchedule=schedule_start,
        chargingRateUnit=charging_rate_unit,
        chargingSchedulePeriod=ocpp_periods,
    )
    charging_profile = OCPP16ChargingProfile(
        chargingProfileId=profile_id,
        transactionId=transaction_id,
        stackLevel=stack_level,
        chargingProfilePurpose=purpose,
        chargingProfileKind=ChargingProfileKind.ABSOLUTE,
        validFrom=schedule_start,
        validTo=schedule.periods[-1].end,
        chargingSchedule=charging_schedule,
    )
    return OCPP16SetChargingProfileRequest(
        connectorId=connector_id,
        csChargingProfiles=charging_profile,
    )


def _build_ocpp_periods(
    schedule: EVChargingSchedule,
    schedule_start: datetime,
    charging_rate_unit: ChargingRateUnit,
) -> list[OCPP16ChargingSchedulePeriod]:
    """Convert SchedulePeriod list to OCPP ChargingSchedulePeriod list.
    startPeriod = seconds elapsed since schedule_start (NOT absolute time).
    """
    ocpp_periods = []
    for period in schedule.periods:
        start_seconds = int((period.start - schedule_start).total_seconds())
        if charging_rate_unit == ChargingRateUnit.WATTS:
            limit = round(period.power_w, 1)
        else:
            limit = round(period.power_w / 230.0, 1)  # W -> A at 230 V single-phase
        ocpp_periods.append(
            OCPP16ChargingSchedulePeriod(
                startPeriod=max(0, start_seconds),
                limit=limit,
            )
        )
    ocpp_periods.sort(key=lambda p: p.startPeriod)
    return ocpp_periods


def to_json(request: OCPP16SetChargingProfileRequest, indent: int = 2) -> str:
    """Serialise SetChargingProfile.req to JSON. Datetimes as ISO 8601 UTC ('Z' suffix)."""
    data = request.model_dump(exclude_none=True)
    return json.dumps(data, indent=indent, default=_serialise_dt)


def to_ocpp_message(
    request: OCPP16SetChargingProfileRequest,
    message_id: str = "optimizer-001",
) -> str:
    """Format as OCPP 1.6 WebSocket CALL message: [2, UniqueId, Action, Payload]."""
    data = request.model_dump(exclude_none=True)
    payload = json.loads(json.dumps(data, default=_serialise_dt))
    return json.dumps([2, message_id, "SetChargingProfile", payload])


def _serialise_dt(obj: object) -> str:
    if isinstance(obj, datetime):
        if obj.tzinfo is None:
            obj = obj.replace(tzinfo=UTC)
        return obj.strftime("%Y-%m-%dT%H:%M:%SZ")
    raise TypeError(f"Cannot serialise {type(obj)}")
