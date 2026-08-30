"""Book and member operations for the library application."""

from __future__ import annotations

from dataclasses import replace

from cli_library_lending_manager.domain import (
    Book,
    LibraryState,
    Member,
    ensure_unique_id,
    ids_match,
    normalize_id,
)

from .errors import ActiveLoanError, BlankFieldError


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
        if any(
            loan.is_active and ids_match(loan.book_id, book.id)
            for loan in self.state.loans
        ):
            raise ActiveLoanError(f"Book has an active loan: {book.id}")
        self.state.books.remove(book)
        return book

    def remove_member(self, member_id: str) -> Member:
        """Remove and return a member unless they have an active loan."""
        member = self.get_member(member_id)
        if any(
            loan.is_active and ids_match(loan.member_id, member.id)
            for loan in self.state.loans
        ):
            raise ActiveLoanError(f"Member has an active loan: {member.id}")
        self.state.members.remove(member)
        return member
