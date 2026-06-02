from datetime import UTC, datetime, timedelta

import pytest

from gridmind.models.ocpp_types import (
    ChargingProfileKind,
    ChargingProfilePurpose,
    ChargingRateUnit,
    OCPP16ChargingProfile,
    OCPP16ChargingSchedule,
    OCPP16ChargingSchedulePeriod,
    OCPP16SetChargingProfileRequest,
)

BASE = datetime(2026, 6, 1, 18, 0, 0, tzinfo=UTC)


def test_charging_rate_unit_values() -> None:
    assert ChargingRateUnit.WATTS == "W"
    assert ChargingRateUnit.AMPERES == "A"


def test_charging_profile_kind_values() -> None:
    assert ChargingProfileKind.ABSOLUTE == "Absolute"
    assert ChargingProfileKind.RELATIVE == "Relative"


def test_ocpp16_schedule_period_valid() -> None:
    p = OCPP16ChargingSchedulePeriod(startPeriod=0, limit=7360.0)
    assert p.startPeriod == 0
    assert p.limit == 7360.0
    assert p.numberPhases is None


def test_ocpp16_schedule_period_negative_start_raises() -> None:
    with pytest.raises(ValueError):
        OCPP16ChargingSchedulePeriod(startPeriod=-1, limit=7360.0)


def test_ocpp16_set_charging_profile_request_structure() -> None:
    period = OCPP16ChargingSchedulePeriod(startPeriod=0, limit=7360.0)
    schedule = OCPP16ChargingSchedule(
        duration=50400,
        startSchedule=BASE,
        chargingRateUnit=ChargingRateUnit.WATTS,
        chargingSchedulePeriod=[period],
    )
    profile = OCPP16ChargingProfile(
        chargingProfileId=1,
        stackLevel=0,
        chargingProfilePurpose=ChargingProfilePurpose.TX_DEFAULT,
        chargingProfileKind=ChargingProfileKind.ABSOLUTE,
        chargingSchedule=schedule,
    )
    req = OCPP16SetChargingProfileRequest(connectorId=1, csChargingProfiles=profile)
    data = req.model_dump(exclude_none=True)
    assert "connectorId" in data
    assert "csChargingProfiles" in data
    assert data["connectorId"] == 1


# --- charging_profile builder tests ---

import json as _json  # noqa: E402

from gridmind.exceptions import OCPPEncodingError  # noqa: E402
from gridmind.models.schedule import EVChargingSchedule, SchedulePeriod  # noqa: E402
from gridmind.ocpp.v16.charging_profile import (  # noqa: E402
    build_set_charging_profile_request,
    to_json,
    to_ocpp_message,
)


def _make_schedule(n_periods: int = 2) -> EVChargingSchedule:
    periods = [
        SchedulePeriod(
            start=BASE + timedelta(hours=i * 5),
            end=BASE + timedelta(hours=(i + 1) * 5),
            power_w=7360.0 if i == 0 else 0.0,
            price_per_kwh=0.25,
        )
        for i in range(n_periods)
    ]
    return EVChargingSchedule(
        session_id="s001",
        charger_id="c001",
        periods=periods,
        total_energy_kwh=36.8,
        final_soc=80.0,
        total_cost=9.2,
        target_soc_met=True,
        feasible=True,
        solver_status="optimal",
        optimised_at=BASE,
        optimisation_duration_ms=50.0,
    )


def test_build_request_connector_id() -> None:
    sched = _make_schedule()
    req = build_set_charging_profile_request(sched, connector_id=1)
    assert req.connectorId == 1


def test_build_request_start_period_is_zero() -> None:
    sched = _make_schedule()
    req = build_set_charging_profile_request(sched)
    first_period = req.csChargingProfiles.chargingSchedule.chargingSchedulePeriod[0]
    assert first_period.startPeriod == 0


def test_build_request_periods_ascending() -> None:
    sched = _make_schedule(3)
    req = build_set_charging_profile_request(sched)
    starts = [
        p.startPeriod
        for p in req.csChargingProfiles.chargingSchedule.chargingSchedulePeriod
    ]
    assert starts == sorted(starts)


def test_to_json_produces_valid_json() -> None:
    sched = _make_schedule()
    req = build_set_charging_profile_request(sched)
    output = to_json(req)
    data = _json.loads(output)
    assert "connectorId" in data
    assert "csChargingProfiles" in data


def test_to_json_datetimes_are_utc_strings() -> None:
    sched = _make_schedule()
    req = build_set_charging_profile_request(sched)
    output = to_json(req)
    data = _json.loads(output)
    start_schedule = data["csChargingProfiles"]["chargingSchedule"]["startSchedule"]
    assert start_schedule.endswith(
        "Z"
    ), f"Expected UTC 'Z' suffix, got: {start_schedule}"


def test_to_ocpp_message_format() -> None:
    sched = _make_schedule()
    req = build_set_charging_profile_request(sched)
    msg = _json.loads(to_ocpp_message(req, message_id="test-001"))
    assert msg[0] == 2  # CALL message type
    assert msg[1] == "test-001"  # message id
    assert msg[2] == "SetChargingProfile"  # action
    assert "connectorId" in msg[3]  # payload


def test_empty_periods_raises() -> None:
    from gridmind.models.schedule import EVChargingSchedule

    sched = EVChargingSchedule(
        session_id="s001",
        charger_id="c001",
        periods=[],
        total_energy_kwh=0.0,
        final_soc=30.0,
        total_cost=0.0,
        target_soc_met=False,
        feasible=False,
        solver_status="infeasible",
        optimised_at=BASE,
        optimisation_duration_ms=0.0,
    )
    with pytest.raises(OCPPEncodingError, match="no periods"):
        build_set_charging_profile_request(sched)
