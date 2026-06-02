from datetime import UTC, datetime

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
