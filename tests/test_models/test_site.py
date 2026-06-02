from datetime import UTC, datetime, timedelta

import pytest

from gridmind.constants import (
    DEFAULT_FLAT_RATE_EUR_KWH,
    DEFAULT_FREQUENCY_HZ,
    DEFAULT_VOLTAGE_V,
)
from gridmind.models.session import ChargerConfig
from gridmind.models.site import GridConstraints, PricePeriod, PriceSignal, SiteConfig

BASE = datetime(2026, 6, 1, 18, 0, 0, tzinfo=UTC)


def test_grid_constraints_defaults() -> None:
    g = GridConstraints(max_site_power_w=50000.0)
    assert g.demand_response_active is False
    assert g.voltage_v == DEFAULT_VOLTAGE_V
    assert g.frequency_hz == DEFAULT_FREQUENCY_HZ
    assert g.demand_response_reduction_percent == 0.0


def test_grid_constraints_zero_power_raises() -> None:
    with pytest.raises(ValueError):
        GridConstraints(max_site_power_w=0.0)


def test_price_period_end_before_start_raises() -> None:
    with pytest.raises(ValueError, match="end must be after start"):
        PricePeriod(start=BASE, end=BASE - timedelta(hours=1), price=0.25)


def test_price_signal_valid() -> None:
    ps = PriceSignal(
        periods=[
            PricePeriod(start=BASE, end=BASE + timedelta(hours=5), price=0.35),
            PricePeriod(
                start=BASE + timedelta(hours=5),
                end=BASE + timedelta(hours=12),
                price=0.10,
            ),
        ],
        currency="EUR",
    )
    assert len(ps.periods) == 2
    assert ps.unit == "EUR/kWh"


def test_price_signal_empty_raises() -> None:
    with pytest.raises(ValueError):
        PriceSignal(periods=[])


def test_site_config_valid() -> None:
    site = SiteConfig(
        site_id="site-001",
        chargers=[ChargerConfig(charger_id="C1", max_power_w=7360.0)],
        grid=GridConstraints(max_site_power_w=22000.0),
    )
    assert site.num_chargers == 1
    assert site.flat_rate_price == DEFAULT_FLAT_RATE_EUR_KWH


def test_site_config_duplicate_charger_ids_raises() -> None:
    with pytest.raises(ValueError, match="unique"):
        SiteConfig(
            site_id="site-001",
            chargers=[
                ChargerConfig(charger_id="C1", max_power_w=7360.0),
                ChargerConfig(charger_id="C1", max_power_w=7360.0),
            ],
            grid=GridConstraints(max_site_power_w=22000.0),
        )


def test_site_config_get_charger() -> None:
    site = SiteConfig(
        site_id="site-001",
        chargers=[ChargerConfig(charger_id="C1", max_power_w=7360.0)],
        grid=GridConstraints(max_site_power_w=22000.0),
    )
    assert site.get_charger("C1") is not None
    assert site.get_charger("MISSING") is None
