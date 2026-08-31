"""Book and member operations for the library application."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
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


@dataclass(frozen=True, slots=True)
class LibraryStatistics:
    """Derived summary counts for the current library state."""

    total_books: int
    total_members: int
    active_loans: int
    overdue_loans: int
    historical_loans: int


def _clean_text(value: str, field_name: str) -> str:
    """Trim required text or raise a useful validation error."""
    cleaned = value.strip()
    if not cleaned:
        raise BlankFieldError(f"{field_name} cannot be blank")
    return cleaned


def _next_id(prefix: str, existing_ids: list[str]) -> str:
    """Generate the next numbered ID without reusing historical identifiers."""
    highest = 0
    folded_prefix = prefix.casefold()
    for identifier in existing_ids:
        normalized = identifier.strip().casefold()
        number = normalized.removeprefix(folded_prefix)
        if normalized.startswith(folded_prefix) and number.isdigit():
            highest = max(highest, int(number))
    return f"{prefix}{highest + 1:03d}"


class Library:
    """Perform validated book and member operations on a library state."""

    def __init__(
        self,
        state: LibraryState | None = None,
        *,
        on_change: Callable[[LibraryState], None] | None = None,
    ) -> None:
        self.state = LibraryState() if state is None else state
        self._on_change = on_change

    def _snapshot(self) -> LibraryState:
        """Copy the state collections so a failed save can be rolled back."""
        return LibraryState(
            list(self.state.books), list(self.state.members), list(self.state.loans)
        )

    def _save_change(self, previous: LibraryState) -> None:
        """Persist a mutation, restoring the previous state if saving fails."""
        if self._on_change is None:
            return
        try:
            self._on_change(self.state)
        except Exception:
            self.state.books = previous.books
            self.state.members = previous.members
            self.state.loans = previous.loans
            raise

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

        previous = self._snapshot()
        book = Book(clean_id, clean_title, clean_author, clean_category)
        self.state.books.append(book)
        self._save_change(previous)
        return book

    def create_book(self, title: str, author: str, category: str) -> Book:
        """Add a book with an automatically generated stable ID."""
        used_ids = [book.id for book in self.state.books]
        used_ids.extend(loan.book_id for loan in self.state.loans)
        return self.add_book(_next_id("B", used_ids), title, author, category)

    def add_member(self, member_id: str, name: str) -> Member:
        """Validate and add a member, then return the new record."""
        clean_id = member_id.strip()
        normalize_id(clean_id)
        clean_name = _clean_text(name, "Member name")
        ensure_unique_id(clean_id, (member.id for member in self.state.members))

        previous = self._snapshot()
        member = Member(clean_id, clean_name)
        self.state.members.append(member)
        self._save_change(previous)
        return member

    def create_member(self, name: str) -> Member:
        """Add a member with an automatically generated stable ID."""
        used_ids = [member.id for member in self.state.members]
        used_ids.extend(loan.member_id for loan in self.state.loans)
        return self.add_member(_next_id("M", used_ids), name)

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
        """Return books ordered by title, author, then stable ID."""
        return sorted(
            self.state.books,
            key=lambda book: (
                book.title.casefold(),
                book.author.casefold(),
                normalize_id(book.id),
            ),
        )

    def list_members(self) -> list[Member]:
        """Return members ordered by name, then stable ID."""
        return sorted(
            self.state.members,
            key=lambda member: (member.name.casefold(), normalize_id(member.id)),
        )

    def list_loans(self) -> list[Loan]:
        """Return newest loans first, using stable ID to break date ties."""
        return sorted(
            self.state.loans,
            key=lambda loan: (-loan.checkout_date.toordinal(), normalize_id(loan.id)),
        )

    def list_active_loans(self) -> list[Loan]:
        """Return active loans ordered by due date, then stable ID."""
        return sorted(
            (loan for loan in self.state.loans if loan.is_active),
            key=lambda loan: (loan.due_date, normalize_id(loan.id)),
        )

    def list_available_books(self) -> list[Book]:
        """Return books with no active loan in default book order."""
        return [book for book in self.list_books() if self.is_book_available(book.id)]

    def list_books_on_loan(self) -> list[Book]:
        """Return books currently referenced by active loans."""
        return [
            book for book in self.list_books() if not self.is_book_available(book.id)
        ]

    def list_returned_loans(self) -> list[Loan]:
        """Return only completed historical loans in default history order."""
        return [loan for loan in self.list_loans() if not loan.is_active]

    def list_overdue_loans(self, *, as_of: date | None = None) -> list[Loan]:
        """Return active loans whose due date is earlier than the chosen date."""
        today = date.today() if as_of is None else as_of
        return [loan for loan in self.list_active_loans() if loan.due_date < today]

    def loans_for_book(self, book_id: str) -> list[Loan]:
        """Return complete history for a known book."""
        book = self.get_book(book_id)
        return [
            loan
            for loan in self.list_loans()
            if normalize_id(loan.book_id) == normalize_id(book.id)
        ]

    def loans_for_member(self, member_id: str) -> list[Loan]:
        """Return complete history for a known member."""
        member = self.get_member(member_id)
        return [
            loan
            for loan in self.list_loans()
            if normalize_id(loan.member_id) == normalize_id(member.id)
        ]

    def list_categories(self) -> list[str]:
        """Return distinct categories in case-insensitive alphabetical order."""
        categories = {book.category for book in self.state.books}
        return sorted(categories, key=str.casefold)

    def books_in_category(self, category: str) -> list[Book]:
        """Return books in one exact case-insensitive category."""
        wanted = category.strip().casefold()
        return [
            book for book in self.list_books() if book.category.casefold() == wanted
        ]

    def books_sorted_by_author(self) -> list[Book]:
        """Return books ordered by author, title, then stable ID."""
        return sorted(
            self.state.books,
            key=lambda book: (
                book.author.casefold(),
                book.title.casefold(),
                normalize_id(book.id),
            ),
        )

    def statistics(self, *, as_of: date | None = None) -> LibraryStatistics:
        """Calculate all dashboard counts from canonical records."""
        return LibraryStatistics(
            total_books=len(self.state.books),
            total_members=len(self.state.members),
            active_loans=len(self.list_active_loans()),
            overdue_loans=len(self.list_overdue_loans(as_of=as_of)),
            historical_loans=len(self.state.loans),
        )

    @staticmethod
    def loan_due_status(loan: Loan, *, as_of: date | None = None) -> str:
        """Return a readable status derived from canonical loan dates."""
        if not loan.is_active:
            return f"Returned {loan.returned_date}"
        today = date.today() if as_of is None else as_of
        days = (loan.due_date - today).days
        if days < 0:
            amount = abs(days)
            return f"Overdue by {amount} day{'s' if amount != 1 else ''}"
        if days == 0:
            return "Due today"
        if days <= 3:
            return f"Due soon: {days} day{'s' if days != 1 else ''}"
        return f"Due in {days} days"

    def search_books(self, query: str) -> list[Book]:
        """Find books by case-insensitive partial descriptive text."""
        term = query.strip().casefold()
        return [
            book
            for book in self.list_books()
            if term in book.title.casefold()
            or term in book.author.casefold()
            or term in book.category.casefold()
        ]

    def search_members(self, query: str) -> list[Member]:
        """Find members by case-insensitive partial name."""
        term = query.strip().casefold()
        return [
            member
            for member in self.list_members()
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
        previous = self._snapshot()
        index = self.state.books.index(current)
        self.state.books[index] = updated
        self._save_change(previous)
        return updated

    def update_member(self, member_id: str, *, name: str) -> Member:
        """Replace a member's name while preserving the stable ID."""
        current = self.get_member(member_id)
        updated = replace(current, name=_clean_text(name, "Member name"))
        previous = self._snapshot()
        index = self.state.members.index(current)
        self.state.members[index] = updated
        self._save_change(previous)
        return updated

    def remove_book(self, book_id: str) -> Book:
        """Remove and return a book unless it has an active loan."""
        book = self.get_book(book_id)
        if self.state.active_loan_for_book(book.id) is not None:
            raise ActiveLoanError(f"Book has an active loan: {book.id}")
        previous = self._snapshot()
        self.state.books.remove(book)
        self._save_change(previous)
        return book

    def remove_member(self, member_id: str) -> Member:
        """Remove and return a member unless they have an active loan."""
        member = self.get_member(member_id)
        if self.state.active_loans_for_member(member.id):
            raise ActiveLoanError(f"Member has an active loan: {member.id}")
        previous = self._snapshot()
        self.state.members.remove(member)
        self._save_change(previous)
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
        previous = self._snapshot()
        self.state.loans.append(loan)
        self._save_change(previous)
        return loan

    def create_loan(
        self,
        book_id: str,
        member_id: str,
        *,
        checkout_date: date | None = None,
    ) -> Loan:
        """Check out a book with an automatically generated loan ID."""
        loan_id = _next_id("L", [loan.id for loan in self.state.loans])
        return self.checkout_book(
            loan_id, book_id, member_id, checkout_date=checkout_date
        )

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

        previous = self._snapshot()
        returned = replace(current, returned_date=returned_on)
        index = self.state.loans.index(current)
        self.state.loans[index] = returned
        self._save_change(previous)
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
