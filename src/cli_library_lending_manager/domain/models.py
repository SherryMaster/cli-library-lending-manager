"""Canonical in-memory records for the library domain."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from .identifiers import UnknownIdentifierError, ids_match


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

    def get_book(self, book_id: str) -> Book:
        """Return the book matching an exact stable identifier."""
        for book in self.books:
            if ids_match(book.id, book_id):
                return book
        raise UnknownIdentifierError(f"Unknown book ID: {book_id.strip()}")

    def get_member(self, member_id: str) -> Member:
        """Return the member matching an exact stable identifier."""
        for member in self.members:
            if ids_match(member.id, member_id):
                return member
        raise UnknownIdentifierError(f"Unknown member ID: {member_id.strip()}")

    def get_loan(self, loan_id: str) -> Loan:
        """Return the loan matching an exact stable identifier."""
        for loan in self.loans:
            if ids_match(loan.id, loan_id):
                return loan
        raise UnknownIdentifierError(f"Unknown loan ID: {loan_id.strip()}")

    def active_loan_for_book(self, book_id: str) -> Loan | None:
        """Return a book's active loan, or ``None`` when it has none."""
        for loan in self.loans:
            if loan.is_active and ids_match(loan.book_id, book_id):
                return loan
        return None

    def active_loans_for_member(self, member_id: str) -> list[Loan]:
        """Return all active loans belonging to a member."""
        return [
            loan
            for loan in self.loans
            if loan.is_active and ids_match(loan.member_id, member_id)
        ]

    def is_book_available(self, book_id: str) -> bool:
        """Return availability derived from the canonical loan history."""
        self.get_book(book_id)
        return self.active_loan_for_book(book_id) is None
