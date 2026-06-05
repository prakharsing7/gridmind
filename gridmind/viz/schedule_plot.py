"""Power timeline visualisation for charging schedules."""

from __future__ import annotations

import numpy as np

try:
    import matplotlib.pyplot as plt
except ImportError as e:
    raise ImportError("matplotlib required: pip install 'gridmind[viz]'") from e

from ..constants import (
    COLOUR_GRID_LIMIT,
    COLOUR_OPTIMISED,
    PLOT_FIGSIZE_FLEET,
    PLOT_FIGSIZE_SINGLE,
)
from ..models.schedule import EVChargingSchedule, FleetSchedule


def plot_fleet_schedule(
    sessions: list[EVChargingSchedule],
    fleet_schedule: FleetSchedule | None = None,
    title: str | None = None,
) -> plt.Figure:
    """Plot stacked power bar chart for all EV sessions over time."""
    fig, ax = plt.subplots(figsize=PLOT_FIGSIZE_FLEET)

    if not sessions:
        ax.text(0.5, 0.5, "No sessions to plot", ha="center", va="center")
        return fig

    all_times = sorted(
        {t for s in sessions for p in s.periods for t in (p.start, p.end)}
    )
    if len(all_times) < 2:
        return fig

    t_starts = all_times[:-1]
    colours = plt.cm.Set2.colors
    bottom = np.zeros(len(t_starts))

    for ev_idx, session in enumerate(sessions):
        powers = np.array(
            [
                next(
                    (
                        per.power_w / 1000.0
                        for per in session.periods
                        if per.start <= t < per.end
                    ),
                    0.0,
                )
                for t in t_starts
            ]
        )
        ax.bar(
            range(len(t_starts)),
            powers,
            bottom=bottom,
            width=0.8,
            label=f"EV {session.charger_id}",
            color=colours[ev_idx % len(colours)],
            alpha=0.85,
            linewidth=0.3,
            edgecolor="white",
        )
        bottom += powers

    if fleet_schedule:
        limit_kw = fleet_schedule.peak_demand_w / 1000.0
        ax.axhline(
            limit_kw,
            color=COLOUR_GRID_LIMIT,
            linewidth=2,
            linestyle="--",
            label=f"Feeder limit ({limit_kw:.0f} kW)",
            zorder=5,
        )

    n_labels = min(12, len(t_starts))
    step = max(1, len(t_starts) // n_labels)
    ax.set_xticks(range(0, len(t_starts), step))
    ax.set_xticklabels(
        [t_starts[i].strftime("%H:%M") for i in range(0, len(t_starts), step)],
        rotation=45,
        ha="right",
        fontsize=8,
    )
    ax.set_xlabel("Time interval", fontsize=11)
    ax.set_ylabel("Power (kW)", fontsize=11)
    ax.set_title(
        title or f"Fleet Charging Schedule — {len(sessions)} EVs",
        fontsize=13,
        fontweight="bold",
    )
    ax.legend(loc="upper right", fontsize=9)
    ax.set_ylim(bottom=0)
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    plt.tight_layout()
    return fig


def plot_single_schedule(
    session: EVChargingSchedule, title: str | None = None
) -> plt.Figure:
    """Plot power timeline for a single EV session."""
    fig, ax = plt.subplots(figsize=PLOT_FIGSIZE_SINGLE)
    powers: list[float] = []
    for period in session.periods:
        powers.extend([period.power_w / 1000.0] * 2)

    ax.fill_between(range(len(powers)), powers, alpha=0.6, color=COLOUR_OPTIMISED)
    ax.plot(range(len(powers)), powers, color=COLOUR_OPTIMISED, linewidth=2)
    ax.set_ylabel("Power (kW)", fontsize=11)
    ax.set_xlabel("Time", fontsize=11)
    ax.set_title(
        title or f"Charging Schedule — {session.session_id}",
        fontsize=13,
        fontweight="bold",
    )
    ax.grid(alpha=0.3, linestyle="--")
    plt.tight_layout()
    return fig
