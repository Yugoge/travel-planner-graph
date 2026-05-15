"""Validation error types."""

from dataclasses import dataclass


@dataclass
class ValidationError:
    """One validator finding. code is the machine-stable rule id; path locates the offender."""
    code: str
    path: str
    message: str
    severity: str = "error"  # error | warning

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.code} at {self.path}: {self.message}"


class TripContractError(Exception):
    """Raised by callers that prefer exceptions to lists."""


class StateMachineError(TripContractError):
    """Raised when a stage transition is rejected by validate_state_transition."""
