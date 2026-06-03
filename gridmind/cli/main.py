"""
Command-line interface for gridmind.

Usage:
    gridmind run --config examples/configs/single_ev.json
    gridmind run --config fleet.json --output results/ --plot
    gridmind compare --config fleet.json
    gridmind generate-config --type single-ev --output my_session.json
    gridmind validate --config my_session.json
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
import sys
from typing import Any

import click


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.version_option()
def cli(verbose: bool) -> None:
    """gridmind: Optimise EV charging schedules, output OCPP profiles."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )


@cli.command()
@click.option(
    "--config", "-c", required=True, type=click.Path(exists=True, readable=True)
)
@click.option("--output", "-o", default=".", type=click.Path())
@click.option("--plot", is_flag=True, help="Generate visualisation plots")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "csv", "both"]),
    default="json",
)
@click.option(
    "--ocpp-version",
    type=click.Choice(["1.6", "2.0.1"]),
    default="1.6",
)
@click.option(
    "--interval", default=15, type=int, help="Optimisation interval in minutes"
)
def run(
    config: str,
    output: str,
    plot: bool,
    output_format: str,
    ocpp_version: str,
    interval: int,
) -> None:
    """Run optimisation from a config file.

    \b
    Examples:
        gridmind run --config examples/configs/single_ev.json
        gridmind run --config fleet.json --output results/ --plot --format both
    """
    from ..inputs.json_loader import load_config
    from ..optimizer.fleet import FleetOptimizer
    from ..optimizer.single_ev import SingleEVOptimizer
    from ..outputs.csv_writer import write_schedule_csv
    from ..outputs.json_writer import write_fleet_results

    if ocpp_version == "2.0.1":
        from ..ocpp.v201.charging_profile import (
            build_set_charging_profile_request,
            to_json,
        )

        to_ocpp_message = None
    else:
        from ..ocpp.v16.charging_profile import (  # type: ignore[assignment]
            build_set_charging_profile_request,
            to_json,
            to_ocpp_message,
        )

    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    click.echo(f"Loading config from {config}...")
    config_data = load_config(Path(config))

    click.echo(f"Optimising with {interval}-minute intervals (OCPP {ocpp_version})...")

    optimizer: Any
    if config_data["type"] == "single_ev":
        optimizer = SingleEVOptimizer(interval_minutes=interval)
        session = config_data["session"]
        price_signal = config_data.get("price_signal")
        flat_rate = config_data.get("flat_rate", 0.25)

        schedule = optimizer.optimize(session, price_signal, flat_rate)
        click.echo(
            f"Optimised. Cost: {schedule.total_cost:.2f} EUR, "
            f"Final SoC: {schedule.final_soc:.1f}%"
        )

        ocpp_request = build_set_charging_profile_request(schedule)
        profile_path = output_dir / f"charging_profile_{session.session_id}.json"
        profile_path.write_text(to_json(ocpp_request))
        click.echo(f"OCPP profile written to {profile_path}")

        if to_ocpp_message is not None:
            message_path = output_dir / f"ocpp_message_{session.session_id}.json"
            message_path.write_text(to_ocpp_message(ocpp_request))
            click.echo(f"OCPP message written to {message_path}")

        if output_format in ("csv", "both"):
            csv_path = output_dir / f"schedule_{session.session_id}.csv"
            write_schedule_csv([schedule], csv_path)
            click.echo(f"Schedule CSV written to {csv_path}")

        if plot:
            _generate_plots([schedule], output_dir)

    elif config_data["type"] == "fleet":
        optimizer = FleetOptimizer(interval_minutes=interval)
        sessions = config_data["sessions"]
        site_config = config_data["site_config"]

        fleet_schedule = optimizer.optimize(sessions, site_config)
        click.echo(
            f"Fleet optimised. {len(fleet_schedule.sessions)} EVs, "
            f"Total cost: {fleet_schedule.total_cost:.2f} EUR, "
            f"Peak demand: {fleet_schedule.peak_demand_w / 1000:.1f} kW"
        )

        if output_format in ("json", "both"):
            results_path = output_dir / "fleet_results.json"
            write_fleet_results(fleet_schedule, results_path)
            click.echo(f"Fleet results written to {results_path}")

            profiles_dir = output_dir / "ocpp_profiles"
            profiles_dir.mkdir(exist_ok=True)
            for ev_sched in fleet_schedule.sessions:
                ocpp_req = build_set_charging_profile_request(ev_sched)
                p = profiles_dir / f"profile_{ev_sched.charger_id}.json"
                p.write_text(to_json(ocpp_req))
            click.echo(f"OCPP profiles written to {profiles_dir}/")

        if output_format in ("csv", "both"):
            csv_path = output_dir / "fleet_schedule.csv"
            write_schedule_csv(fleet_schedule.sessions, csv_path)
            click.echo(f"Fleet schedule CSV written to {csv_path}")

        if plot:
            _generate_plots(fleet_schedule.sessions, output_dir, fleet_schedule)

    click.echo("Done.")


@cli.command()
@click.option("--config", "-c", required=True, type=click.Path(exists=True))
@click.option("--output", "-o", default=".", type=click.Path())
@click.option("--plot", is_flag=True)
@click.option(
    "--interval", default=15, type=int, help="Optimisation interval in minutes"
)
def compare(config: str, output: str, plot: bool, interval: int) -> None:
    """Compare optimised vs uncontrolled charging strategies."""
    from ..inputs.json_loader import load_config
    from ..optimizer.single_ev import SingleEVOptimizer
    from ..optimizer.strategies import uncontrolled_strategy

    config_data = load_config(Path(config))
    if config_data["type"] != "single_ev":
        click.echo(
            "compare command currently supports single_ev configs only.", err=True
        )
        sys.exit(1)

    session = config_data["session"]
    price_signal = config_data.get("price_signal")
    flat_rate = config_data.get("flat_rate", 0.25)

    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    opt = SingleEVOptimizer(interval_minutes=interval)
    optimised = opt.optimize(session, price_signal, flat_rate)
    baseline = uncontrolled_strategy(
        session, price_signal=price_signal, flat_rate=flat_rate
    )

    click.echo(
        f"Optimised cost:    {optimised.total_cost:.2f} EUR  "
        f"(SoC: {optimised.final_soc:.1f}%)"
    )
    click.echo(
        f"Uncontrolled cost: {baseline.total_cost:.2f} EUR  "
        f"(SoC: {baseline.final_soc:.1f}%)"
    )
    if baseline.total_cost and optimised.total_cost:
        saving = baseline.total_cost - optimised.total_cost
        pct = saving / baseline.total_cost * 100
        click.echo(f"Saving: {saving:.2f} EUR ({pct:.1f}%)")

    if plot:
        _generate_plots([optimised], output_dir)


@cli.command("generate-config")
@click.option(
    "--type",
    "config_type",
    type=click.Choice(["single-ev", "fleet"]),
    required=True,
)
@click.option("--output", "-o", required=True, type=click.Path())
def generate_config(config_type: str, output: str) -> None:
    """Generate a template config JSON file."""
    from ..inputs.synthetic import generate_example_config

    config = generate_example_config(config_type)
    Path(output).write_text(json.dumps(config, indent=2, default=str))
    click.echo(f"Template config written to {output}")


@cli.command()
@click.option("--config", "-c", required=True, type=click.Path(exists=True))
def validate(config: str) -> None:
    """Validate a config file without running optimisation."""
    from pydantic import ValidationError

    from ..inputs.json_loader import load_config

    try:
        load_config(Path(config))
        click.echo("Config is valid")
    except (ValueError, ValidationError) as e:
        click.echo(f"Validation failed: {e}", err=True)
        sys.exit(1)


def _generate_plots(
    sessions: list[Any],
    output_dir: Path,
    fleet_schedule: Any = None,
) -> None:
    try:
        from ..viz.schedule_plot import plot_fleet_schedule
        from ..viz.soc_plot import plot_soc_curves

        fig = plot_fleet_schedule(sessions, fleet_schedule)
        fig.savefig(output_dir / "schedule_plot.png", dpi=150, bbox_inches="tight")
        click.echo(f"Schedule plot saved to {output_dir / 'schedule_plot.png'}")

        fig2 = plot_soc_curves(sessions)
        fig2.savefig(output_dir / "soc_curves.png", dpi=150, bbox_inches="tight")
        click.echo(f"SoC curves saved to {output_dir / 'soc_curves.png'}")
    except ImportError:
        click.echo(
            "Warning: matplotlib not installed. "
            "Install with: pip install 'gridmind[viz]'"
        )
