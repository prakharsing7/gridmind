"""
Example 3: EV fleet on a shared feeder.

5 EVs, 50 kW feeder limit, flat-rate electricity.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from gridmind import (
    ChargerConfig,
    EVSession,
    FleetOptimizer,
    GridConstraints,
    SiteConfig,
    build_set_charging_profile_request,
)

BASE = datetime(2026, 6, 1, 17, 0, tzinfo=UTC)

chargers = [
    ChargerConfig(charger_id=f"CHARGER-0{i}", max_power_w=7360.0) for i in range(1, 6)
]
site = SiteConfig(
    site_id="demo-fleet",
    chargers=chargers,
    grid=GridConstraints(max_site_power_w=50000.0),
    flat_rate_price=0.25,
)

sessions = [
    EVSession(
        session_id=f"s00{i}",
        charger_id=f"CHARGER-0{i}",
        arrival_time=BASE + timedelta(hours=i),
        departure_time=BASE + timedelta(hours=14),
        initial_soc=20.0 + i * 5,
        target_soc=80.0,
        battery_capacity_kwh=60.0,
        max_charge_rate_w=7360.0,
    )
    for i in range(1, 6)
]

optimizer = FleetOptimizer(interval_minutes=15)
fleet_schedule = optimizer.optimize(sessions, site)

print(f"Fleet optimised: {len(fleet_schedule.sessions)} EVs")
print(f"Total cost: {fleet_schedule.total_cost:.2f} EUR")
print(f"Peak demand: {fleet_schedule.peak_demand_w / 1000:.1f} kW")
print(f"Feeder limit respected: {fleet_schedule.feeder_limit_respected}")

for sched in fleet_schedule.sessions:
    req = build_set_charging_profile_request(sched)
    print(
        f"\n{sched.charger_id}: {sched.total_cost:.2f} EUR, {sched.final_soc:.0f}% SoC"
    )
