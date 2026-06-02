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
