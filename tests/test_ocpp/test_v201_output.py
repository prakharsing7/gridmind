from datetime import UTC, datetime, timedelta
import json

from gridmind.models.schedule import EVChargingSchedule, SchedulePeriod
from gridmind.ocpp.v201.charging_profile import (
    build_set_charging_profile_request,
    to_json,
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
