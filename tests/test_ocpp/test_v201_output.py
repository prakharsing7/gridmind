from datetime import UTC, datetime, timedelta
import json

import pytest

from gridmind.exceptions import OCPPEncodingError
from gridmind.models.schedule import EVChargingSchedule, SchedulePeriod
from gridmind.ocpp.v201.charging_profile import (
    build_set_charging_profile_request,
    to_json,
)
from gridmind.ocpp.v201.validator import (
    validate_set_charging_profile_request as v201_validate,
)

BASE = datetime(2026, 6, 1, 18, 0, 0, tzinfo=UTC)


def _make_schedule() -> EVChargingSchedule:
    return EVChargingSchedule(
        session_id="s001",
        charger_id="c001",
        periods=[
            SchedulePeriod(
                start=BASE,
                end=BASE + timedelta(hours=5),
                power_w=7360.0,
                price_per_kwh=0.25,
            ),
            SchedulePeriod(
                start=BASE + timedelta(hours=5),
                end=BASE + timedelta(hours=14),
                power_w=0.0,
                price_per_kwh=0.10,
            ),
        ],
        total_energy_kwh=36.8,
        final_soc=80.0,
        total_cost=9.2,
        target_soc_met=True,
        feasible=True,
        solver_status="optimal",
        optimised_at=BASE,
        optimisation_duration_ms=50.0,
    )


def test_v201_request_has_evse_id() -> None:
    sched = _make_schedule()
    req = build_set_charging_profile_request(sched, evse_id=1)
    assert req["evseId"] == 1


def test_v201_request_has_charging_profile() -> None:
    sched = _make_schedule()
    req = build_set_charging_profile_request(sched)
    assert "chargingProfile" in req


def test_v201_periods_ascending() -> None:
    sched = _make_schedule()
    req = build_set_charging_profile_request(sched)
    periods = req["chargingProfile"]["chargingSchedule"][0]["chargingSchedulePeriod"]
    starts = [p["startPeriod"] for p in periods]
    assert starts == sorted(starts)


def test_v201_to_json_valid() -> None:
    sched = _make_schedule()
    req = build_set_charging_profile_request(sched)
    output = to_json(req)
    data = json.loads(output)
    assert "evseId" in data


def test_v201_start_period_zero() -> None:
    sched = _make_schedule()
    req = build_set_charging_profile_request(sched)
    first = req["chargingProfile"]["chargingSchedule"][0]["chargingSchedulePeriod"][0]
    assert first["startPeriod"] == 0


def test_v201_empty_periods_raises() -> None:
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


def test_v201_naive_datetime_raises() -> None:
    naive_base = datetime(2026, 6, 1, 18, 0, 0)  # no tzinfo
    sched = EVChargingSchedule(
        session_id="s001",
        charger_id="c001",
        periods=[
            SchedulePeriod(
                start=naive_base,
                end=naive_base + timedelta(hours=5),
                power_w=7360.0,
                price_per_kwh=0.25,
            )
        ],
        total_energy_kwh=36.8,
        final_soc=80.0,
        total_cost=9.2,
        target_soc_met=True,
        feasible=True,
        solver_status="optimal",
        optimised_at=BASE,
        optimisation_duration_ms=50.0,
    )
    with pytest.raises(OCPPEncodingError, match="timezone-aware"):
        build_set_charging_profile_request(sched)


def test_v201_transaction_id_included() -> None:
    sched = _make_schedule()
    req = build_set_charging_profile_request(sched, transaction_id="tx-abc-123")
    assert req["chargingProfile"]["transactionId"] == "tx-abc-123"


# --- validator tests ---


def test_v201_validator_valid_request() -> None:
    sched = _make_schedule()
    req = build_set_charging_profile_request(sched)
    errors = v201_validate(req)
    assert errors == []


def test_v201_validator_missing_evse_id() -> None:
    errors = v201_validate(
        {"chargingProfile": {"chargingSchedule": [{"chargingSchedulePeriod": []}]}}
    )
    assert any("evseId" in e for e in errors)


def test_v201_validator_missing_charging_profile() -> None:
    errors = v201_validate({"evseId": 1})
    assert any("chargingProfile" in e for e in errors)


def test_v201_validator_empty_schedule() -> None:
    errors = v201_validate({"evseId": 1, "chargingProfile": {"chargingSchedule": []}})
    assert any("chargingSchedule" in e for e in errors)


def test_v201_validator_non_ascending_periods() -> None:
    req = {
        "evseId": 1,
        "chargingProfile": {
            "chargingSchedule": [
                {
                    "chargingSchedulePeriod": [
                        {"startPeriod": 100, "limit": 7360.0},
                        {"startPeriod": 0, "limit": 0.0},
                    ]
                }
            ]
        },
    }
    errors = v201_validate(req)
    assert any("ascending" in e for e in errors)
