"""
Custom exceptions for gridmind.
All exceptions inherit from OCPPOptimizerError for easy catch-all handling.
"""


class OCPPOptimizerError(Exception):
    """Base exception for all errors in this package."""


class OptimisationError(OCPPOptimizerError):
    """General optimisation failure."""


class InfeasibleError(OptimisationError):
    """
    Raised when no feasible schedule exists.

    Common causes:
    - Insufficient session time to reach target SoC
    - Feeder limit too restrictive for fleet size
    - Target SoC set too high given hardware limits
    """


class SolverError(OptimisationError):
    """Raised when the mathematical solver encounters an unexpected error."""


class OCPPEncodingError(OCPPOptimizerError):
    """Raised when a schedule cannot be encoded as a valid OCPP profile."""


class ConfigValidationError(OCPPOptimizerError):
    """Raised when input configuration is invalid."""


class SessionConflictError(OCPPOptimizerError):
    """Raised when multiple sessions are assigned to the same charger at the same time."""
