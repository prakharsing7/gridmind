"""
OCPP-specific type definitions.
Based on OCPP 1.6 specification (Open Charge Alliance, 2019).
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ChargingRateUnit(StrEnum):
    """OCPP 1.6 Section 7.18: ChargingRateUnitType"""

    WATTS = "W"
    AMPERES = "A"


class ChargingProfileKind(StrEnum):
    """OCPP 1.6 Section 7.17: ChargingProfileKindType"""

    ABSOLUTE = "Absolute"
    RECURRING = "Recurring"
    RELATIVE = "Relative"


class RecurrencyKind(StrEnum):
    """OCPP 1.6 Section 7.35: RecurrencyKindType"""

    DAILY = "Daily"
    WEEKLY = "Weekly"


class ChargingProfilePurpose(StrEnum):
    """OCPP 1.6 Section 7.16: ChargingProfilePurposeType"""

    CHARGE_POINT_MAX = "ChargePointMaxProfile"
    TX_DEFAULT = "TxDefaultProfile"
    TX = "TxProfile"


class OCPP16ChargingSchedulePeriod(BaseModel):
    """OCPP 1.6 Section 7.14: ChargingSchedulePeriod"""

    startPeriod: int = Field(
        ..., ge=0, description="Start of period relative to schedule start (seconds)."
    )
    limit: float = Field(
        ..., ge=0.0, description="Power limit (W or A, per chargingRateUnit)."
    )
    numberPhases: int | None = Field(default=None, ge=1, le=3)


class OCPP16ChargingSchedule(BaseModel):
    """OCPP 1.6 Section 7.13: ChargingSchedule"""

    duration: int | None = Field(default=None, ge=0)
    startSchedule: datetime | None = Field(default=None)
    chargingRateUnit: ChargingRateUnit = Field(default=ChargingRateUnit.WATTS)
    chargingSchedulePeriod: list[OCPP16ChargingSchedulePeriod] = Field(
        ..., min_length=1, max_length=1024
    )
    minChargingRate: float | None = Field(default=None, ge=0.0)


class OCPP16ChargingProfile(BaseModel):
    """OCPP 1.6 Section 7.12: ChargingProfile"""

    chargingProfileId: int
    transactionId: int | None = Field(default=None)
    stackLevel: int = Field(default=0, ge=0)
    chargingProfilePurpose: ChargingProfilePurpose = Field(
        default=ChargingProfilePurpose.TX_DEFAULT
    )
    chargingProfileKind: ChargingProfileKind = Field(
        default=ChargingProfileKind.ABSOLUTE
    )
    recurrencyKind: RecurrencyKind | None = Field(default=None)
    validFrom: datetime | None = Field(default=None)
    validTo: datetime | None = Field(default=None)
    chargingSchedule: OCPP16ChargingSchedule


class OCPP16SetChargingProfileRequest(BaseModel):
    """OCPP 1.6 Section 5.14.2: SetChargingProfile.req"""

    connectorId: int = Field(..., ge=0)
    csChargingProfiles: OCPP16ChargingProfile
