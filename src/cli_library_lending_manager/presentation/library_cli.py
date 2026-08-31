"""Terminal menus and prompts for the complete library application."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from cli_library_lending_manager.application import Library
from cli_library_lending_manager.domain import Book, Loan, Member
from cli_library_lending_manager.persistence import StorageError

from .menu_manager import Menu, MenuItem

PAGE_SIZE = 8


class LibraryCLI:
    """Translate friendly terminal interaction into application operations."""

    def __init__(
        self,
        library: Library,
        *,
        backup_fn: Callable[[], Path] | None = None,
        input_fn: Callable[[str], str] = input,
        output_fn: Callable[[str], None] = print,
    ) -> None:
        self.library = library
        self._backup_fn = backup_fn
        self._input = input_fn
        self._output = output_fn

    def create_main_menu(self) -> Menu:
        return Menu(
            "Library Lending Manager",
            [
                MenuItem(self._dashboard_label, self.show_dashboard, "Library summary"),
                MenuItem("Books", self.open_books_menu, "Manage and explore books"),
                MenuItem("Members", self.open_members_menu, "Manage members"),
                MenuItem("Loans", self.open_loans_menu, "Checkout, returns, and history"),
                MenuItem("Export backup", self.export_backup, "Create a timestamped JSON copy"),
                MenuItem("Exit", description="Close the application", close_on_select=True),
            ],
        )

    def open_books_menu(self) -> None:
        Menu(
            "Books",
            [
                MenuItem("Add book", self.add_book),
                MenuItem("Browse all", self.browse_books),
                MenuItem("Available books", self.browse_available_books),
                MenuItem("Books on loan", self.browse_books_on_loan),
                MenuItem("Search", self.search_books),
                MenuItem("Sort and filter", self.open_book_filters),
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
                MenuItem("Browse all", self.browse_members),
                MenuItem("Search", self.search_members),
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
                MenuItem("Overdue loans", self.browse_overdue_loans),
                MenuItem("Returned loans", self.browse_returned_loans),
                MenuItem("Complete history", self.browse_loan_history),
                MenuItem("Back", close_on_select=True),
            ],
        ).run()

    def show_dashboard(self) -> None:
        stats = self.library.statistics()
        self._output("Library summary")
        self._output(f"Books: {stats.total_books}")
        self._output(f"Members: {stats.total_members}")
        self._output(f"Active loans: {stats.active_loans}")
        self._output(f"Overdue loans: {stats.overdue_loans}")
        self._output(f"Total loan history: {stats.historical_loans}")
        if stats.overdue_loans:
            self._output("Attention: overdue loans need review.")
        self._pause()

    def _dashboard_label(self) -> str:
        stats = self.library.statistics()
        return f"Dashboard — {stats.total_books} books · {stats.active_loans} active"

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
        self._open_book_menu("All books", self.library.list_books(), self.show_book)

    def browse_available_books(self) -> None:
        self._open_book_menu(
            "Available books", self.library.list_available_books(), self.show_book
        )

    def browse_books_on_loan(self) -> None:
        self._open_book_menu(
            "Books on loan", self.library.list_books_on_loan(), self.show_book
        )

    def search_books(self) -> None:
        books = self.library.search_books(self._input("Search text: "))
        self._open_book_menu("Book search results", books, self.show_book)

    def open_book_filters(self) -> None:
        Menu(
            "Sort and filter books",
            [
                MenuItem("By title", self.browse_books),
                MenuItem("By author", self.browse_books_by_author),
                MenuItem("By category", self.choose_category),
                MenuItem("Available only", self.browse_available_books),
                MenuItem("On loan only", self.browse_books_on_loan),
                MenuItem("Back", close_on_select=True),
            ],
        ).run()

    def browse_books_by_author(self) -> None:
        self._open_book_menu(
            "Books by author", self.library.books_sorted_by_author(), self.show_book
        )

    def choose_category(self) -> None:
        categories = self.library.list_categories()
        if not categories:
            self._empty("No categories found.")
            return
        Menu(
            "Choose a category",
            [
                *[
                    MenuItem(
                        category,
                        lambda selected=category: self.browse_category(selected),
                    )
                    for category in categories
                ],
                MenuItem("Back", close_on_select=True),
            ],
        ).run()

    def browse_category(self, category: str) -> None:
        self._open_book_menu(
            category, self.library.books_in_category(category), self.show_book
        )

    def choose_book_to_update(self) -> None:
        self._open_book_menu(
            "Choose a book to update", self.library.list_books(), self.update_book
        )

    def update_book(self, book: Book) -> None:
        try:
            updated = self.library.update_book(
                book.id,
                title=self._input(f"New title [{book.title}]: ") or book.title,
                author=self._input(f"New author [{book.author}]: ") or book.author,
                category=self._input(f"New category [{book.category}]: ")
                or book.category,
            )
            self._output(f"Updated book {updated.id}: {updated.title}")
        except (ValueError, StorageError) as error:
            self._output(f"Could not update book: {error}")
        self._pause()

    def choose_book_to_remove(self) -> None:
        self._open_book_menu(
            "Choose a book to remove", self.library.list_books(), self.remove_book
        )

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
        self._open_member_menu(
            "All members", self.library.list_members(), self.show_member
        )

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
                member.id,
                name=self._input(f"New name [{member.name}]: ") or member.name,
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
        self._open_book_menu(
            "Choose an available book",
            self.library.list_available_books(),
            self.choose_borrower,
        )

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
        self._open_loan_menu(
            "Active loans", self.library.list_active_loans(), self.show_loan
        )

    def browse_overdue_loans(self) -> None:
        self._open_loan_menu(
            "Overdue loans", self.library.list_overdue_loans(), self.show_loan
        )

    def browse_returned_loans(self) -> None:
        self._open_loan_menu(
            "Returned loans", self.library.list_returned_loans(), self.show_loan
        )

    def browse_loan_history(self) -> None:
        self._open_loan_menu("Loan history", self.library.list_loans(), self.show_loan)

    def show_book(self, book: Book) -> None:
        self._output(f"ID: {book.id}")
        self._output(f"Title: {book.title}")
        self._output(f"Author: {book.author}")
        self._output(f"Category: {book.category}")
        active = self.library.active_loan_for_book(book.id)
        if active is None:
            self._output("Status: Available")
        else:
            member = self.library.get_member(active.member_id)
            self._output(f"Status: On loan to {member.name}")
            self._output(f"Due: {active.due_date} ({self.library.loan_due_status(active)})")
        history = self.library.loans_for_book(book.id)
        self._output(f"Loan history: {len(history)}")
        for loan in history:
            self._output(f"  {self._loan_label(loan)} · {self.library.loan_due_status(loan)}")
        self._pause()

    def show_member(self, member: Member) -> None:
        self._output(f"ID: {member.id}")
        self._output(f"Name: {member.name}")
        history = self.library.loans_for_member(member.id)
        active = [loan for loan in history if loan.is_active]
        self._output(f"Active loans: {len(active)}")
        self._output(f"Total borrowing history: {len(history)}")
        for loan in history:
            self._output(f"  {self._loan_label(loan)} · {self.library.loan_due_status(loan)}")
        self._pause()

    def show_loan(self, loan: Loan) -> None:
        self._output(f"ID: {loan.id}")
        self._output(f"Book / member: {self._loan_label(loan)}")
        self._output(f"Checkout: {loan.checkout_date}")
        self._output(f"Due: {loan.due_date}")
        self._output(f"Status: {self.library.loan_due_status(loan)}")
        self._pause()

    def export_backup(self) -> None:
        if self._backup_fn is None:
            self._output("Backup is unavailable in a temporary unsaved session.")
            self._pause()
            return
        try:
            destination = self._backup_fn()
            self._output(f"Backup created: {destination}")
        except StorageError as error:
            self._output(f"Could not create backup: {error}")
        self._pause()

    def _open_book_menu(
        self, title: str, books: list[Book], action: Callable[[Book], None]
    ) -> None:
        self._open_paged_menu(
            title,
            books,
            "No books found.",
            lambda book: MenuItem(
                f"{book.title} — {book.author}",
                lambda selected=book: action(selected),
                f"{book.category} · {book.id} · "
                f"{'Available' if self.library.is_book_available(book.id) else 'On loan'}",
            ),
        )

    def _open_member_menu(
        self, title: str, members: list[Member], action: Callable[[Member], None]
    ) -> None:
        self._open_paged_menu(
            title,
            members,
            "No members found.",
            lambda member: MenuItem(
                member.name,
                lambda selected=member: action(selected),
                f"{member.id} · {len(self.library.active_loans_for_member(member.id))} active",
            ),
        )

    def _open_loan_menu(
        self, title: str, loans: list[Loan], action: Callable[[Loan], None]
    ) -> None:
        self._open_paged_menu(
            title,
            loans,
            "No loans found.",
            lambda loan: MenuItem(
                self._loan_label(loan),
                lambda selected=loan: action(selected),
                f"{self.library.loan_due_status(loan)} · {loan.id}",
            ),
        )

    def _open_paged_menu(
        self,
        title: str,
        values: list[Any],
        empty_message: str,
        item_builder: Callable[[Any], MenuItem],
    ) -> None:
        if not values:
            self._empty(empty_message)
            return

        page = 0
        total_pages = (len(values) + PAGE_SIZE - 1) // PAGE_SIZE
        while True:
            movement = 0
            menu: Menu

            def previous_page() -> None:
                nonlocal movement
                movement = -1
                menu.close()

            def next_page() -> None:
                nonlocal movement
                movement = 1
                menu.close()

            start = page * PAGE_SIZE
            items = [item_builder(value) for value in values[start : start + PAGE_SIZE]]
            if page > 0:
                items.append(MenuItem("← Previous page", previous_page))
            if page < total_pages - 1:
                items.append(MenuItem("Next page →", next_page))
            items.append(MenuItem("Back", close_on_select=True))
            menu = Menu(f"{title} · Page {page + 1}/{total_pages}", items)
            menu.run()
            if movement == 0:
                return
            page += movement

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

    def _empty(self, message: str) -> None:
        self._output(message)
        self._pause()

    def _confirm(self, prompt: str) -> bool:
        return self._input(prompt).strip().casefold() == "y"

    def _pause(self) -> None:
        self._input("Press Enter to continue...")
