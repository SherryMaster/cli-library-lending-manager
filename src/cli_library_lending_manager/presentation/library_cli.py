"""Terminal menus and prompts for library operations."""

from __future__ import annotations

from collections.abc import Callable

from cli_library_lending_manager.application import Library
from cli_library_lending_manager.domain import Book, Loan, Member
from cli_library_lending_manager.persistence import StorageError

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
                MenuItem("Browse books", self.browse_books),
                MenuItem("Search books", self.search_books),
                MenuItem("Update book", self.choose_book_to_update),
                MenuItem("Remove book", self.choose_book_to_remove),
                MenuItem("Back", close_on_select=True),
            ],
        ).run()

    def open_members_menu(self) -> None:
        Menu(
            "Members",
            [
                MenuItem("Add member", self.add_member),
                MenuItem("Browse members", self.browse_members),
                MenuItem("Search members", self.search_members),
                MenuItem("Update member", self.choose_member_to_update),
                MenuItem("Remove member", self.choose_member_to_remove),
                MenuItem("Back", close_on_select=True),
            ],
        ).run()

    def open_loans_menu(self) -> None:
        Menu(
            "Loans",
            [
                MenuItem("Check out book", self.choose_book_to_checkout),
                MenuItem("Return loan", self.choose_loan_to_return),
                MenuItem("Active loans", self.browse_active_loans),
                MenuItem("Loan history", self.browse_loan_history),
                MenuItem("Back", close_on_select=True),
            ],
        ).run()

    def add_book(self) -> None:
        try:
            book = self.library.create_book(
                self._input("Title: "),
                self._input("Author: "),
                self._input("Category: "),
            )
            self._output(f"Added book {book.id}: {book.title}")
        except (ValueError, StorageError) as error:
            self._output(f"Could not add book: {error}")
        self._pause()

    def add_member(self) -> None:
        try:
            member = self.library.create_member(self._input("Name: "))
            self._output(f"Added member {member.id}: {member.name}")
        except (ValueError, StorageError) as error:
            self._output(f"Could not add member: {error}")
        self._pause()

    def browse_books(self) -> None:
        self._open_book_menu("Browse books", self.library.list_books(), self.show_book)

    def search_books(self) -> None:
        books = self.library.search_books(self._input("Search text: "))
        self._open_book_menu("Book search results", books, self.show_book)

    def choose_book_to_update(self) -> None:
        self._open_book_menu("Choose a book to update", self.library.list_books(), self.update_book)

    def update_book(self, book: Book) -> None:
        try:
            updated = self.library.update_book(
                book.id,
                title=self._input(f"New title [{book.title}]: ") or book.title,
                author=self._input(f"New author [{book.author}]: ") or book.author,
                category=self._input(f"New category [{book.category}]: ") or book.category,
            )
            self._output(f"Updated book {updated.id}: {updated.title}")
        except (ValueError, StorageError) as error:
            self._output(f"Could not update book: {error}")
        self._pause()

    def choose_book_to_remove(self) -> None:
        self._open_book_menu("Choose a book to remove", self.library.list_books(), self.remove_book)

    def remove_book(self, book: Book) -> None:
        if not self._confirm(f"Remove {book.title}? [y/N]: "):
            self._output("Removal cancelled.")
            self._pause()
            return
        try:
            removed = self.library.remove_book(book.id)
            self._output(f"Removed book {removed.id}: {removed.title}")
        except (ValueError, StorageError) as error:
            self._output(f"Could not remove book: {error}")
        self._pause()

    def browse_members(self) -> None:
        self._open_member_menu("Browse members", self.library.list_members(), self.show_member)

    def search_members(self) -> None:
        members = self.library.search_members(self._input("Search text: "))
        self._open_member_menu("Member search results", members, self.show_member)

    def choose_member_to_update(self) -> None:
        self._open_member_menu(
            "Choose a member to update", self.library.list_members(), self.update_member
        )

    def update_member(self, member: Member) -> None:
        try:
            updated = self.library.update_member(
                member.id, name=self._input(f"New name [{member.name}]: ") or member.name
            )
            self._output(f"Updated member {updated.id}: {updated.name}")
        except (ValueError, StorageError) as error:
            self._output(f"Could not update member: {error}")
        self._pause()

    def choose_member_to_remove(self) -> None:
        self._open_member_menu(
            "Choose a member to remove", self.library.list_members(), self.remove_member
        )

    def remove_member(self, member: Member) -> None:
        if not self._confirm(f"Remove {member.name}? [y/N]: "):
            self._output("Removal cancelled.")
            self._pause()
            return
        try:
            removed = self.library.remove_member(member.id)
            self._output(f"Removed member {removed.id}: {removed.name}")
        except (ValueError, StorageError) as error:
            self._output(f"Could not remove member: {error}")
        self._pause()

    def choose_book_to_checkout(self) -> None:
        available = [
            book
            for book in self.library.list_books()
            if self.library.is_book_available(book.id)
        ]
        self._open_book_menu("Choose an available book", available, self.choose_borrower)

    def choose_borrower(self, book: Book) -> None:
        self._open_member_menu(
            f"Who is borrowing {book.title}?",
            self.library.list_members(),
            lambda member: self.checkout_book(book, member),
        )

    def checkout_book(self, book: Book, member: Member) -> None:
        try:
            loan = self.library.create_loan(book.id, member.id)
            self._output(
                f"Checked out {book.title} to {member.name}; due {loan.due_date}"
            )
        except (ValueError, StorageError) as error:
            self._output(f"Could not check out book: {error}")
        self._pause()

    def choose_loan_to_return(self) -> None:
        self._open_loan_menu(
            "Choose a loan to return", self.library.list_active_loans(), self.return_loan
        )

    def return_loan(self, loan: Loan) -> None:
        try:
            returned = self.library.return_loan(loan.id)
            self._output(f"Returned loan {returned.id} on {returned.returned_date}")
        except (ValueError, StorageError) as error:
            self._output(f"Could not return loan: {error}")
        self._pause()

    def browse_active_loans(self) -> None:
        self._open_loan_menu("Active loans", self.library.list_active_loans(), self.show_loan)

    def browse_loan_history(self) -> None:
        self._open_loan_menu("Loan history", self.library.list_loans(), self.show_loan)

    def show_book(self, book: Book) -> None:
        status = "Available" if self.library.is_book_available(book.id) else "On loan"
        self._output(f"ID: {book.id}")
        self._output(f"Title: {book.title}")
        self._output(f"Author: {book.author}")
        self._output(f"Category: {book.category}")
        self._output(f"Status: {status}")
        self._pause()

    def show_member(self, member: Member) -> None:
        self._output(f"ID: {member.id}")
        self._output(f"Name: {member.name}")
        self._output(f"Active loans: {len(self.library.active_loans_for_member(member.id))}")
        self._pause()

    def show_loan(self, loan: Loan) -> None:
        status = "Active" if loan.is_active else f"Returned {loan.returned_date}"
        self._output(f"ID: {loan.id}")
        self._output(f"Book: {loan.book_id}")
        self._output(f"Member: {loan.member_id}")
        self._output(f"Checkout: {loan.checkout_date}")
        self._output(f"Due: {loan.due_date}")
        self._output(f"Status: {status}")
        self._pause()

    def _open_book_menu(
        self, title: str, books: list[Book], action: Callable[[Book], None]
    ) -> None:
        if not books:
            self._output("No books found.")
            self._pause()
            return
        items = [
            MenuItem(
                f"{book.title} — {book.author}",
                lambda selected=book: action(selected),
                f"{book.category} · {book.id}",
            )
            for book in books
        ]
        items.append(MenuItem("Back", close_on_select=True))
        Menu(title, items).run()

    def _open_member_menu(
        self, title: str, members: list[Member], action: Callable[[Member], None]
    ) -> None:
        if not members:
            self._output("No members found.")
            self._pause()
            return
        items = [
            MenuItem(
                member.name,
                lambda selected=member: action(selected),
                member.id,
            )
            for member in members
        ]
        items.append(MenuItem("Back", close_on_select=True))
        Menu(title, items).run()

    def _open_loan_menu(
        self, title: str, loans: list[Loan], action: Callable[[Loan], None]
    ) -> None:
        if not loans:
            self._output("No loans found.")
            self._pause()
            return
        items = [
            MenuItem(
                self._loan_label(loan),
                lambda selected=loan: action(selected),
                f"Due {loan.due_date} · {loan.id}",
            )
            for loan in loans
        ]
        items.append(MenuItem("Back", close_on_select=True))
        Menu(title, items).run()

    def _loan_label(self, loan: Loan) -> str:
        try:
            book = self.library.get_book(loan.book_id).title
        except ValueError:
            book = loan.book_id
        try:
            member = self.library.get_member(loan.member_id).name
        except ValueError:
            member = loan.member_id
        return f"{book} → {member}"

    def _confirm(self, prompt: str) -> bool:
        return self._input(prompt).strip().casefold() == "y"

    def _pause(self) -> None:
        self._input("Press Enter to continue...")
