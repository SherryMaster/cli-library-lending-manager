"""Canonical in-memory records for the library domain."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True, slots=True)
class Book:
    """A library-owned book identified independently of its descriptive data."""

    id: str
    title: str
    author: str
    category: str


@dataclass(frozen=True, slots=True)
class Member:
    """A person registered to borrow books from the library."""

    id: str
    name: str


@dataclass(frozen=True, slots=True)
class Loan:
    """A current or historical lending relationship.

    ``returned_date`` is the single source of truth for return status. An
    absent date means the loan is active; a present date means it is part of
    the retained return history.
    """

    id: str
    book_id: str
    member_id: str
    checkout_date: date
    due_date: date
    returned_date: date | None = None

    @property
    def is_active(self) -> bool:
        """Return whether this loan has not yet been returned."""
        return self.returned_date is None


@dataclass(slots=True)
class LibraryState:
    """Own the canonical entity collections for one in-memory library.

    The loan collection contains both active and returned loans. Availability,
    totals, and overdue status will be derived from these records rather than
    stored as competing sources of truth.
    """

    books: list[Book] = field(default_factory=list)
    members: list[Member] = field(default_factory=list)
    loans: list[Loan] = field(default_factory=list)
