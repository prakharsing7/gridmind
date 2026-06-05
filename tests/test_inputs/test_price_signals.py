from datetime import UTC, datetime, timedelta

import pytest

from gridmind.inputs.price_signals import build_flat_signal, build_tou_signal
from gridmind.inputs.synthetic import generate_example_config

BASE = datetime(2026, 6, 1, 18, 0, 0, tzinfo=UTC)


def test_build_flat_signal() -> None:
    signal = build_flat_signal(price=0.25, start=BASE, end=BASE + timedelta(hours=14))
    assert len(signal.periods) == 1
    assert signal.periods[0].price == 0.25


def test_build_tou_signal() -> None:
    signal = build_tou_signal(
        peak_price=0.35,
        cheap_price=0.10,
        peak_start_hour=18,
        peak_end_hour=23,
        start=BASE,
        end=BASE + timedelta(hours=14),
    )
    assert len(signal.periods) == 2
    peak = next(p for p in signal.periods if p.price == 0.35)
    cheap = next(p for p in signal.periods if p.price == 0.10)
    assert peak.start.hour == 18
    assert cheap.start.hour == 23


def test_generate_example_config_single_ev() -> None:
    config = generate_example_config("single-ev")
    assert config["type"] == "single_ev"
    assert "session" in config
    assert "session_id" in config["session"]


def test_generate_example_config_fleet() -> None:
    config = generate_example_config("fleet")
    assert config["type"] == "fleet"
    assert "sessions" in config
    assert "site_config" in config
    assert len(config["sessions"]) >= 3


def test_generate_example_config_unknown_type_raises() -> None:
    with pytest.raises(ValueError, match="Unknown config type"):
        generate_example_config("unknown-type")


def test_build_tou_signal_peak_wraps_midnight() -> None:
    """When peak_end <= peak_start, peak_end is advanced by 1 day."""
    from datetime import timedelta

    # peak_start=22, peak_end=2 → wraps midnight
    signal = build_tou_signal(
        peak_price=0.40,
        cheap_price=0.10,
        peak_start_hour=22,
        peak_end_hour=2,
        start=BASE,
        end=BASE + timedelta(hours=20),
    )
    assert any(p.price == 0.40 for p in signal.periods)


def test_build_tou_signal_no_leading_cheap_period() -> None:
    """When peak_start == start, no leading cheap period is inserted."""
    # peak_start_hour = 18 == BASE.hour, so peak_start == start
    signal = build_tou_signal(
        peak_price=0.40,
        cheap_price=0.10,
        peak_start_hour=18,
        peak_end_hour=23,
        start=BASE,
        end=BASE + timedelta(hours=14),
    )
    # first period should be peak (no leading cheap)
    assert signal.periods[0].price == 0.40


def test_build_tou_signal_no_trailing_cheap_period() -> None:
    """When peak_end >= end, no trailing cheap period is added."""

    # peak covers the full range up to end
    signal = build_tou_signal(
        peak_price=0.40,
        cheap_price=0.10,
        peak_start_hour=18,
        peak_end_hour=23,
        start=BASE,
        end=BASE.replace(hour=23),  # end == peak_end
    )
    assert all(p.price == 0.40 for p in signal.periods)


def test_evsession_target_soc_already_met() -> None:
    """When initial_soc >= target_soc, energy_needed <= 0 → validator returns self."""
    from datetime import timedelta

    from gridmind.models.session import EVSession

    session = EVSession(
        session_id="s-happy",
        charger_id="c001",
        arrival_time=BASE,
        departure_time=BASE + timedelta(hours=14),
        initial_soc=80.0,
        target_soc=70.0,  # already exceeded
        battery_capacity_kwh=60.0,
        max_charge_rate_w=7360.0,
    )
    # Should not raise — validator returns self when energy_needed_kwh <= 0
    assert session.target_soc == 70.0
