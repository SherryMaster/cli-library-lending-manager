import unittest
from datetime import date

from cli_library_lending_manager.domain import Book, LibraryState, Loan, Member


class DomainModelTests(unittest.TestCase):
    def test_state_owns_all_canonical_record_types(self) -> None:
        book = Book("B001", "Dune", "Frank Herbert", "Science Fiction")
        member = Member("M001", "Sara Khan")
        loan = Loan(
            "L001",
            book.id,
            member.id,
            date(2026, 8, 29),
            date(2026, 9, 12),
        )

        state = LibraryState([book], [member], [loan])

        self.assertEqual(state.books, [book])
        self.assertEqual(state.members, [member])
        self.assertEqual(state.loans, [loan])

    def test_return_status_is_derived_from_returned_date(self) -> None:
        active = Loan(
            "L001", "B001", "M001", date(2026, 8, 29), date(2026, 9, 12)
        )
        returned = Loan(
            "L002",
            "B002",
            "M001",
            date(2026, 8, 1),
            date(2026, 8, 15),
            returned_date=date(2026, 8, 10),
        )

        self.assertTrue(active.is_active)
        self.assertFalse(returned.is_active)

    def test_empty_states_do_not_share_collections(self) -> None:
        first = LibraryState()
        second = LibraryState()

        first.books.append(Book("B001", "Dune", "Frank Herbert", "Fiction"))

        self.assertEqual(second.books, [])


if __name__ == "__main__":
    unittest.main()
