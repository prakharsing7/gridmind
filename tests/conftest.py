"""Shared fixtures for all tests."""

from datetime import UTC, datetime, timedelta

import pytest

from gridmind.models.session import ChargerConfig, EVSession
from gridmind.models.site import GridConstraints, PricePeriod, PriceSignal, SiteConfig


@pytest.fixture
def base_time() -> datetime:
    """Base UTC time used consistently across all tests."""
    return datetime(2026, 6, 1, 18, 0, 0, tzinfo=UTC)


@pytest.fixture
def single_session(base_time: datetime) -> EVSession:
    """Single EV session: 30% → 80%, 7.4 kW charger, 14-hour window."""
    return EVSession(
        session_id="test-session-001",
        charger_id="charger-001",
        arrival_time=base_time,
        departure_time=base_time + timedelta(hours=14),
        initial_soc=30.0,
        target_soc=80.0,
        battery_capacity_kwh=60.0,
        max_charge_rate_w=7360.0,
    )


@pytest.fixture
def charger_config() -> ChargerConfig:
    return ChargerConfig(charger_id="charger-001", max_power_w=7360.0)


@pytest.fixture
def site_config(charger_config: ChargerConfig) -> SiteConfig:
    return SiteConfig(
        site_id="test-site-001",
        chargers=[charger_config],
        grid=GridConstraints(max_site_power_w=22000.0),
        flat_rate_price=0.25,
    )


@pytest.fixture
def tou_price_signal(base_time: datetime) -> PriceSignal:
    """TOU price signal: peak 6 pm-11 pm (0.35), cheap 11 pm-8 am (0.10)."""
    peak_start = base_time
    peak_end = base_time.replace(hour=23, minute=0, second=0)
    cheap_start = peak_end
    cheap_end = base_time + timedelta(hours=14)
    return PriceSignal(
        periods=[
            PricePeriod(start=peak_start, end=peak_end, price=0.35),
            PricePeriod(start=cheap_start, end=cheap_end, price=0.10),
        ],
        currency="EUR",
    )


@pytest.fixture
def fleet_sessions(base_time: datetime) -> list[EVSession]:
    """Fleet of 3 EVs with varied arrival/departure times and battery sizes."""
    configs = [
        ("ev-001", "charger-001", 0, 14, 20.0, 80.0, 60.0, 7360.0),
        ("ev-002", "charger-002", 2, 12, 50.0, 90.0, 77.0, 7360.0),
        ("ev-003", "charger-003", 1, 10, 10.0, 70.0, 40.0, 7360.0),
    ]
    sessions = []
    for sid, cid, arr_h, dep_h, isoc, tsoc, cap, pmax in configs:
        sessions.append(
            EVSession(
                session_id=sid,
                charger_id=cid,
                arrival_time=base_time + timedelta(hours=arr_h),
                departure_time=base_time + timedelta(hours=dep_h),
                initial_soc=isoc,
                target_soc=tsoc,
                battery_capacity_kwh=cap,
                max_charge_rate_w=pmax,
            )
        )
    return sessions


@pytest.fixture
def fleet_site_config(base_time: datetime) -> SiteConfig:
    """Site config for 3-EV fleet tests."""
    chargers = [
        ChargerConfig(charger_id="charger-001", max_power_w=7360.0),
        ChargerConfig(charger_id="charger-002", max_power_w=7360.0),
        ChargerConfig(charger_id="charger-003", max_power_w=7360.0),
    ]
    return SiteConfig(
        site_id="test-fleet-site",
        chargers=chargers,
        grid=GridConstraints(max_site_power_w=22000.0),
        flat_rate_price=0.25,
    )
