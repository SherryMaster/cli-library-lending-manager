import unittest
from datetime import date

from cli_library_lending_manager.domain import (
    BlankIdentifierError,
    Book,
    DuplicateIdentifierError,
    LibraryState,
    Loan,
    Member,
    UnknownIdentifierError,
    ensure_unique_id,
    ids_match,
    normalize_id,
)


class IdentifierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.book = Book("B001", "Dune", "Frank Herbert", "Science Fiction")
        self.member = Member("M001", "Sara Khan")
        self.loan = Loan(
            "L001",
            self.book.id,
            self.member.id,
            date(2026, 8, 30),
            date(2026, 9, 13),
        )
        self.state = LibraryState([self.book], [self.member], [self.loan])

    def test_normalization_trims_and_ignores_case(self) -> None:
        self.assertEqual(normalize_id(" B001 "), "b001")
        self.assertTrue(ids_match("B001", " b001 "))

    def test_blank_identifier_is_rejected(self) -> None:
        with self.assertRaises(BlankIdentifierError):
            normalize_id("   ")

    def test_equivalent_duplicate_is_rejected(self) -> None:
        with self.assertRaises(DuplicateIdentifierError):
            ensure_unique_id(" b001 ", [book.id for book in self.state.books])

    def test_different_identifier_is_allowed(self) -> None:
        ensure_unique_id("B002", [book.id for book in self.state.books])

    def test_state_uses_the_shared_rule_for_all_exact_lookups(self) -> None:
        self.assertIs(self.state.get_book(" b001 "), self.book)
        self.assertIs(self.state.get_member("m001"), self.member)
        self.assertIs(self.state.get_loan("l001"), self.loan)

    def test_unknown_identifier_is_rejected(self) -> None:
        with self.assertRaises(UnknownIdentifierError):
            self.state.get_book("B999")


if __name__ == "__main__":
    unittest.main()
