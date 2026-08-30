"""Terminal menus and prompts for library operations."""

from __future__ import annotations

from collections.abc import Callable

from cli_library_lending_manager.application import Library
from cli_library_lending_manager.domain import Book, Loan, Member

from .menu_manager import Menu, MenuItem


class LibraryCLI:
    """Translate terminal interaction into calls to the Library application."""

    def __init__(
        self,
        library: Library,
        *,
        input_fn: Callable[[str], str] = input,
        output_fn: Callable[[str], None] = print,
    ) -> None:
        self.library = library
        self._input = input_fn
        self._output = output_fn

    def create_main_menu(self) -> Menu:
        return Menu(
            "Library Lending Manager",
            [
                MenuItem("Books", self.open_books_menu, "Manage library books"),
                MenuItem("Members", self.open_members_menu, "Manage members"),
                MenuItem("Loans", self.open_loans_menu, "Check out and return books"),
                MenuItem("Exit", description="Close the application", close_on_select=True),
            ],
        )

    def open_books_menu(self) -> None:
        Menu(
            "Books",
            [
                MenuItem("Add book", self.add_book),
                MenuItem("List books", self.list_books),
                MenuItem("Search books", self.search_books),
                MenuItem("Update book", self.update_book),
                MenuItem("Remove book", self.remove_book),
                MenuItem("Back", close_on_select=True),
            ],
        ).run()

    def open_members_menu(self) -> None:
        Menu(
            "Members",
            [
                MenuItem("Add member", self.add_member),
                MenuItem("List members", self.list_members),
                MenuItem("Search members", self.search_members),
                MenuItem("Update member", self.update_member),
                MenuItem("Remove member", self.remove_member),
                MenuItem("Back", close_on_select=True),
            ],
        ).run()

    def open_loans_menu(self) -> None:
        Menu(
            "Loans",
            [
                MenuItem("Check out book", self.checkout_book),
                MenuItem("Return loan", self.return_loan),
                MenuItem("Active loans", self.list_active_loans),
                MenuItem("Loan history", self.list_loan_history),
                MenuItem("Back", close_on_select=True),
            ],
        ).run()

    def add_book(self) -> None:
        try:
            book = self.library.add_book(
                self._input("Book ID: "),
                self._input("Title: "),
                self._input("Author: "),
                self._input("Category: "),
            )
            self._output(f"Added book {book.id}: {book.title}")
        except ValueError as error:
            self._output(f"Could not add book: {error}")
        self._pause()

    def list_books(self) -> None:
        self._show_books(self.library.list_books())
        self._pause()

    def search_books(self) -> None:
        books = self.library.search_books(self._input("Search text: "))
        self._show_books(books)
        self._pause()

    def update_book(self) -> None:
        try:
            book = self.library.update_book(
                self._input("Book ID: "),
                title=self._input("New title: "),
                author=self._input("New author: "),
                category=self._input("New category: "),
            )
            self._output(f"Updated book {book.id}: {book.title}")
        except ValueError as error:
            self._output(f"Could not update book: {error}")
        self._pause()

    def remove_book(self) -> None:
        book_id = self._input("Book ID: ")
        if not self._confirm("Remove this book? [y/N]: "):
            self._output("Removal cancelled.")
            self._pause()
            return
        try:
            book = self.library.remove_book(book_id)
            self._output(f"Removed book {book.id}: {book.title}")
        except ValueError as error:
            self._output(f"Could not remove book: {error}")
        self._pause()

    def add_member(self) -> None:
        try:
            member = self.library.add_member(
                self._input("Member ID: "), self._input("Name: ")
            )
            self._output(f"Added member {member.id}: {member.name}")
        except ValueError as error:
            self._output(f"Could not add member: {error}")
        self._pause()

    def list_members(self) -> None:
        self._show_members(self.library.list_members())
        self._pause()

    def search_members(self) -> None:
        members = self.library.search_members(self._input("Search text: "))
        self._show_members(members)
        self._pause()

    def update_member(self) -> None:
        try:
            member = self.library.update_member(
                self._input("Member ID: "), name=self._input("New name: ")
            )
            self._output(f"Updated member {member.id}: {member.name}")
        except ValueError as error:
            self._output(f"Could not update member: {error}")
        self._pause()

    def remove_member(self) -> None:
        member_id = self._input("Member ID: ")
        if not self._confirm("Remove this member? [y/N]: "):
            self._output("Removal cancelled.")
            self._pause()
            return
        try:
            member = self.library.remove_member(member_id)
            self._output(f"Removed member {member.id}: {member.name}")
        except ValueError as error:
            self._output(f"Could not remove member: {error}")
        self._pause()

    def checkout_book(self) -> None:
        try:
            loan = self.library.checkout_book(
                self._input("Loan ID: "),
                self._input("Book ID: "),
                self._input("Member ID: "),
            )
            self._output(
                f"Checked out {loan.book_id} to {loan.member_id}; due {loan.due_date}"
            )
        except ValueError as error:
            self._output(f"Could not check out book: {error}")
        self._pause()

    def return_loan(self) -> None:
        try:
            loan = self.library.return_loan(self._input("Loan ID: "))
            self._output(f"Returned loan {loan.id} on {loan.returned_date}")
        except ValueError as error:
            self._output(f"Could not return loan: {error}")
        self._pause()

    def list_active_loans(self) -> None:
        self._show_loans(self.library.list_active_loans())
        self._pause()

    def list_loan_history(self) -> None:
        self._show_loans(self.library.list_loans())
        self._pause()

    def _show_books(self, books: list[Book]) -> None:
        if not books:
            self._output("No books found.")
            return
        for book in books:
            status = "Available" if self.library.is_book_available(book.id) else "On loan"
            self._output(
                f"{book.id} | {book.title} | {book.author} | {book.category} | {status}"
            )

    def _show_members(self, members: list[Member]) -> None:
        if not members:
            self._output("No members found.")
            return
        for member in members:
            self._output(f"{member.id} | {member.name}")

    def _show_loans(self, loans: list[Loan]) -> None:
        if not loans:
            self._output("No loans found.")
            return
        for loan in loans:
            status = "Active" if loan.is_active else f"Returned {loan.returned_date}"
            self._output(
                f"{loan.id} | Book {loan.book_id} | Member {loan.member_id} | "
                f"Due {loan.due_date} | {status}"
            )

    def _confirm(self, prompt: str) -> bool:
        return self._input(prompt).strip().casefold() == "y"

    def _pause(self) -> None:
        self._input("Press Enter to continue...")
