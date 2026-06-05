"""Tests for visualisation modules using the non-interactive Agg backend."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # must be set before any other matplotlib import

from datetime import UTC, datetime, timedelta

from gridmind.models.schedule import EVChargingSchedule, FleetSchedule, SchedulePeriod

BASE = datetime(2026, 6, 1, 18, 0, 0, tzinfo=UTC)


def _single_session(power_w: float = 7360.0) -> EVChargingSchedule:
    return EVChargingSchedule(
        session_id="s001",
        charger_id="c001",
        periods=[
            SchedulePeriod(
                start=BASE,
                end=BASE + timedelta(hours=5),
                power_w=power_w,
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


def _fleet_schedule() -> FleetSchedule:
    ev = _single_session()
    return FleetSchedule(
        site_id="site-001",
        sessions=[ev],
        total_energy_kwh=36.8,
        total_cost=9.2,
        peak_demand_w=7360.0,
        avg_demand_w=5000.0,
        feeder_limit_respected=True,
        all_sessions_feasible=True,
        demand_response_met=True,
        optimised_at=BASE,
        optimisation_duration_ms=100.0,
        solver="CLARABEL",
        num_variables=56,
        num_constraints=114,
    )


def test_plot_fleet_schedule_returns_figure() -> None:
    import matplotlib.pyplot as plt

    from gridmind.viz.schedule_plot import plot_fleet_schedule

    fig = plot_fleet_schedule([_single_session()])
    assert isinstance(fig, plt.Figure)
    plt.close("all")


def test_plot_fleet_schedule_with_fleet_schedule() -> None:
    import matplotlib.pyplot as plt

    from gridmind.viz.schedule_plot import plot_fleet_schedule

    fig = plot_fleet_schedule([_single_session()], fleet_schedule=_fleet_schedule())
    assert isinstance(fig, plt.Figure)
    plt.close("all")


def test_plot_fleet_schedule_empty_sessions() -> None:
    import matplotlib.pyplot as plt

    from gridmind.viz.schedule_plot import plot_fleet_schedule

    fig = plot_fleet_schedule([])
    assert isinstance(fig, plt.Figure)
    plt.close("all")


def test_plot_single_schedule_returns_figure() -> None:
    import matplotlib.pyplot as plt

    from gridmind.viz.schedule_plot import plot_single_schedule

    fig = plot_single_schedule(_single_session())
    assert isinstance(fig, plt.Figure)
    plt.close("all")


def test_plot_soc_curves_returns_figure() -> None:
    import matplotlib.pyplot as plt

    from gridmind.viz.soc_plot import plot_soc_curves

    fig = plot_soc_curves([_single_session()])
    assert isinstance(fig, plt.Figure)
    plt.close("all")


def test_plot_soc_curves_with_capacities() -> None:
    import matplotlib.pyplot as plt

    from gridmind.viz.soc_plot import plot_soc_curves

    fig = plot_soc_curves([_single_session()], battery_capacities_kwh=[60.0])
    assert isinstance(fig, plt.Figure)
    plt.close("all")


def test_plot_soc_curves_empty_sessions() -> None:
    import matplotlib.pyplot as plt

    from gridmind.viz.soc_plot import plot_soc_curves

    fig = plot_soc_curves([])
    assert isinstance(fig, plt.Figure)
    plt.close("all")


def test_plot_cost_breakdown_returns_figure() -> None:
    import matplotlib.pyplot as plt

    from gridmind.viz.cost_plot import plot_cost_breakdown

    fig = plot_cost_breakdown([_single_session()])
    assert isinstance(fig, plt.Figure)
    plt.close("all")


def test_plot_strategy_comparison_returns_figure() -> None:
    import matplotlib.pyplot as plt

    from gridmind.viz.comparison_plot import plot_strategy_comparison

    opt = _single_session(power_w=3680.0)
    unc = _single_session(power_w=7360.0)
    fig = plot_strategy_comparison(opt, unc)
    assert isinstance(fig, plt.Figure)
    plt.close("all")
