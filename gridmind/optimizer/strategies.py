"""
Baseline charging strategies for comparison.
These are NOT optimised — they represent simple reference behaviours.

Used in strategy comparison to show how much the optimiser saves vs.
naive alternatives.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import math

from ..models.schedule import EVChargingSchedule, SchedulePeriod
from ..models.session import EVSession
from ..models.site import PriceSignal, SiteConfig


def uncontrolled_strategy(
    session: EVSession,
    site_config: SiteConfig | None = None,
    flat_rate: float = 0.25,
    price_signal: PriceSignal | None = None,
    interval_minutes: int = 15,
) -> EVChargingSchedule:
    """
    Uncontrolled charging: charge at full power immediately on connection.

    Reference baseline representing 'plug in and charge at max' behaviour —
    what most deployed chargers do today without smart charging enabled.
    """
    dt = timedelta(minutes=interval_minutes)
    dt_hours = interval_minutes / 60.0
    p_max = session.max_charge_rate_w
    eff = session.charging_efficiency
    cap = session.battery_capacity_kwh

    energy_needed = session.energy_needed_kwh
    energy_per_interval = p_max * eff * dt_hours / 1000.0
    intervals_needed = (
        math.ceil(energy_needed / energy_per_interval) if energy_per_interval > 0 else 0
    )

    periods: list[SchedulePeriod] = []
    total_energy = 0.0
    total_cost = 0.0

    t = session.arrival_time
    idx = 0
    while t < session.departure_time:
        p = p_max if idx < intervals_needed else 0.0
        energy_kwh = p * eff * dt_hours / 1000.0

        price = flat_rate
        if price_signal:
            for period in price_signal.periods:
                if period.start <= t < period.end:
                    price = period.price
                    break

        periods.append(
            SchedulePeriod(start=t, end=t + dt, power_w=p, price_per_kwh=price)
        )
        total_energy += energy_kwh
        total_cost += energy_kwh * price
        t += dt
        idx += 1

    initial_energy = (session.initial_soc / 100.0) * cap
    final_soc = min(((initial_energy + total_energy) / cap) * 100.0, 100.0)

    return EVChargingSchedule(
        session_id=session.session_id,
        charger_id=session.charger_id,
        periods=periods,
        total_energy_kwh=total_energy,
        final_soc=final_soc,
        total_cost=total_cost,
        target_soc_met=(final_soc >= session.target_soc - 0.5),
        feasible=True,
        solver_status="UNCONTROLLED_BASELINE",
        optimised_at=datetime.now(UTC),
        optimisation_duration_ms=0.0,
    )
