import json
from pathlib import Path

import pytest

from gridmind.inputs.json_loader import load_config
from gridmind.inputs.synthetic import generate_example_config
from gridmind.models.session import EVSession
from gridmind.models.site import SiteConfig


def test_load_single_ev_config(tmp_path: Path) -> None:
    config_data = generate_example_config("single-ev")
    config_file = tmp_path / "single_ev.json"
    config_file.write_text(json.dumps(config_data))

    result = load_config(config_file)
    assert result["type"] == "single_ev"
    assert isinstance(result["session"], EVSession)


def test_load_fleet_config(tmp_path: Path) -> None:
    config_data = generate_example_config("fleet")
    config_file = tmp_path / "fleet.json"
    config_file.write_text(json.dumps(config_data))

    result = load_config(config_file)
    assert result["type"] == "fleet"
    assert isinstance(result["site_config"], SiteConfig)
    assert all(isinstance(s, EVSession) for s in result["sessions"])


def test_load_config_price_signal_parsed(tmp_path: Path) -> None:
    config_data = generate_example_config("single-ev")
    config_file = tmp_path / "single_ev.json"
    config_file.write_text(json.dumps(config_data))

    result = load_config(config_file)
    assert result.get("price_signal") is not None


def test_load_config_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "nonexistent.json")


def test_load_config_unknown_type_raises(tmp_path: Path) -> None:
    config_file = tmp_path / "bad.json"
    config_file.write_text(json.dumps({"type": "unknown"}))
    with pytest.raises(ValueError, match="Unknown config type"):
        load_config(config_file)
