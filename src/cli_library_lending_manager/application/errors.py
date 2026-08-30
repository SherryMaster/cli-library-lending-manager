"""Errors raised by library application operations."""


class BlankFieldError(ValueError):
    """Raised when required descriptive text is blank."""


class ActiveLoanError(ValueError):
    """Raised when an active loan prevents an operation."""


class BookAlreadyLoanedError(ValueError):
    """Raised when checkout is requested for an unavailable book."""


class LoanAlreadyReturnedError(ValueError):
    """Raised when a returned loan is returned again."""


class InvalidLoanDateError(ValueError):
    """Raised when loan dates are chronologically invalid."""
