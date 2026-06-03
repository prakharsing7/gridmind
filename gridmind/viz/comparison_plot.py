"""Strategy comparison visualisation (optimised vs uncontrolled)."""

from __future__ import annotations

try:
    from matplotlib.figure import Figure as MplFigure
    import matplotlib.pyplot as plt
except ImportError as e:
    raise ImportError("matplotlib required: pip install 'gridmind[viz]'") from e

from ..constants import COLOUR_OPTIMISED, COLOUR_UNCONTROLLED, PLOT_FIGSIZE_COMPARISON
from ..models.schedule import EVChargingSchedule


def plot_strategy_comparison(
    optimised: EVChargingSchedule,
    uncontrolled: EVChargingSchedule,
    title: str | None = None,
) -> MplFigure:
    """Side-by-side cost and power comparison between optimised and uncontrolled strategies."""
    fig, axes = plt.subplots(1, 2, figsize=PLOT_FIGSIZE_COMPARISON)

    ax_cost = axes[0]
    labels = ["Uncontrolled", "Optimised"]
    costs = [uncontrolled.total_cost or 0.0, optimised.total_cost or 0.0]
    colours = [COLOUR_UNCONTROLLED, COLOUR_OPTIMISED]
    bars = ax_cost.bar(labels, costs, color=colours, alpha=0.85)
    for bar, cost in zip(bars, costs, strict=True):
        ax_cost.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.01,
            f"{cost:.2f} EUR",
            ha="center",
            va="bottom",
            fontsize=10,
        )
    ax_cost.set_ylabel("Total Cost (EUR)", fontsize=11)
    ax_cost.set_title("Cost Comparison", fontsize=12, fontweight="bold")
    ax_cost.grid(axis="y", alpha=0.3, linestyle="--")

    ax_power = axes[1]

    def _power_series(sched: EVChargingSchedule) -> tuple[range, list[float]]:
        powers: list[float] = []
        for p in sched.periods:
            powers.extend([p.power_w / 1000.0] * 2)
        return range(len(powers)), powers

    x_u, p_u = _power_series(uncontrolled)
    x_o, p_o = _power_series(optimised)
    ax_power.plot(
        x_u,
        p_u,
        color=COLOUR_UNCONTROLLED,
        linewidth=2,
        label="Uncontrolled",
        alpha=0.8,
    )
    ax_power.plot(
        x_o, p_o, color=COLOUR_OPTIMISED, linewidth=2, label="Optimised", alpha=0.8
    )
    ax_power.set_ylabel("Power (kW)", fontsize=11)
    ax_power.set_xlabel("Time steps", fontsize=11)
    ax_power.set_title("Power Profile Comparison", fontsize=12, fontweight="bold")
    ax_power.legend(fontsize=9)
    ax_power.grid(alpha=0.3, linestyle="--")

    fig.suptitle(
        title or f"Strategy Comparison — {optimised.session_id}",
        fontsize=13,
        fontweight="bold",
    )
    plt.tight_layout()
    return fig
