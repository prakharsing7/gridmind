"""State-of-Charge curve visualisation."""

from __future__ import annotations

try:
    import matplotlib.pyplot as plt
except ImportError as e:
    raise ImportError("matplotlib required: pip install 'gridmind[viz]'") from e

from ..constants import PLOT_FIGSIZE_FLEET
from ..models.schedule import EVChargingSchedule


def plot_soc_curves(
    sessions: list[EVChargingSchedule],
    battery_capacities_kwh: list[float] | None = None,
    title: str | None = None,
) -> plt.Figure:
    """
    Plot estimated SoC trajectory for each session.

    SoC is reconstructed from period energy values (approximate).
    """
    fig, ax = plt.subplots(figsize=PLOT_FIGSIZE_FLEET)
    colours = plt.cm.Set2.colors

    for idx, session in enumerate(sessions):
        cap_kwh = battery_capacities_kwh[idx] if battery_capacities_kwh else 60.0
        times = [session.periods[0].start]
        soc_values = [0.0]

        cumulative_kwh = 0.0
        for period in session.periods:
            cumulative_kwh += period.energy_kwh
            times.append(period.end)
            soc_values.append(min(cumulative_kwh / cap_kwh * 100.0, 100.0))

        ax.plot(
            range(len(times)),
            soc_values,
            label=f"EV {session.charger_id}",
            color=colours[idx % len(colours)],
            linewidth=2,
            marker="o",
            markersize=3,
        )

    ax.set_xlabel("Time step", fontsize=11)
    ax.set_ylabel("State of Charge (%)", fontsize=11)
    ax.set_title(title or "SoC Trajectories", fontsize=13, fontweight="bold")
    ax.set_ylim(0, 105)
    ax.axhline(
        80,
        color="grey",
        linestyle="--",
        linewidth=1,
        alpha=0.5,
        label="80% target",
    )
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(alpha=0.3, linestyle="--")
    plt.tight_layout()
    return fig
