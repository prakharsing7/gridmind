"""
Data model for a single EV charging session.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from gridmind.constants import (
    DEFAULT_CHARGING_EFFICIENCY,
    DEFAULT_VOLTAGE_V,
    MIN_SOC_DEFAULT_PERCENT,
)


class EVSession(BaseModel):
    """
    Represents a single EV charging session at one charger.

    All power values are in Watts (W).
    All SoC values are in percent (0.0-100.0).
    All times are timezone-aware UTC datetimes.
    """

    session_id: str = Field(..., description="Unique identifier for this session")
    charger_id: str = Field(
        ..., description="Charger identifier (must match ChargerConfig.charger_id)"
    )

    arrival_time: datetime = Field(
        ..., description="Time when EV connected to charger (UTC, timezone-aware)"
    )
    departure_time: datetime = Field(
        ..., description="Expected departure time (UTC, timezone-aware)"
    )

    initial_soc: float = Field(
        ..., ge=0.0, le=100.0, description="State of Charge at arrival (percent)"
    )
    target_soc: float = Field(
        default=80.0,
        ge=0.0,
        le=100.0,
        description="Required SoC at departure (percent)",
    )
    min_soc: float = Field(
        default=MIN_SOC_DEFAULT_PERCENT,
        ge=0.0,
        le=100.0,
        description="Minimum allowed SoC at any point (percent)",
    )

    battery_capacity_kwh: float = Field(
        ..., gt=0.0, description="Total usable battery capacity (kWh)"
    )

    max_charge_rate_w: float = Field(
        ..., gt=0.0, description="Maximum charging rate for this EV (Watts)"
    )
    min_charge_rate_w: float = Field(
        default=0.0,
        ge=0.0,
        description="Minimum charging rate when charging (0 = can pause)",
    )
    charging_efficiency: float = Field(
        default=DEFAULT_CHARGING_EFFICIENCY,
        gt=0.0,
        le=1.0,
        description="AC-to-battery charging efficiency (0-1)",
    )

    @field_validator("departure_time")
    @classmethod
    def departure_after_arrival(cls, v: datetime, info: Any) -> datetime:
        if "arrival_time" in info.data and v <= info.data["arrival_time"]:
            raise ValueError("departure_time must be after arrival_time")
        return v

    @model_validator(mode="after")
    def target_soc_reachable(self) -> EVSession:
        """Raise if target SoC is mathematically unreachable given time and power constraints."""
        energy_needed_kwh = (
            (self.target_soc - self.initial_soc)
            / 100.0
            * self.battery_capacity_kwh
            / self.charging_efficiency
        )
        if energy_needed_kwh <= 0:
            return self
        session_hours = (
            self.departure_time - self.arrival_time
        ).total_seconds() / 3600.0
        max_deliverable_kwh = (self.max_charge_rate_w / 1000.0) * session_hours
        if energy_needed_kwh > max_deliverable_kwh * 1.05:
            raise ValueError(
                f"Target SoC {self.target_soc}% is not reachable: "
                f"need {energy_needed_kwh:.2f} kWh but can deliver max "
                f"{max_deliverable_kwh:.2f} kWh in available session time"
            )
        return self

    @property
    def session_duration_hours(self) -> float:
        """Session length in hours."""
        return (self.departure_time - self.arrival_time).total_seconds() / 3600.0

    @property
    def energy_needed_kwh(self) -> float:
        """Energy (kWh) needed to go from initial_soc to target_soc, accounting for efficiency."""
        return max(
            0.0,
            (self.target_soc - self.initial_soc)
            / 100.0
            * self.battery_capacity_kwh
            / self.charging_efficiency,
        )


class ChargerConfig(BaseModel):
    """
    Configuration for a physical EV charger.
    This is the hardware layer; EVSession is the session layer.
    """

    charger_id: str = Field(
        ..., description="Unique charger identifier (matches OCPP chargePointId)"
    )
    max_power_w: float = Field(
        ..., gt=0.0, description="Hardware maximum power output (Watts)"
    )
    min_power_w: float = Field(
        default=0.0,
        ge=0.0,
        description="Minimum power when active (Watts). 0 = can be turned off",
    )
    num_connectors: int = Field(
        default=1, ge=1, le=4, description="Number of connectors on this charger"
    )
    connector_type: str = Field(
        default="Type2",
        description="Connector type: Type1, Type2, CCS, CHAdeMO, Schuko",
    )
    supports_smart_charging: bool = Field(
        default=True,
        description="Whether charger implements OCPP SetChargingProfile",
    )
    phase_count: int = Field(
        default=3, ge=1, le=3, description="Number of AC phases (1 or 3)"
    )
    voltage_v: float = Field(
        default=DEFAULT_VOLTAGE_V, gt=0.0, description="Operating voltage (Volts)"
    )
