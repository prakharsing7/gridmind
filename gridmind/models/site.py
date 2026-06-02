"""
Data models for site-level configuration and grid constraints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from gridmind.constants import DEFAULT_FREQUENCY_HZ, DEFAULT_VOLTAGE_V


class GridConstraints(BaseModel):
    """
    Grid-side constraints for the charging site.
    These come from the DSO or site electrical infrastructure.
    """

    max_site_power_w: float = Field(
        ..., gt=0.0, description="Maximum total power draw for the entire site (Watts)."
    )
    max_feeder_current_a: float | None = Field(
        default=None, gt=0.0, description="Maximum feeder current (Amperes)."
    )

    demand_response_active: bool = Field(default=False)
    demand_response_reduction_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    demand_response_start: datetime | None = Field(default=None)
    demand_response_end: datetime | None = Field(default=None)

    voltage_v: float = Field(default=DEFAULT_VOLTAGE_V, gt=0.0)
    frequency_hz: float = Field(default=DEFAULT_FREQUENCY_HZ, gt=0.0)


class PricePeriod(BaseModel):
    """A single period in a price signal."""

    start: datetime
    end: datetime
    price: float = Field(..., description="Price per kWh in signal currency")

    @field_validator("end")
    @classmethod
    def end_after_start(cls, v: datetime, info: Any) -> datetime:
        if "start" in info.data and v <= info.data["start"]:
            raise ValueError("Price period end must be after start")
        return v


class PriceSignal(BaseModel):
    """
    Time-varying electricity price signal.
    Can represent TOU tariff, real-time pricing, or day-ahead prices.
    """

    periods: list[PricePeriod] = Field(..., min_length=1)
    currency: str = Field(default="EUR")
    unit: str = Field(default="EUR/kWh")
