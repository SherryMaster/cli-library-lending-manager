"""Book and member operations for the library application."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, timedelta

from cli_library_lending_manager.domain import (
    Book,
    LibraryState,
    Loan,
    Member,
    ensure_unique_id,
    normalize_id,
)

from .errors import (
    ActiveLoanError,
    BlankFieldError,
    BookAlreadyLoanedError,
    InvalidLoanDateError,
    LoanAlreadyReturnedError,
)

LOAN_PERIOD_DAYS = 14


def _clean_text(value: str, field_name: str) -> str:
    """Trim required text or raise a useful validation error."""
    cleaned = value.strip()
    if not cleaned:
        raise BlankFieldError(f"{field_name} cannot be blank")
    return cleaned


class Library:
    """Perform validated book and member operations on a library state."""

    def __init__(self, state: LibraryState | None = None) -> None:
        self.state = LibraryState() if state is None else state

    def add_book(
        self, book_id: str, title: str, author: str, category: str
    ) -> Book:
        """Validate and add a book, then return the new record."""
        clean_id = book_id.strip()
        normalize_id(clean_id)
        clean_title = _clean_text(title, "Book title")
        clean_author = _clean_text(author, "Book author")
        clean_category = _clean_text(category, "Book category")
        ensure_unique_id(clean_id, (book.id for book in self.state.books))

        book = Book(clean_id, clean_title, clean_author, clean_category)
        self.state.books.append(book)
        return book

    def add_member(self, member_id: str, name: str) -> Member:
        """Validate and add a member, then return the new record."""
        clean_id = member_id.strip()
        normalize_id(clean_id)
        clean_name = _clean_text(name, "Member name")
        ensure_unique_id(clean_id, (member.id for member in self.state.members))

        member = Member(clean_id, clean_name)
        self.state.members.append(member)
        return member

    def get_book(self, book_id: str) -> Book:
        """Find a book using exact stable-ID matching."""
        return self.state.get_book(book_id)

    def get_member(self, member_id: str) -> Member:
        """Find a member using exact stable-ID matching."""
        return self.state.get_member(member_id)

    def get_loan(self, loan_id: str) -> Loan:
        """Find a loan using exact stable-ID matching."""
        return self.state.get_loan(loan_id)

    def list_books(self) -> list[Book]:
        """Return a copy of the current book collection."""
        return list(self.state.books)

    def list_members(self) -> list[Member]:
        """Return a copy of the current member collection."""
        return list(self.state.members)

    def search_books(self, query: str) -> list[Book]:
        """Find books by case-insensitive partial descriptive text."""
        term = query.strip().casefold()
        return [
            book
            for book in self.state.books
            if term in book.title.casefold()
            or term in book.author.casefold()
            or term in book.category.casefold()
        ]

    def search_members(self, query: str) -> list[Member]:
        """Find members by case-insensitive partial name."""
        term = query.strip().casefold()
        return [
            member
            for member in self.state.members
            if term in member.name.casefold()
        ]

    def update_book(
        self, book_id: str, *, title: str, author: str, category: str
    ) -> Book:
        """Replace a book's descriptive data while preserving its stable ID."""
        current = self.get_book(book_id)
        updated = replace(
            current,
            title=_clean_text(title, "Book title"),
            author=_clean_text(author, "Book author"),
            category=_clean_text(category, "Book category"),
        )
        index = self.state.books.index(current)
        self.state.books[index] = updated
        return updated

    def update_member(self, member_id: str, *, name: str) -> Member:
        """Replace a member's name while preserving the stable ID."""
        current = self.get_member(member_id)
        updated = replace(current, name=_clean_text(name, "Member name"))
        index = self.state.members.index(current)
        self.state.members[index] = updated
        return updated

    def remove_book(self, book_id: str) -> Book:
        """Remove and return a book unless it has an active loan."""
        book = self.get_book(book_id)
        if self.state.active_loan_for_book(book.id) is not None:
            raise ActiveLoanError(f"Book has an active loan: {book.id}")
        self.state.books.remove(book)
        return book

    def remove_member(self, member_id: str) -> Member:
        """Remove and return a member unless they have an active loan."""
        member = self.get_member(member_id)
        if self.state.active_loans_for_member(member.id):
            raise ActiveLoanError(f"Member has an active loan: {member.id}")
        self.state.members.remove(member)
        return member

    def checkout_book(
        self,
        loan_id: str,
        book_id: str,
        member_id: str,
        *,
        checkout_date: date | None = None,
    ) -> Loan:
        """Create a 14-day loan after validating the complete relationship."""
        clean_loan_id = loan_id.strip()
        normalize_id(clean_loan_id)
        ensure_unique_id(clean_loan_id, (loan.id for loan in self.state.loans))
        book = self.get_book(book_id)
        member = self.get_member(member_id)

        if self.state.active_loan_for_book(book.id) is not None:
            raise BookAlreadyLoanedError(f"Book is already on loan: {book.id}")

        checked_out_on = date.today() if checkout_date is None else checkout_date
        loan = Loan(
            id=clean_loan_id,
            book_id=book.id,
            member_id=member.id,
            checkout_date=checked_out_on,
            due_date=checked_out_on + timedelta(days=LOAN_PERIOD_DAYS),
        )
        self.state.loans.append(loan)
        return loan

    def return_loan(
        self, loan_id: str, *, returned_date: date | None = None
    ) -> Loan:
        """Complete a loan exactly once while preserving its history."""
        current = self.get_loan(loan_id)
        if not current.is_active:
            raise LoanAlreadyReturnedError(f"Loan is already returned: {current.id}")

        returned_on = date.today() if returned_date is None else returned_date
        if returned_on < current.checkout_date:
            raise InvalidLoanDateError(
                "Returned date cannot be earlier than checkout date"
            )

        returned = replace(current, returned_date=returned_on)
        index = self.state.loans.index(current)
        self.state.loans[index] = returned
        return returned

    def active_loan_for_book(self, book_id: str) -> Loan | None:
        """Return an active loan after confirming that the book exists."""
        book = self.get_book(book_id)
        return self.state.active_loan_for_book(book.id)

    def active_loans_for_member(self, member_id: str) -> list[Loan]:
        """Return active loans after confirming that the member exists."""
        member = self.get_member(member_id)
        return self.state.active_loans_for_member(member.id)

    def is_book_available(self, book_id: str) -> bool:
        """Return availability derived from active loan records."""
        return self.state.is_book_available(book_id)
