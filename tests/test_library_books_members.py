import unittest
from datetime import date

from cli_library_lending_manager.application import (
    ActiveLoanError,
    BlankFieldError,
    Library,
)
from cli_library_lending_manager.domain import (
    BlankIdentifierError,
    DuplicateIdentifierError,
    LibraryState,
    Loan,
    UnknownIdentifierError,
)


class LibraryBookMemberTests(unittest.TestCase):
    def setUp(self) -> None:
        self.library = Library()
        self.book = self.library.add_book(
            "B001", "Dune", "Frank Herbert", "Science Fiction"
        )
        self.member = self.library.add_member("M001", "Sara Khan")

    def test_add_trims_book_and_member_fields(self) -> None:
        book = self.library.add_book(
            " B002 ", " The Hobbit ", " Tolkien ", " Fantasy "
        )
        member = self.library.add_member(" M002 ", " Ali Ahmed ")

        self.assertEqual(
            (book.id, book.title, book.author, book.category),
            ("B002", "The Hobbit", "Tolkien", "Fantasy"),
        )
        self.assertEqual((member.id, member.name), ("M002", "Ali Ahmed"))

    def test_add_rejects_blank_required_fields_without_mutating_state(self) -> None:
        original_books = self.library.list_books()
        original_members = self.library.list_members()

        with self.assertRaises(BlankFieldError):
            self.library.add_book("B002", " ", "Author", "Category")
        with self.assertRaises(BlankFieldError):
            self.library.add_member("M002", " ")

        self.assertEqual(self.library.list_books(), original_books)
        self.assertEqual(self.library.list_members(), original_members)

    def test_add_rejects_blank_and_equivalent_duplicate_ids(self) -> None:
        with self.assertRaises(BlankIdentifierError):
            self.library.add_book(" ", "Title", "Author", "Category")
        with self.assertRaises(DuplicateIdentifierError):
            self.library.add_book(" b001 ", "Other", "Author", "Category")
        with self.assertRaises(DuplicateIdentifierError):
            self.library.add_member("m001", "Someone Else")

        self.assertEqual(len(self.library.list_books()), 1)
        self.assertEqual(len(self.library.list_members()), 1)

    def test_exact_lookup_reuses_stable_id_rules(self) -> None:
        self.assertIs(self.library.get_book(" b001 "), self.book)
        self.assertIs(self.library.get_member("m001"), self.member)

        with self.assertRaises(UnknownIdentifierError):
            self.library.get_member("M999")

    def test_list_methods_return_copies(self) -> None:
        books = self.library.list_books()
        members = self.library.list_members()
        books.clear()
        members.clear()

        self.assertEqual(self.library.list_books(), [self.book])
        self.assertEqual(self.library.list_members(), [self.member])

    def test_search_is_partial_case_insensitive_and_descriptive(self) -> None:
        fantasy_book = self.library.add_book(
            "B002", "The Hobbit", "Tolkien", "Fantasy"
        )
        self.library.add_member("M002", "Ali Ahmed")

        self.assertEqual(self.library.search_books("HERB"), [self.book])
        self.assertEqual(self.library.search_books("fant"), [fantasy_book])
        self.assertEqual(self.library.search_members("sara"), [self.member])
        self.assertEqual(self.library.search_members("missing"), [])

    def test_update_replaces_records_but_preserves_ids(self) -> None:
        updated_book = self.library.update_book(
            "b001", title=" Dune Messiah ", author="Frank Herbert", category="SF"
        )
        updated_member = self.library.update_member("m001", name=" Sara Ahmed ")

        self.assertEqual(updated_book.id, "B001")
        self.assertEqual(updated_book.title, "Dune Messiah")
        self.assertEqual(updated_member.id, "M001")
        self.assertEqual(updated_member.name, "Sara Ahmed")
        self.assertIsNot(updated_book, self.book)
        self.assertIsNot(updated_member, self.member)

    def test_failed_update_does_not_change_the_existing_record(self) -> None:
        with self.assertRaises(BlankFieldError):
            self.library.update_book(
                "B001", title="New Title", author=" ", category="Fiction"
            )

        self.assertIs(self.library.get_book("B001"), self.book)

    def test_remove_book_and_member_without_active_loans(self) -> None:
        removed_book = self.library.remove_book("b001")
        removed_member = self.library.remove_member("m001")

        self.assertIs(removed_book, self.book)
        self.assertIs(removed_member, self.member)
        self.assertEqual(self.library.list_books(), [])
        self.assertEqual(self.library.list_members(), [])

    def test_active_loan_blocks_removal_without_mutating_state(self) -> None:
        loan = Loan(
            "L001",
            self.book.id,
            self.member.id,
            date(2026, 8, 30),
            date(2026, 9, 13),
        )
        self.library.state.loans.append(loan)

        with self.assertRaises(ActiveLoanError):
            self.library.remove_book("B001")
        with self.assertRaises(ActiveLoanError):
            self.library.remove_member("M001")

        self.assertEqual(self.library.list_books(), [self.book])
        self.assertEqual(self.library.list_members(), [self.member])
        self.assertEqual(self.library.state.loans, [loan])

    def test_returned_history_does_not_block_removal_or_get_deleted(self) -> None:
        loan = Loan(
            "L001",
            self.book.id,
            self.member.id,
            date(2026, 8, 1),
            date(2026, 8, 15),
            returned_date=date(2026, 8, 10),
        )
        self.library.state.loans.append(loan)

        self.library.remove_book("B001")
        self.library.remove_member("M001")

        self.assertEqual(self.library.state.loans, [loan])

    def test_library_uses_supplied_state_or_creates_an_empty_one(self) -> None:
        supplied = LibraryState()

        self.assertIs(Library(supplied).state, supplied)
        self.assertEqual(Library().state, LibraryState())


if __name__ == "__main__":
    unittest.main()
