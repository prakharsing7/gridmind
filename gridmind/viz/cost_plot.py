"""Cost breakdown visualisation."""

from __future__ import annotations

try:
    import matplotlib.pyplot as plt
except ImportError as e:
    raise ImportError("matplotlib required: pip install 'gridmind[viz]'") from e

from ..constants import COLOUR_OPTIMISED, PLOT_FIGSIZE_SINGLE
from ..models.schedule import EVChargingSchedule


def plot_cost_breakdown(
    sessions: list[EVChargingSchedule],
    title: str | None = None,
) -> plt.Figure:
    """Bar chart of total cost per EV session."""
    fig, ax = plt.subplots(figsize=PLOT_FIGSIZE_SINGLE)
    labels = [s.charger_id for s in sessions]
    costs = [s.total_cost or 0.0 for s in sessions]

    bars = ax.bar(labels, costs, color=COLOUR_OPTIMISED, alpha=0.85, edgecolor="white")
    for bar, cost in zip(bars, costs, strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.01,
            f"{cost:.2f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    ax.set_xlabel("Charger", fontsize=11)
    ax.set_ylabel("Cost (EUR)", fontsize=11)
    ax.set_title(title or "Charging Cost per EV", fontsize=13, fontweight="bold")
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    plt.tight_layout()
    return fig
