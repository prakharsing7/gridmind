import json
from pathlib import Path

from click.testing import CliRunner

from gridmind.cli.main import cli
from gridmind.inputs.synthetic import generate_example_config


def test_cli_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "gridmind" in result.output


def test_cli_validate_valid_config(tmp_path: Path) -> None:
    config = generate_example_config("single-ev")
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config))

    runner = CliRunner()
    result = runner.invoke(cli, ["validate", "--config", str(config_file)])
    assert result.exit_code == 0
    assert "valid" in result.output.lower()


def test_cli_validate_invalid_config_exits_1(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad.json"
    bad_file.write_text(json.dumps({"type": "garbage"}))

    runner = CliRunner()
    result = runner.invoke(cli, ["validate", "--config", str(bad_file)])
    assert result.exit_code == 1


def test_cli_generate_config_single_ev(tmp_path: Path) -> None:
    output_file = tmp_path / "out.json"
    runner = CliRunner()
    result = runner.invoke(
        cli, ["generate-config", "--type", "single-ev", "--output", str(output_file)]
    )
    assert result.exit_code == 0
    data = json.loads(output_file.read_text())
    assert data["type"] == "single_ev"


def test_cli_run_single_ev_produces_ocpp_output(tmp_path: Path) -> None:
    config = generate_example_config("single-ev")
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config))

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "--config",
            str(config_file),
            "--output",
            str(tmp_path),
            "--interval",
            "30",
        ],
    )
    assert result.exit_code == 0, f"CLI failed: {result.output}"
    profile_files = list(tmp_path.glob("charging_profile_*.json"))
    assert len(profile_files) == 1
    data = json.loads(profile_files[0].read_text())
    assert "connectorId" in data
    assert "csChargingProfiles" in data


def test_cli_run_fleet_produces_profiles(tmp_path: Path) -> None:
    config = generate_example_config("fleet")
    config_file = tmp_path / "fleet.json"
    config_file.write_text(json.dumps(config))

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "--config",
            str(config_file),
            "--output",
            str(tmp_path),
            "--interval",
            "30",
        ],
    )
    assert result.exit_code == 0, f"CLI failed: {result.output}"
    profiles_dir = tmp_path / "ocpp_profiles"
    assert profiles_dir.exists()
    assert len(list(profiles_dir.glob("*.json"))) >= 3
