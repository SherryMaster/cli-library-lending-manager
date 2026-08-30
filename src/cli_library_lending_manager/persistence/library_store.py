"""JSON persistence adapter for complete library state."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from cli_library_lending_manager.domain import (
    Book,
    IdentifierError,
    LibraryState,
    Loan,
    Member,
    normalize_id,
)

from .json_storage import JsonStorage, StorageError


class InvalidDataError(StorageError):
    """Raised when stored JSON has an invalid library-data shape."""


class JsonLibraryStore:
    """Load and save canonical library records through ``JsonStorage``."""

    def __init__(self, file_path: str | Path) -> None:
        self.file_path = Path(file_path)
        self.storage = JsonStorage(
            self.file_path, {"books": [], "members": [], "loans": []}
        )

    def load(self) -> LibraryState:
        """Load and validate a complete state, or return an empty first launch."""
        data = self.storage.load()
        return self._state_from_data(data)

    def save(self, state: LibraryState) -> None:
        """Serialize and atomically save a complete library state."""
        self.storage.save(
            {
                "books": [
                    {
                        "id": book.id,
                        "title": book.title,
                        "author": book.author,
                        "category": book.category,
                    }
                    for book in state.books
                ],
                "members": [
                    {"id": member.id, "name": member.name}
                    for member in state.members
                ],
                "loans": [
                    {
                        "id": loan.id,
                        "book_id": loan.book_id,
                        "member_id": loan.member_id,
                        "checkout_date": loan.checkout_date.isoformat(),
                        "due_date": loan.due_date.isoformat(),
                        "returned_date": (
                            loan.returned_date.isoformat()
                            if loan.returned_date is not None
                            else None
                        ),
                    }
                    for loan in state.loans
                ],
            }
        )

    def _state_from_data(self, data: Any) -> LibraryState:
        if not isinstance(data, dict):
            raise InvalidDataError("Library data must be a JSON object")

        books_data = self._record_list(data, "books")
        members_data = self._record_list(data, "members")
        loans_data = self._record_list(data, "loans")

        books = [self._book(record, index) for index, record in enumerate(books_data)]
        members = [
            self._member(record, index) for index, record in enumerate(members_data)
        ]
        loans = [self._loan(record, index) for index, record in enumerate(loans_data)]

        self._ensure_unique("book", [book.id for book in books])
        self._ensure_unique("member", [member.id for member in members])
        self._ensure_unique("loan", [loan.id for loan in loans])
        self._validate_relationships(books, members, loans)
        return LibraryState(books, members, loans)

    @staticmethod
    def _record_list(data: dict[str, Any], name: str) -> list[Any]:
        if name not in data:
            raise InvalidDataError(f"Library data is missing '{name}'")
        records = data[name]
        if not isinstance(records, list):
            raise InvalidDataError(f"'{name}' must be a list")
        return records

    def _book(self, value: Any, index: int) -> Book:
        record = self._record(value, f"books[{index}]")
        return Book(
            self._text(record, "id", f"books[{index}]"),
            self._text(record, "title", f"books[{index}]"),
            self._text(record, "author", f"books[{index}]"),
            self._text(record, "category", f"books[{index}]"),
        )

    def _member(self, value: Any, index: int) -> Member:
        record = self._record(value, f"members[{index}]")
        return Member(
            self._text(record, "id", f"members[{index}]"),
            self._text(record, "name", f"members[{index}]"),
        )

    def _loan(self, value: Any, index: int) -> Loan:
        location = f"loans[{index}]"
        record = self._record(value, location)
        checkout_date = self._date(record, "checkout_date", location)
        due_date = self._date(record, "due_date", location)
        returned_date = self._optional_date(record, "returned_date", location)
        if due_date < checkout_date:
            raise InvalidDataError(f"{location}.due_date precedes checkout_date")
        if returned_date is not None and returned_date < checkout_date:
            raise InvalidDataError(f"{location}.returned_date precedes checkout_date")
        return Loan(
            self._text(record, "id", location),
            self._text(record, "book_id", location),
            self._text(record, "member_id", location),
            checkout_date,
            due_date,
            returned_date,
        )

    @staticmethod
    def _record(value: Any, location: str) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise InvalidDataError(f"{location} must be an object")
        return value

    @staticmethod
    def _text(record: dict[str, Any], key: str, location: str) -> str:
        value = record.get(key)
        if not isinstance(value, str) or not value.strip():
            raise InvalidDataError(f"{location}.{key} must be non-blank text")
        return value.strip()

    @staticmethod
    def _date(record: dict[str, Any], key: str, location: str) -> date:
        value = record.get(key)
        if not isinstance(value, str):
            raise InvalidDataError(f"{location}.{key} must be an ISO date")
        try:
            return date.fromisoformat(value)
        except ValueError as error:
            raise InvalidDataError(f"{location}.{key} must be an ISO date") from error

    def _optional_date(
        self, record: dict[str, Any], key: str, location: str
    ) -> date | None:
        if key not in record:
            raise InvalidDataError(f"{location} is missing '{key}'")
        if record[key] is None:
            return None
        return self._date(record, key, location)

    @staticmethod
    def _ensure_unique(kind: str, identifiers: list[str]) -> None:
        seen: set[str] = set()
        try:
            for identifier in identifiers:
                normalized = normalize_id(identifier)
                if normalized in seen:
                    raise InvalidDataError(f"Duplicate {kind} ID: {identifier}")
                seen.add(normalized)
        except IdentifierError as error:
            raise InvalidDataError(f"Invalid {kind} ID: {error}") from error

    @staticmethod
    def _validate_relationships(
        books: list[Book], members: list[Member], loans: list[Loan]
    ) -> None:
        book_ids = {normalize_id(book.id) for book in books}
        member_ids = {normalize_id(member.id) for member in members}
        active_books: set[str] = set()

        for loan in loans:
            if not loan.is_active:
                continue
            book_id = normalize_id(loan.book_id)
            member_id = normalize_id(loan.member_id)
            if book_id not in book_ids:
                raise InvalidDataError(
                    f"Active loan {loan.id} references unknown book {loan.book_id}"
                )
            if member_id not in member_ids:
                raise InvalidDataError(
                    f"Active loan {loan.id} references unknown member {loan.member_id}"
                )
            if book_id in active_books:
                raise InvalidDataError(f"Book {loan.book_id} has multiple active loans")
            active_books.add(book_id)
