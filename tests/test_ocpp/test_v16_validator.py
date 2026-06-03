from datetime import UTC, datetime

from gridmind.models.ocpp_types import (
    ChargingProfileKind,
    ChargingProfilePurpose,
    ChargingRateUnit,
    OCPP16ChargingProfile,
    OCPP16ChargingSchedule,
    OCPP16ChargingSchedulePeriod,
    OCPP16SetChargingProfileRequest,
)
from gridmind.ocpp.v16.validator import validate_set_charging_profile_request

BASE = datetime(2026, 6, 1, 18, 0, 0, tzinfo=UTC)


def _make_valid_request() -> OCPP16SetChargingProfileRequest:
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
    return OCPP16SetChargingProfileRequest(connectorId=1, csChargingProfiles=profile)


def test_valid_request_passes_validation() -> None:
    req = _make_valid_request()
    validate_set_charging_profile_request(req)  # Should not raise


def test_validation_returns_no_errors_for_valid() -> None:
    req = _make_valid_request()
    errors = validate_set_charging_profile_request(req)
    assert errors == []


def test_serialise_raises_for_non_datetime() -> None:
    """_serialise in v16 validator should raise TypeError for non-datetime objects."""
    import pytest

    from gridmind.ocpp.v16.validator import _serialise

    with pytest.raises(TypeError):
        _serialise("not-a-datetime")
