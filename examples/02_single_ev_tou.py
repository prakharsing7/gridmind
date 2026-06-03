"""
Example 2: Single EV, time-of-use pricing.

Shows how the optimiser shifts charging to the cheap-rate window.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from gridmind import (
    EVSession,
    PricePeriod,
    PriceSignal,
    SingleEVOptimizer,
    uncontrolled_strategy,
)

BASE = datetime(2026, 6, 1, 18, 0, tzinfo=UTC)

session = EVSession(
    session_id="tou-example",
    charger_id="charger-001",
    arrival_time=BASE,
    departure_time=BASE + timedelta(hours=14),
    initial_soc=30.0,
    target_soc=80.0,
    battery_capacity_kwh=60.0,
    max_charge_rate_w=7360.0,
)

price_signal = PriceSignal(
    periods=[
        PricePeriod(start=BASE, end=BASE.replace(hour=23), price=0.35),
        PricePeriod(
            start=BASE.replace(hour=23),
            end=BASE + timedelta(hours=14),
            price=0.10,
        ),
    ]
)

optimizer = SingleEVOptimizer(interval_minutes=15)
optimised = optimizer.optimize(session, price_signal=price_signal)
uncontrolled = uncontrolled_strategy(session, price_signal=price_signal)

print(f"Optimised cost:    {optimised.total_cost:.2f} EUR")
print(f"Uncontrolled cost: {uncontrolled.total_cost:.2f} EUR")
saving = uncontrolled.total_cost - optimised.total_cost
print(f"Saving: {saving:.2f} EUR ({saving / uncontrolled.total_cost * 100:.1f}%)")
