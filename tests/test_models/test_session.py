import pytest

from gridmind.exceptions import (
    ConfigValidationError,
    InfeasibleError,
    OCPPEncodingError,
    OCPPOptimizerError,
    OptimisationError,
    SessionConflictError,
    SolverError,
)


def test_exception_hierarchy():
    assert issubclass(OptimisationError, OCPPOptimizerError)
    assert issubclass(InfeasibleError, OptimisationError)
    assert issubclass(SolverError, OptimisationError)
    assert issubclass(OCPPEncodingError, OCPPOptimizerError)
    assert issubclass(ConfigValidationError, OCPPOptimizerError)
    assert issubclass(SessionConflictError, OCPPOptimizerError)


def test_infeasible_error_is_catchable_as_base():
    with pytest.raises(OCPPOptimizerError):
        raise InfeasibleError("not enough time")
