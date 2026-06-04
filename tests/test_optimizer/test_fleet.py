import pytest

from gridmind.optimizer.fleet import FleetOptimizer


def test_fleet_all_sessions_feasible(fleet_sessions, fleet_site_config) -> None:
    opt = FleetOptimizer(interval_minutes=15)
    result = opt.optimize(fleet_sessions, fleet_site_config)
    assert result.all_sessions_feasible


def test_fleet_feeder_limit_respected(fleet_sessions, fleet_site_config) -> None:
    opt = FleetOptimizer(interval_minutes=15)
    result = opt.optimize(fleet_sessions, fleet_site_config)
    assert result.feeder_limit_respected


def test_fleet_peak_demand_within_limit(fleet_sessions, fleet_site_config) -> None:
    opt = FleetOptimizer(interval_minutes=15)
    result = opt.optimize(fleet_sessions, fleet_site_config)
    assert result.peak_demand_w <= fleet_site_config.grid.max_site_power_w + 1.0


def test_fleet_all_target_socs_met(fleet_sessions, fleet_site_config) -> None:
    opt = FleetOptimizer(interval_minutes=15)
    result = opt.optimize(fleet_sessions, fleet_site_config)
    for sched in result.sessions:
        assert sched.target_soc_met, f"Target SoC not met for {sched.session_id}"


def test_fleet_session_count(fleet_sessions, fleet_site_config) -> None:
    opt = FleetOptimizer(interval_minutes=15)
    result = opt.optimize(fleet_sessions, fleet_site_config)
    assert len(result.sessions) == len(fleet_sessions)


def test_fleet_unknown_charger_raises(single_session, site_config) -> None:
    from gridmind.models.session import EVSession

    bad_session = EVSession(
        session_id="bad",
        charger_id="NONEXISTENT",
        arrival_time=single_session.arrival_time,
        departure_time=single_session.departure_time,
        initial_soc=30.0,
        target_soc=80.0,
        battery_capacity_kwh=60.0,
        max_charge_rate_w=7360.0,
    )
    opt = FleetOptimizer(interval_minutes=15)
    with pytest.raises(ValueError, match="unknown charger"):
        opt.optimize([bad_session], site_config)


def test_fleet_empty_sessions_raises(fleet_site_config) -> None:
    opt = FleetOptimizer(interval_minutes=15)
    with pytest.raises(ValueError, match="At least one session"):
        opt.optimize([], fleet_site_config)
