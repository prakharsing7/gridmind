"""
Example 1: Single EV, flat-rate electricity.

Demonstrates the simplest use case: one EV, no time-varying price.
"""

from __future__ import annotations

from datetime import UTC, datetime

from gridmind import (
    EVSession,
    SingleEVOptimizer,
    build_set_charging_profile_request,
    to_json,
)

session = EVSession(
    session_id="example-001",
    charger_id="charger-001",
    arrival_time=datetime(2026, 6, 1, 18, 0, tzinfo=UTC),
    departure_time=datetime(2026, 6, 2, 8, 0, tzinfo=UTC),
    initial_soc=30.0,
    target_soc=80.0,
    battery_capacity_kwh=60.0,
    max_charge_rate_w=7360.0,
)

optimizer = SingleEVOptimizer(interval_minutes=15)
schedule = optimizer.optimize(session, flat_rate=0.25)

print(f"Session: {session.session_id}")
print(f"Optimised cost: {schedule.total_cost:.2f} EUR")
print(f"Final SoC: {schedule.final_soc:.1f}%")
print(f"Schedule periods: {len(schedule.periods)}")

ocpp_req = build_set_charging_profile_request(schedule)
print("\nOCPP SetChargingProfile.req:")
print(to_json(ocpp_req))
