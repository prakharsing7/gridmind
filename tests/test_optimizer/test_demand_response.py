from datetime import UTC, datetime, timedelta

from gridmind.models.site import GridConstraints
from gridmind.optimizer.demand_response import apply_demand_response

BASE = datetime(2026, 6, 1, 18, 0, 0, tzinfo=UTC)


def test_apply_demand_response_sets_active_flag() -> None:
    grid = GridConstraints(max_site_power_w=50000.0)
    updated = apply_demand_response(
        grid,
        reduction_percent=30.0,
        start=BASE,
        end=BASE + timedelta(hours=2),
    )
    assert updated.demand_response_active is True
    assert updated.demand_response_reduction_percent == 30.0
    assert updated.demand_response_start == BASE
    assert updated.demand_response_end == BASE + timedelta(hours=2)


def test_apply_demand_response_does_not_mutate_original() -> None:
    grid = GridConstraints(max_site_power_w=50000.0)
    apply_demand_response(
        grid, reduction_percent=20.0, start=BASE, end=BASE + timedelta(hours=1)
    )
    assert grid.demand_response_active is False


def test_fleet_respects_demand_response_limit(
    fleet_sessions, fleet_site_config
) -> None:
    from gridmind.optimizer.demand_response import apply_demand_response
    from gridmind.optimizer.fleet import FleetOptimizer

    dr_start = fleet_sessions[0].arrival_time + timedelta(hours=2)
    dr_end = dr_start + timedelta(minutes=90)
    updated_grid = apply_demand_response(
        fleet_site_config.grid,
        reduction_percent=30.0,
        start=dr_start,
        end=dr_end,
    )
    dr_site = fleet_site_config.model_copy(update={"grid": updated_grid})

    opt = FleetOptimizer(interval_minutes=15)
    result = opt.optimize(fleet_sessions, dr_site)
    assert result.demand_response_met
    assert result.all_sessions_feasible
