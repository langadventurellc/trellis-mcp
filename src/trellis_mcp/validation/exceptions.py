"""Exception classes for validation operations.

This module defines custom exception classes used throughout the validation
system for different types of validation errors.
"""


class CircularDependencyError(ValueError):
    """Exception raised when a circular dependency is detected in prerequisites."""

    def __init__(self, cycle_path: list[str]):
        """Initialize circular dependency error.

        Args:
            cycle_path: List of object IDs that form the cycle
        """
        self.cycle_path = cycle_path
        cycle_str = " -> ".join(cycle_path)
        super().__init__(f"Circular dependency detected: {cycle_str}")


class TrellisValidationError(Exception):
    """Custom validation error that can hold multiple error messages."""

    def __init__(self, errors: list[str]):
        """Initialize validation error.

        Args:
            errors: List of validation error messages
        """
        self.errors = errors
        super().__init__(f"Validation failed: {'; '.join(errors)}")
