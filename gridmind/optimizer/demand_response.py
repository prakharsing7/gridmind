"""
Demand response helpers for the fleet optimiser.

These functions modify GridConstraints to activate DR constraints.
The FleetOptimizer reads these flags when building its LP.
"""

from __future__ import annotations

from datetime import datetime

from ..models.site import GridConstraints


def apply_demand_response(
    grid: GridConstraints,
    reduction_percent: float,
    start: datetime,
    end: datetime,
) -> GridConstraints:
    """
    Return a new GridConstraints with a demand response event activated.

    Does NOT mutate the original. The FleetOptimizer will enforce:
        sum(P[i,t]) <= max_site_power * (1 - reduction_percent/100)
    for all t in [start, end).
    """
    return grid.model_copy(
        update={
            "demand_response_active": True,
            "demand_response_reduction_percent": reduction_percent,
            "demand_response_start": start,
            "demand_response_end": end,
        }
    )
