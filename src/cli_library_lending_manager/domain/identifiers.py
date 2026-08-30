"""Shared rules for stable library identifiers."""

from collections.abc import Iterable


class IdentifierError(ValueError):
    """Base error for invalid identifier operations."""


class BlankIdentifierError(IdentifierError):
    """Raised when an identifier is empty or only whitespace."""


class DuplicateIdentifierError(IdentifierError):
    """Raised when an equivalent identifier already exists."""


class UnknownIdentifierError(IdentifierError):
    """Raised when no entity has the requested identifier."""


def normalize_id(identifier: str) -> str:
    """Return the case-insensitive comparison form of an identifier."""
    normalized = identifier.strip().casefold()
    if not normalized:
        raise BlankIdentifierError("Identifier cannot be blank")
    return normalized


def ids_match(first: str, second: str) -> bool:
    """Return whether two identifiers are equivalent under the shared rule."""
    return normalize_id(first) == normalize_id(second)


def ensure_unique_id(identifier: str, existing_ids: Iterable[str]) -> None:
    """Raise when an equivalent identifier already exists."""
    normalized = normalize_id(identifier)
    if any(normalize_id(existing) == normalized for existing in existing_ids):
        raise DuplicateIdentifierError(f"Identifier already exists: {identifier.strip()}")
