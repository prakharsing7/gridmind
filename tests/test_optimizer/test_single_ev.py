from datetime import UTC, datetime, timedelta

import pytest

from gridmind.models.site import PricePeriod
from gridmind.optimizer.base import BaseOptimizer

BASE = datetime(2026, 6, 1, 18, 0, 0, tzinfo=UTC)


class ConcreteOptimizer(BaseOptimizer):
    """Minimal concrete subclass for testing the ABC."""

    def optimize(self, *args, **kwargs):  # type: ignore[override]
        return None


def test_discretise_horizon_count() -> None:
    opt = ConcreteOptimizer(interval_minutes=15)
    intervals = opt._discretise_horizon(BASE, BASE + timedelta(hours=1))
    assert len(intervals) == 4  # 4 x 15-min slots in 1 hour


def test_discretise_horizon_values() -> None:
    opt = ConcreteOptimizer(interval_minutes=30)
    intervals = opt._discretise_horizon(BASE, BASE + timedelta(hours=1))
    assert intervals[0] == BASE
    assert intervals[1] == BASE + timedelta(minutes=30)


def test_get_price_at_in_period() -> None:
    opt = ConcreteOptimizer()
    periods = [PricePeriod(start=BASE, end=BASE + timedelta(hours=5), price=0.35)]
    assert opt._get_price_at(BASE + timedelta(hours=2), periods) == 0.35


def test_get_price_at_falls_back_to_default() -> None:
    opt = ConcreteOptimizer()
    periods = [PricePeriod(start=BASE, end=BASE + timedelta(hours=1), price=0.35)]
    assert (
        opt._get_price_at(BASE + timedelta(hours=3), periods, default_price=0.99)
        == 0.99
    )


def test_soc_energy_conversions() -> None:
    opt = ConcreteOptimizer()
    assert opt._soc_to_energy_kwh(50.0, 60.0) == 30.0
    assert opt._energy_to_soc(30.0, 60.0) == 50.0


# --- SingleEVOptimizer tests ---


from gridmind.optimizer.single_ev import SingleEVOptimizer  # noqa: E402


def test_target_soc_met(single_session) -> None:
    opt = SingleEVOptimizer(interval_minutes=15)
    sched = opt.optimize(single_session)
    assert sched.target_soc_met
    assert sched.final_soc >= single_session.target_soc - 0.5


def test_power_never_exceeds_max(single_session) -> None:
    opt = SingleEVOptimizer(interval_minutes=15)
    sched = opt.optimize(single_session)
    for period in sched.periods:
        assert period.power_w <= single_session.max_charge_rate_w + 1.0


def test_cheap_rate_cost_lower_than_uncontrolled(
    single_session, tou_price_signal
) -> None:
    """Optimised schedule should cost less than uncontrolled under TOU pricing."""
    from gridmind.optimizer.strategies import uncontrolled_strategy

    opt = SingleEVOptimizer(interval_minutes=15)
    optimised = opt.optimize(single_session, price_signal=tou_price_signal)
    uncontrolled = uncontrolled_strategy(single_session, price_signal=tou_price_signal)
    assert optimised.total_cost < uncontrolled.total_cost


def test_schedule_is_feasible(single_session) -> None:
    opt = SingleEVOptimizer(interval_minutes=15)
    sched = opt.optimize(single_session)
    assert sched.feasible is True


def test_schedule_has_periods(single_session) -> None:
    opt = SingleEVOptimizer(interval_minutes=15)
    sched = opt.optimize(single_session)
    assert len(sched.periods) > 0


def test_external_power_limit_respected(single_session) -> None:
    opt = SingleEVOptimizer(interval_minutes=15)
    limit = 3500.0
    sched = opt.optimize(single_session, external_power_limit_w=limit)
    for period in sched.periods:
        assert period.power_w <= limit + 1.0


def test_flat_rate_produces_positive_cost(single_session) -> None:
    opt = SingleEVOptimizer(interval_minutes=15)
    sched = opt.optimize(single_session, flat_rate=0.25)
    assert sched.total_cost is not None
    assert sched.total_cost > 0


def test_zero_interval_horizon_raises() -> None:
    """When _discretise_horizon returns empty list, optimizer raises InfeasibleError."""
    from unittest.mock import patch

    from gridmind.exceptions import InfeasibleError
    from gridmind.models.session import EVSession

    base = datetime(2026, 6, 1, 18, 0, 0, tzinfo=UTC)
    session = EVSession(
        session_id="zero-window",
        charger_id="c001",
        arrival_time=base,
        departure_time=base + timedelta(hours=14),
        initial_soc=30.0,
        target_soc=80.0,
        battery_capacity_kwh=60.0,
        max_charge_rate_w=7360.0,
    )
    opt = SingleEVOptimizer(interval_minutes=15)
    with (
        patch.object(opt, "_discretise_horizon", return_value=[]),
        pytest.raises(InfeasibleError, match="zero time intervals"),
    ):
        opt.optimize(session)


def test_infeasible_session_raises() -> None:
    """Physically infeasible session (too little time/power) raises InfeasibleError."""
    from gridmind.exceptions import InfeasibleError
    from gridmind.models.session import EVSession

    # Validator allows 5% tolerance, so make it impossible within that margin
    # Use min_charge_rate_w > max_charge_rate_w is invalid; instead use very tight SoC
    # with 0-10% initial and 100% target in 15 minutes at 100W
    base = datetime(2026, 6, 1, 18, 0, 0, tzinfo=UTC)
    # 0% → 80% of 60 kWh at 100 W would take 480 h — not reachable
    # but pydantic validator blocks this. Use min_soc constraint that kills feasibility.
    # Easiest: force min_soc=99 with initial_soc=30, target_soc=80 → always infeasible
    session = EVSession(
        session_id="infeasible-session",
        charger_id="c001",
        arrival_time=base,
        departure_time=base + timedelta(hours=14),
        initial_soc=30.0,
        target_soc=80.0,
        battery_capacity_kwh=60.0,
        max_charge_rate_w=7360.0,
        min_soc=99.0,  # must stay above 99% at all times but starts at 30% → infeasible
    )
    opt = SingleEVOptimizer(interval_minutes=15)
    with pytest.raises(InfeasibleError):
        opt.optimize(session)
