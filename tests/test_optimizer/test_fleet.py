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


def test_fleet_explicit_horizon(fleet_sessions, fleet_site_config, base_time) -> None:
    """Passing explicit horizon_start/end should still produce valid results."""
    from datetime import timedelta

    opt = FleetOptimizer(interval_minutes=15)
    result = opt.optimize(
        fleet_sessions,
        fleet_site_config,
        horizon_start=base_time,
        horizon_end=base_time + timedelta(hours=14),
    )
    assert result.all_sessions_feasible


def test_fleet_with_min_charge_rate(base_time, fleet_site_config) -> None:
    """Session with min_charge_rate_w > 0 exercises the p_min_w constraint branch."""
    from datetime import timedelta

    from gridmind.models.session import EVSession

    session = EVSession(
        session_id="ev-minrate",
        charger_id="charger-001",
        arrival_time=base_time,
        departure_time=base_time + timedelta(hours=14),
        initial_soc=30.0,
        target_soc=60.0,
        battery_capacity_kwh=60.0,
        max_charge_rate_w=7360.0,
        min_charge_rate_w=500.0,
    )
    opt = FleetOptimizer(interval_minutes=30)
    result = opt.optimize([session], fleet_site_config)
    assert result.all_sessions_feasible


def test_fleet_with_price_signal(
    fleet_sessions, fleet_site_config, tou_price_signal
) -> None:
    """Fleet optimizer with a PriceSignal exercises the non-None price_signal branch."""
    from gridmind.models.session import ChargerConfig
    from gridmind.models.site import GridConstraints, SiteConfig

    chargers = [
        ChargerConfig(charger_id="charger-001", max_power_w=7360.0),
        ChargerConfig(charger_id="charger-002", max_power_w=7360.0),
        ChargerConfig(charger_id="charger-003", max_power_w=7360.0),
    ]
    site = SiteConfig(
        site_id="test-fleet-site",
        chargers=chargers,
        grid=GridConstraints(max_site_power_w=22000.0),
        flat_rate_price=0.25,
        price_signal=tou_price_signal,
    )
    opt = FleetOptimizer(interval_minutes=15)
    result = opt.optimize(fleet_sessions, site)
    assert result.total_cost > 0
