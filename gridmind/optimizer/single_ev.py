"""
Single EV charging optimiser.

Formulation:
    Variables:  p[t] = charging power at interval t (Watts)
    Objective:  minimise sum(price[t] * p[t] * interval_hours) for all t
    Subject to:
        - power bounds: 0 <= p[t] <= p_max for all t
        - SoC bounds:   soc_min <= soc[t] <= 100 for all t
        - departure:    soc[T] >= target_soc
        - continuity:   soc[t+1] = soc[t] + p[t] * eff * dt / capacity

This is a convex LP (linear objective, linear constraints).
Solved using CVXPY with CLARABEL (default) or ECOS (fallback).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging
import time

import numpy as np

try:
    import cvxpy as cp
except ImportError as e:
    raise ImportError("CVXPY is required: pip install cvxpy") from e

from ..constants import (
    FALLBACK_SOLVER,
    MIN_POWER_THRESHOLD_W,
    SOC_TOLERANCE_PERCENT,
)
from ..exceptions import InfeasibleError, SolverError
from ..models.schedule import EVChargingSchedule, SchedulePeriod
from ..models.session import EVSession
from ..models.site import PriceSignal
from .base import BaseOptimizer

logger = logging.getLogger(__name__)


class SingleEVOptimizer(BaseOptimizer):
    """
    Optimise charging schedule for a single EV session.

    Uses convex optimisation (LP via CVXPY) to minimise charging cost
    while satisfying SoC constraints and charger power limits.

    Example:
        >>> from gridmind import SingleEVOptimizer, EVSession
        >>> from datetime import datetime, timezone
        >>> session = EVSession(
        ...     session_id="s001", charger_id="c001",
        ...     arrival_time=datetime(2026, 6, 1, 18, 0, tzinfo=timezone.utc),
        ...     departure_time=datetime(2026, 6, 2, 8, 0, tzinfo=timezone.utc),
        ...     initial_soc=30.0, target_soc=80.0,
        ...     battery_capacity_kwh=60.0, max_charge_rate_w=7400.0,
        ... )
        >>> optimizer = SingleEVOptimizer(interval_minutes=15)
        >>> schedule = optimizer.optimize(session)
        >>> print(f"Total cost: {schedule.total_cost:.2f} EUR")
    """

    def optimize(  # type: ignore[override]
        self,
        session: EVSession,
        price_signal: PriceSignal | None = None,
        flat_rate: float = 0.25,
        external_power_limit_w: float | None = None,
    ) -> EVChargingSchedule:
        """
        Compute optimal charging schedule for one EV session.

        Args:
            session: EV session parameters.
            price_signal: Time-varying price. If None, uses flat_rate.
            flat_rate: Electricity price (EUR/kWh) if no price_signal.
            external_power_limit_w: Additional power cap from site constraints.

        Returns:
            EVChargingSchedule with optimal per-interval power values.

        Raises:
            InfeasibleError: If no feasible schedule exists.
            SolverError: If the solver fails unexpectedly.
        """
        t0 = time.perf_counter()

        intervals = self._discretise_horizon(
            session.arrival_time, session.departure_time
        )
        n = len(intervals)
        if n == 0:
            raise InfeasibleError(
                f"Session {session.session_id}: zero time intervals in horizon"
            )

        dt_hours = self.interval_minutes / 60.0
        prices = self._build_price_vector(intervals, price_signal, flat_rate)

        p_max_w = session.max_charge_rate_w
        if external_power_limit_w is not None:
            p_max_w = min(p_max_w, external_power_limit_w)
        p_min_w = session.min_charge_rate_w

        p = cp.Variable(n, name="power_w", nonneg=True)
        energy_added_kwh = p * session.charging_efficiency * dt_hours / 1000.0

        initial_energy_kwh = self._soc_to_energy_kwh(
            session.initial_soc, session.battery_capacity_kwh
        )
        cumulative_energy = cp.cumsum(energy_added_kwh)
        soc_energy_kwh = initial_energy_kwh + cumulative_energy
        soc_pct = soc_energy_kwh / session.battery_capacity_kwh * 100.0

        objective = cp.Minimize(cp.sum(cp.multiply(prices, energy_added_kwh)))
        constraints = [
            p >= p_min_w,
            p <= p_max_w,
            soc_pct >= session.min_soc,
            soc_pct <= 100.0,
            soc_pct[-1] >= session.target_soc - SOC_TOLERANCE_PERCENT,
        ]

        problem = cp.Problem(objective, constraints)
        try:
            problem.solve(solver=self.solver, verbose=self.verbose)
        except cp.SolverError:
            logger.warning(
                "Primary solver %s failed, trying %s", self.solver, FALLBACK_SOLVER
            )
            try:
                problem.solve(solver=FALLBACK_SOLVER, verbose=self.verbose)
            except cp.SolverError as e:
                raise SolverError(
                    f"Both solvers failed for session {session.session_id}: {e}"
                ) from e

        if problem.status in [cp.INFEASIBLE, cp.INFEASIBLE_INACCURATE]:
            raise InfeasibleError(
                f"No feasible schedule for session {session.session_id}. "
                f"Solver status: {problem.status}"
            )
        if problem.status not in [cp.OPTIMAL, cp.OPTIMAL_INACCURATE]:
            raise SolverError(f"Unexpected solver status: {problem.status}")

        power_values = np.where(p.value < MIN_POWER_THRESHOLD_W, 0.0, p.value)
        schedule_periods = self._build_schedule_periods(intervals, power_values, prices)

        total_added = float(
            np.sum(power_values * session.charging_efficiency * dt_hours / 1000.0)
        )
        final_soc = self._energy_to_soc(
            initial_energy_kwh + total_added, session.battery_capacity_kwh
        )
        total_cost = float(np.sum(power_values / 1000.0 * dt_hours * prices))
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        return EVChargingSchedule(
            session_id=session.session_id,
            charger_id=session.charger_id,
            periods=schedule_periods,
            total_energy_kwh=total_added,
            final_soc=final_soc,
            total_cost=total_cost,
            target_soc_met=(final_soc >= session.target_soc - SOC_TOLERANCE_PERCENT),
            feasible=True,
            solver_status=str(problem.status),
            optimised_at=datetime.now(UTC),
            optimisation_duration_ms=elapsed_ms,
        )

    def _build_price_vector(
        self,
        intervals: list[datetime],
        price_signal: PriceSignal | None,
        flat_rate: float,
    ) -> np.ndarray:
        """Build EUR/kWh array for each interval."""
        if price_signal is None:
            return np.full(len(intervals), flat_rate)
        return np.array(
            [self._get_price_at(t, price_signal.periods, flat_rate) for t in intervals]
        )

    def _build_schedule_periods(
        self,
        intervals: list[datetime],
        power_values: np.ndarray,
        prices: np.ndarray,
    ) -> list[SchedulePeriod]:
        """
        Convert per-interval power array to SchedulePeriod list.
        Consecutive intervals with the same power level are merged.
        """
        if not intervals:
            return []

        dt = timedelta(minutes=self.interval_minutes)
        periods: list[SchedulePeriod] = []
        current_start = intervals[0]
        current_power = power_values[0]
        current_price = prices[0]

        for i in range(1, len(intervals)):
            if abs(power_values[i] - current_power) > MIN_POWER_THRESHOLD_W:
                periods.append(
                    SchedulePeriod(
                        start=current_start,
                        end=intervals[i],
                        power_w=float(current_power),
                        price_per_kwh=float(current_price),
                    )
                )
                current_start = intervals[i]
                current_power = power_values[i]
                current_price = prices[i]

        periods.append(
            SchedulePeriod(
                start=current_start,
                end=intervals[-1] + dt,
                power_w=float(current_power),
                price_per_kwh=float(current_price),
            )
        )
        return periods
