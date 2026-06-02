from datetime import UTC, datetime, timedelta

import pytest

from gridmind.constants import DEFAULT_CHARGING_EFFICIENCY
from gridmind.exceptions import (
    ConfigValidationError,
    InfeasibleError,
    OCPPEncodingError,
    OCPPOptimizerError,
    OptimisationError,
    SessionConflictError,
    SolverError,
)
from gridmind.models.session import EVSession

BASE_TIME = datetime(2026, 6, 1, 18, 0, 0, tzinfo=UTC)


def test_exception_hierarchy():
    assert issubclass(OptimisationError, OCPPOptimizerError)
    assert issubclass(InfeasibleError, OptimisationError)
    assert issubclass(SolverError, OptimisationError)
    assert issubclass(OCPPEncodingError, OCPPOptimizerError)
    assert issubclass(ConfigValidationError, OCPPOptimizerError)
    assert issubclass(SessionConflictError, OCPPOptimizerError)


def test_infeasible_error_is_catchable_as_base():
    with pytest.raises(OCPPOptimizerError):
        raise InfeasibleError("not enough time")


def test_ev_session_valid():
    s = EVSession(
        session_id="s001",
        charger_id="c001",
        arrival_time=BASE_TIME,
        departure_time=BASE_TIME + timedelta(hours=14),
        initial_soc=30.0,
        target_soc=80.0,
        battery_capacity_kwh=60.0,
        max_charge_rate_w=7360.0,
    )
    assert s.session_id == "s001"
    assert s.charging_efficiency == DEFAULT_CHARGING_EFFICIENCY


def test_ev_session_departure_before_arrival_raises():
    with pytest.raises(ValueError, match="departure_time must be after arrival_time"):
        EVSession(
            session_id="s001",
            charger_id="c001",
            arrival_time=BASE_TIME,
            departure_time=BASE_TIME - timedelta(hours=1),
            initial_soc=30.0,
            battery_capacity_kwh=60.0,
            max_charge_rate_w=7360.0,
        )


def test_ev_session_unreachable_target_soc_raises():
    with pytest.raises(ValueError, match="not reachable"):
        EVSession(
            session_id="s001",
            charger_id="c001",
            arrival_time=BASE_TIME,
            departure_time=BASE_TIME + timedelta(minutes=30),
            initial_soc=0.0,
            target_soc=80.0,
            battery_capacity_kwh=60.0,
            max_charge_rate_w=7360.0,
        )


def test_session_duration_hours_property():
    s = EVSession(
        session_id="s001",
        charger_id="c001",
        arrival_time=BASE_TIME,
        departure_time=BASE_TIME + timedelta(hours=14),
        initial_soc=30.0,
        target_soc=80.0,
        battery_capacity_kwh=60.0,
        max_charge_rate_w=7360.0,
    )
    assert s.session_duration_hours == 14.0


def test_energy_needed_kwh_property():
    s = EVSession(
        session_id="s001",
        charger_id="c001",
        arrival_time=BASE_TIME,
        departure_time=BASE_TIME + timedelta(hours=14),
        initial_soc=30.0,
        target_soc=80.0,
        battery_capacity_kwh=60.0,
        max_charge_rate_w=7360.0,
        charging_efficiency=1.0,
    )
    # (80 - 30) / 100 * 60 / 1.0 = 30 kWh
    assert abs(s.energy_needed_kwh - 30.0) < 0.01
