"""Core lending concepts and business rules.

This package must remain independent of terminal and persistence details.
"""

from .identifiers import (
    BlankIdentifierError,
    DuplicateIdentifierError,
    IdentifierError,
    UnknownIdentifierError,
    ensure_unique_id,
    ids_match,
    normalize_id,
)
from .models import Book, LibraryState, Loan, Member

__all__ = [
    "BlankIdentifierError",
    "Book",
    "DuplicateIdentifierError",
    "IdentifierError",
    "LibraryState",
    "Loan",
    "Member",
    "UnknownIdentifierError",
    "ensure_unique_id",
    "ids_match",
    "normalize_id",
]
