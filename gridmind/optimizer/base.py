"""
Abstract base class for all optimisers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class BaseOptimizer(ABC):
    """
    Abstract base class for all charging schedule optimisers.

    Subclasses must implement `optimize()`.
    Provides shared utilities for time discretisation, price lookup,
    and SoC/energy conversions.
    """

    def __init__(
        self,
        interval_minutes: int = 15,
        solver: str = "CLARABEL",
        verbose: bool = False,
        tolerance: float = 1e-4,
    ) -> None:
        self.interval_minutes = interval_minutes
        self.interval_seconds = interval_minutes * 60
        self.solver = solver
        self.verbose = verbose
        self.tolerance = tolerance
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def optimize(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        """Run optimisation and return schedule(s)."""

    def _discretise_horizon(self, start: datetime, end: datetime) -> list[datetime]:
        """Return list of interval start times from start to end (exclusive)."""
        intervals: list[datetime] = []
        t = start
        delta = timedelta(minutes=self.interval_minutes)
        while t < end:
            intervals.append(t)
            t += delta
        return intervals

    def _get_price_at(
        self,
        t: datetime,
        price_periods: list,  # list[PricePeriod] — avoid circular import
        default_price: float = 0.25,
    ) -> float:
        """Return electricity price at time t; falls back to default_price."""
        for period in price_periods:
            if period.start <= t < period.end:
                return period.price
        return default_price

    def _soc_to_energy_kwh(
        self, soc_percent: float, battery_capacity_kwh: float
    ) -> float:
        """Convert SoC percentage to absolute stored energy (kWh)."""
        return (soc_percent / 100.0) * battery_capacity_kwh

    def _energy_to_soc(self, energy_kwh: float, battery_capacity_kwh: float) -> float:
        """Convert absolute stored energy (kWh) to SoC percentage."""
        return (energy_kwh / battery_capacity_kwh) * 100.0
