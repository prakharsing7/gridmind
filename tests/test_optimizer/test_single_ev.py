from datetime import UTC, datetime, timedelta

from gridmind.models.site import PricePeriod
from gridmind.optimizer.base import BaseOptimizer

BASE = datetime(2026, 6, 1, 18, 0, 0, tzinfo=UTC)


class ConcreteOptimizer(BaseOptimizer):
    """Minimal concrete subclass for testing the ABC."""

    def optimize(self, *args, **kwargs):  # type: ignore[override]
        return None


def test_discretise_horizon_count() -> None:
    opt = ConcreteOptimizer(interval_minutes=15)
    intervals = opt._discretise_horizon(BASE, BASE + timedelta(hours=1))
    assert len(intervals) == 4  # 4 x 15-min slots in 1 hour


def test_discretise_horizon_values() -> None:
    opt = ConcreteOptimizer(interval_minutes=30)
    intervals = opt._discretise_horizon(BASE, BASE + timedelta(hours=1))
    assert intervals[0] == BASE
    assert intervals[1] == BASE + timedelta(minutes=30)


def test_get_price_at_in_period() -> None:
    opt = ConcreteOptimizer()
    periods = [PricePeriod(start=BASE, end=BASE + timedelta(hours=5), price=0.35)]
    assert opt._get_price_at(BASE + timedelta(hours=2), periods) == 0.35


def test_get_price_at_falls_back_to_default() -> None:
    opt = ConcreteOptimizer()
    periods = [PricePeriod(start=BASE, end=BASE + timedelta(hours=1), price=0.35)]
    assert (
        opt._get_price_at(BASE + timedelta(hours=3), periods, default_price=0.99)
        == 0.99
    )


def test_soc_energy_conversions() -> None:
    opt = ConcreteOptimizer()
    assert opt._soc_to_energy_kwh(50.0, 60.0) == 30.0
    assert opt._energy_to_soc(30.0, 60.0) == 50.0
