from datetime import UTC, datetime, timedelta

from gridmind.models.schedule import EVChargingSchedule, FleetSchedule, SchedulePeriod

BASE = datetime(2026, 6, 1, 18, 0, 0, tzinfo=UTC)


def test_schedule_period_duration() -> None:
    p = SchedulePeriod(
        start=BASE,
        end=BASE + timedelta(hours=1),
        power_w=7360.0,
        price_per_kwh=0.25,
    )
    assert p.duration_hours == 1.0


def test_schedule_period_energy_kwh() -> None:
    p = SchedulePeriod(
        start=BASE,
        end=BASE + timedelta(hours=2),
        power_w=7000.0,
    )
    # 7000 W * 2 h / 1000 = 14 kWh
    assert abs(p.energy_kwh - 14.0) < 0.01


def test_schedule_period_cost() -> None:
    p = SchedulePeriod(
        start=BASE,
        end=BASE + timedelta(hours=1),
        power_w=7000.0,
        price_per_kwh=0.25,
    )
    # 7 kWh * 0.25 = 1.75 EUR
    assert abs(p.cost - 1.75) < 0.01


def test_schedule_period_cost_none_when_no_price() -> None:
    p = SchedulePeriod(start=BASE, end=BASE + timedelta(hours=1), power_w=7000.0)
    assert p.cost is None


def test_ev_charging_schedule_fields() -> None:
    p = SchedulePeriod(start=BASE, end=BASE + timedelta(hours=1), power_w=7360.0)
    s = EVChargingSchedule(
        session_id="s001",
        charger_id="c001",
        periods=[p],
        total_energy_kwh=7.36,
        final_soc=80.0,
        total_cost=1.84,
        target_soc_met=True,
        feasible=True,
        solver_status="optimal",
        optimised_at=BASE,
        optimisation_duration_ms=42.0,
    )
    assert s.feasible is True
    assert s.solver_status == "optimal"


def test_fleet_schedule_fields() -> None:
    p = SchedulePeriod(start=BASE, end=BASE + timedelta(hours=1), power_w=7360.0)
    ev = EVChargingSchedule(
        session_id="s001",
        charger_id="c001",
        periods=[p],
        total_energy_kwh=7.36,
        final_soc=80.0,
        total_cost=1.84,
        target_soc_met=True,
        feasible=True,
        solver_status="optimal",
        optimised_at=BASE,
        optimisation_duration_ms=42.0,
    )
    fs = FleetSchedule(
        site_id="site-001",
        sessions=[ev],
        total_energy_kwh=7.36,
        total_cost=1.84,
        peak_demand_w=7360.0,
        avg_demand_w=7360.0,
        feeder_limit_respected=True,
        all_sessions_feasible=True,
        demand_response_met=True,
        optimised_at=BASE,
        optimisation_duration_ms=100.0,
        solver="CLARABEL",
        num_variables=56,
        num_constraints=114,
    )
    assert fs.all_sessions_feasible is True
