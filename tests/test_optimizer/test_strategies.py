from gridmind.optimizer.strategies import uncontrolled_strategy


def test_uncontrolled_charges_at_max_power(single_session) -> None:
    sched = uncontrolled_strategy(single_session)
    charging_periods = [p for p in sched.periods if p.power_w > 0]
    assert all(
        abs(p.power_w - single_session.max_charge_rate_w) < 1.0
        for p in charging_periods
    )


def test_uncontrolled_target_soc_met(single_session) -> None:
    sched = uncontrolled_strategy(single_session)
    assert sched.target_soc_met


def test_uncontrolled_charges_immediately(single_session) -> None:
    """Uncontrolled charging starts at arrival, not deferred."""
    sched = uncontrolled_strategy(single_session)
    first_charging = next(p for p in sched.periods if p.power_w > 0)
    assert first_charging.start == single_session.arrival_time


def test_uncontrolled_respects_price_signal_for_cost(
    single_session, tou_price_signal
) -> None:
    sched = uncontrolled_strategy(single_session, price_signal=tou_price_signal)
    assert sched.total_cost is not None
    assert sched.total_cost > 0


def test_uncontrolled_solver_status(single_session) -> None:
    sched = uncontrolled_strategy(single_session)
    assert sched.solver_status == "UNCONTROLLED_BASELINE"


def test_uncontrolled_feasible(single_session) -> None:
    sched = uncontrolled_strategy(single_session)
    assert sched.feasible is True
