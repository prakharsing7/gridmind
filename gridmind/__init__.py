"""
gridmind

A Python library and CLI tool that computes optimal EV charging schedules
and outputs them as OCPP-native SetChargingProfile messages.

Typical usage:
    from gridmind import SingleEVOptimizer, FleetOptimizer, EVSession
    from gridmind import build_set_charging_profile_request, to_json
"""

from __future__ import annotations

from .constants import VERSION
from .exceptions import (
    ConfigValidationError,
    InfeasibleError,
    OCPPEncodingError,
    OCPPOptimizerError,
    OptimisationError,
    SolverError,
)
from .models.schedule import EVChargingSchedule, FleetSchedule, SchedulePeriod
from .models.session import ChargerConfig, EVSession
from .models.site import GridConstraints, PricePeriod, PriceSignal, SiteConfig
from .ocpp.v16.charging_profile import (
    build_set_charging_profile_request,
    to_json,
    to_ocpp_message,
)
from .optimizer.demand_response import apply_demand_response
from .optimizer.fleet import FleetOptimizer
from .optimizer.single_ev import SingleEVOptimizer
from .optimizer.strategies import uncontrolled_strategy

__version__ = VERSION

__all__ = [
    "ChargerConfig",
    "ConfigValidationError",
    "EVChargingSchedule",
    "EVSession",
    "FleetOptimizer",
    "FleetSchedule",
    "GridConstraints",
    "InfeasibleError",
    "OCPPEncodingError",
    "OCPPOptimizerError",
    "OptimisationError",
    "PricePeriod",
    "PriceSignal",
    "SchedulePeriod",
    "SingleEVOptimizer",
    "SiteConfig",
    "SolverError",
    "apply_demand_response",
    "build_set_charging_profile_request",
    "to_json",
    "to_ocpp_message",
    "uncontrolled_strategy",
]
