"""Errors raised by library application operations."""


class BlankFieldError(ValueError):
    """Raised when required descriptive text is blank."""


class ActiveLoanError(ValueError):
    """Raised when an active loan prevents an operation."""
