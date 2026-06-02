"""
Output data models for charging schedules — single EV and fleet level.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SchedulePeriod(BaseModel):
    """A single time-sliced interval within a charging schedule."""

    start: datetime
    end: datetime
    power_w: float = Field(
        ..., ge=0.0, description="Average power during this period (Watts)."
    )
    price_per_kwh: float | None = Field(default=None, ge=0.0)

    @property
    def duration_hours(self) -> float:
        return (self.end - self.start).total_seconds() / 3600.0

    @property
    def energy_kwh(self) -> float:
        return self.power_w * self.duration_hours / 1000.0

    @property
    def cost(self) -> float | None:
        if self.price_per_kwh is None:
            return None
        return self.energy_kwh * self.price_per_kwh


class EVChargingSchedule(BaseModel):
    """Optimised charging schedule for a single EV session."""

    session_id: str
    charger_id: str
    periods: list[SchedulePeriod] = Field(..., min_length=1)

    total_energy_kwh: float = Field(..., ge=0.0)
    final_soc: float = Field(..., ge=0.0, le=100.0)
    total_cost: float | None = Field(default=None, ge=0.0)

    target_soc_met: bool
    feasible: bool
    solver_status: str

    optimised_at: datetime
    optimisation_duration_ms: float = Field(..., ge=0.0)


class FleetSchedule(BaseModel):
    """Aggregated optimisation result for all EVs at a site."""

    site_id: str
    sessions: list[EVChargingSchedule] = Field(..., min_length=1)

    total_energy_kwh: float = Field(..., ge=0.0)
    total_cost: float | None = Field(default=None, ge=0.0)
    peak_demand_w: float = Field(..., ge=0.0)
    avg_demand_w: float = Field(..., ge=0.0)

    feeder_limit_respected: bool
    all_sessions_feasible: bool
    demand_response_met: bool

    optimised_at: datetime
    optimisation_duration_ms: float = Field(..., ge=0.0)
    solver: str
    num_variables: int = Field(..., ge=0)
    num_constraints: int = Field(..., ge=0)
