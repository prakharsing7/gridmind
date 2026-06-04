"""
Fleet (multi-EV) charging optimiser.

Formulation:
    Variables:  P[i,t] = charging power for charger i at interval t (Watts)
    Objective:  minimise sum(price[t] * P[i,t] * dt) over all i, t
    Subject to:
        Per-charger: 0 <= P[i,t] <= p_max[i], SoC bounds, departure target
        Site-level:  sum_i(P[i,t]) <= site_max_power for all t
        DR (if active): sum_i(P[i,t]) <= dr_limit for t in DR window
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging
import time

import numpy as np

try:
    import cvxpy as cp
except ImportError as e:
    raise ImportError("CVXPY required: pip install cvxpy") from e

from ..constants import FALLBACK_SOLVER, MIN_POWER_THRESHOLD_W, SOC_TOLERANCE_PERCENT
from ..exceptions import InfeasibleError, SolverError
from ..models.schedule import EVChargingSchedule, FleetSchedule, SchedulePeriod
from ..models.session import EVSession
from ..models.site import PriceSignal, SiteConfig
from .base import BaseOptimizer

logger = logging.getLogger(__name__)


class FleetOptimizer(BaseOptimizer):
    """
    Jointly optimise charging schedules for all EVs at a site.

    Enforces the shared feeder capacity constraint — total fleet draw
    never exceeds site_max_power at any interval.

    Example:
        >>> optimizer = FleetOptimizer(interval_minutes=15)
        >>> fleet_schedule = optimizer.optimize(sessions, site_config)
    """

    def optimize(  # type: ignore[override]
        self,
        sessions: list[EVSession],
        site_config: SiteConfig,
        horizon_start: datetime | None = None,
        horizon_end: datetime | None = None,
    ) -> FleetSchedule:
        """
        Jointly optimise all EV sessions at a site.

        Args:
            sessions: List of EV sessions to optimise.
            site_config: Site configuration (chargers, grid constraints, price signal).
            horizon_start: Start of optimisation window. Default: earliest arrival.
            horizon_end: End of optimisation window. Default: latest departure.

        Returns:
            FleetSchedule with per-EV schedules and aggregate metrics.

        Raises:
            ValueError: If sessions list is empty or a session references an unknown charger.
            InfeasibleError: If the joint LP is infeasible.
            SolverError: If the solver encounters an unexpected error.
        """
        if not sessions:
            raise ValueError("At least one session required")

        site_charger_ids = {c.charger_id for c in site_config.chargers}
        for s in sessions:
            if s.charger_id not in site_charger_ids:
                raise ValueError(
                    f"Session {s.session_id} references unknown charger '{s.charger_id}'"
                )

        t0 = time.perf_counter()

        if horizon_start is None:
            horizon_start = min(s.arrival_time for s in sessions)
        if horizon_end is None:
            horizon_end = max(s.departure_time for s in sessions)

        intervals = self._discretise_horizon(horizon_start, horizon_end)
        n_t = len(intervals)
        n_ev = len(sessions)
        dt_hours = self.interval_minutes / 60.0

        prices = self._build_price_vector(
            intervals, site_config.price_signal, site_config.flat_rate_price
        )

        P = cp.Variable((n_ev, n_t), name="fleet_power_w", nonneg=True)  # noqa: N806

        # Participation mask: 1 when EV i is connected at interval t
        active = np.zeros((n_ev, n_t), dtype=float)
        for i, session in enumerate(sessions):
            for t_idx, t in enumerate(intervals):
                interval_end = t + timedelta(minutes=self.interval_minutes)
                if t >= session.arrival_time and interval_end <= session.departure_time:
                    active[i, t_idx] = 1.0

        constraints: list = []

        for i, session in enumerate(sessions):
            charger = site_config.get_charger(session.charger_id)
            p_max_w = min(
                session.max_charge_rate_w,
                charger.max_power_w if charger else float("inf"),
            )
            p_min_w = session.min_charge_rate_w

            for t_idx in range(n_t):
                if active[i, t_idx] == 0.0:
                    constraints.append(P[i, t_idx] == 0.0)
                else:
                    constraints.append(P[i, t_idx] <= p_max_w)
                    if p_min_w > 0:
                        constraints.append(P[i, t_idx] >= p_min_w)

            initial_e = self._soc_to_energy_kwh(
                session.initial_soc, session.battery_capacity_kwh
            )
            target_e = self._soc_to_energy_kwh(
                session.target_soc, session.battery_capacity_kwh
            )

            energy_added = P[i, :] * session.charging_efficiency * dt_hours / 1000.0
            soc_energy = initial_e + cp.cumsum(energy_added)

            constraints.append(
                soc_energy * 100.0 / session.battery_capacity_kwh <= 100.0
            )
            constraints.append(
                soc_energy * 100.0 / session.battery_capacity_kwh >= session.min_soc
            )

            last_idx = max(
                (t_idx for t_idx in range(n_t) if active[i, t_idx] == 1.0),
                default=None,
            )
            if last_idx is not None:
                constraints.append(
                    soc_energy[last_idx]
                    >= target_e
                    - SOC_TOLERANCE_PERCENT / 100.0 * session.battery_capacity_kwh
                )

        fleet_power = cp.sum(P, axis=0)
        constraints.append(fleet_power <= site_config.grid.max_site_power_w)

        dr = site_config.grid
        if (
            dr.demand_response_active
            and dr.demand_response_start
            and dr.demand_response_end
        ):
            dr_limit = site_config.grid.max_site_power_w * (
                1.0 - dr.demand_response_reduction_percent / 100.0
            )
            for t_idx, t in enumerate(intervals):
                if dr.demand_response_start <= t < dr.demand_response_end:
                    constraints.append(fleet_power[t_idx] <= dr_limit)

        cost = cp.sum(cp.multiply(prices, cp.sum(P * dt_hours / 1000.0, axis=0)))
        problem = cp.Problem(cp.Minimize(cost), constraints)

        try:
            problem.solve(solver=self.solver, verbose=self.verbose)
        except cp.SolverError:
            logger.warning(
                "Primary solver %s failed, trying %s", self.solver, FALLBACK_SOLVER
            )
            try:
                problem.solve(solver=FALLBACK_SOLVER, verbose=self.verbose)
            except cp.SolverError as e:
                raise SolverError(f"Fleet solver failed: {e}") from e

        if problem.status in [cp.INFEASIBLE, cp.INFEASIBLE_INACCURATE]:
            raise InfeasibleError(
                "Fleet optimisation infeasible. "
                "Check: feeder limit too tight, insufficient session time."
            )

        P_val = np.where(P.value < MIN_POWER_THRESHOLD_W, 0.0, P.value)  # noqa: N806
        ev_schedules = [
            self._build_ev_schedule(
                sessions[i], intervals, P_val[i, :], prices, dt_hours
            )
            for i in range(n_ev)
        ]

        fleet_power_values = np.sum(P_val, axis=0)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        solver_name = (
            str(problem.solver_stats.solver_name) if problem.solver_stats else "unknown"
        )

        return FleetSchedule(
            site_id=site_config.site_id,
            sessions=ev_schedules,
            total_energy_kwh=sum(s.total_energy_kwh for s in ev_schedules),
            total_cost=sum(
                s.total_cost for s in ev_schedules if s.total_cost is not None
            ),
            peak_demand_w=float(np.max(fleet_power_values)),
            avg_demand_w=float(np.mean(fleet_power_values)),
            feeder_limit_respected=bool(
                np.all(fleet_power_values <= site_config.grid.max_site_power_w + 1.0)
            ),
            all_sessions_feasible=all(s.feasible for s in ev_schedules),
            demand_response_met=True,
            optimised_at=datetime.now(UTC),
            optimisation_duration_ms=elapsed_ms,
            solver=solver_name,
            num_variables=len(problem.variables()),
            num_constraints=len(problem.constraints),
        )

    def _build_price_vector(
        self,
        intervals: list[datetime],
        price_signal: PriceSignal | None,
        flat_rate: float,
    ) -> np.ndarray:
        if price_signal is None:
            return np.full(len(intervals), flat_rate)
        return np.array(
            [self._get_price_at(t, price_signal.periods, flat_rate) for t in intervals]
        )

    def _build_ev_schedule(
        self,
        session: EVSession,
        intervals: list[datetime],
        power_values: np.ndarray,
        prices: np.ndarray,
        dt_hours: float,
    ) -> EVChargingSchedule:
        """Build per-EV EVChargingSchedule from the solved power matrix row."""
        dt = timedelta(minutes=self.interval_minutes)
        periods: list[SchedulePeriod] = []

        if intervals:
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

        initial_e = self._soc_to_energy_kwh(
            session.initial_soc, session.battery_capacity_kwh
        )
        total_added = float(
            np.sum(power_values * session.charging_efficiency * dt_hours / 1000.0)
        )
        final_soc = self._energy_to_soc(
            initial_e + total_added, session.battery_capacity_kwh
        )
        total_cost = float(np.sum(power_values / 1000.0 * dt_hours * prices))

        return EVChargingSchedule(
            session_id=session.session_id,
            charger_id=session.charger_id,
            periods=periods,
            total_energy_kwh=total_added,
            final_soc=final_soc,
            total_cost=total_cost,
            target_soc_met=(final_soc >= session.target_soc - SOC_TOLERANCE_PERCENT),
            feasible=True,
            solver_status="optimal",
            optimised_at=datetime.now(UTC),
            optimisation_duration_ms=0.0,
        )
