import unittest
from datetime import date

from cli_library_lending_manager.application import Library, LibraryStatistics


class ViewAndStatisticsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.library = Library()
        self.dune = self.library.add_book(
            "B002", "Dune", "Frank Herbert", "Science Fiction"
        )
        self.hobbit = self.library.add_book(
            "B001", "The Hobbit", "Tolkien", "Fantasy"
        )
        self.foundation = self.library.add_book(
            "B003", "Foundation", "Isaac Asimov", "Science Fiction"
        )
        self.sara = self.library.add_member("M002", "Sara Khan")
        self.ali = self.library.add_member("M001", "Ali Ahmed")

        self.overdue = self.library.checkout_book(
            "L002", "B002", "M002", checkout_date=date(2026, 8, 1)
        )
        returned = self.library.checkout_book(
            "L001", "B001", "M001", checkout_date=date(2026, 8, 10)
        )
        self.returned = self.library.return_loan(
            returned.id, returned_date=date(2026, 8, 15)
        )

    def test_major_views_have_deterministic_ordering(self) -> None:
        self.assertEqual(
            self.library.list_books(), [self.dune, self.foundation, self.hobbit]
        )
        self.assertEqual(self.library.list_members(), [self.ali, self.sara])
        self.assertEqual(self.library.list_loans(), [self.returned, self.overdue])
        self.assertEqual(self.library.list_available_books(), [self.foundation, self.hobbit])
        self.assertEqual(self.library.list_books_on_loan(), [self.dune])

    def test_loan_filters_and_relationship_history(self) -> None:
        self.assertEqual(self.library.list_active_loans(), [self.overdue])
        self.assertEqual(self.library.list_returned_loans(), [self.returned])
        self.assertEqual(
            self.library.list_overdue_loans(as_of=date(2026, 8, 31)),
            [self.overdue],
        )
        self.assertEqual(self.library.loans_for_book("b002"), [self.overdue])
        self.assertEqual(self.library.loans_for_member("m002"), [self.overdue])

    def test_categories_author_sort_and_statistics_are_derived(self) -> None:
        self.assertEqual(
            self.library.list_categories(), ["Fantasy", "Science Fiction"]
        )
        self.assertEqual(
            self.library.books_in_category("science fiction"),
            [self.dune, self.foundation],
        )
        self.assertEqual(
            self.library.books_sorted_by_author(),
            [self.dune, self.foundation, self.hobbit],
        )
        self.assertEqual(
            self.library.statistics(as_of=date(2026, 8, 31)),
            LibraryStatistics(3, 2, 1, 1, 2),
        )

    def test_due_status_handles_boundaries(self) -> None:
        as_of = date(2026, 8, 31)
        self.assertEqual(
            self.library.loan_due_status(self.overdue, as_of=as_of),
            "Overdue by 16 days",
        )
        due_today = self.library.create_loan(
            self.foundation.id, self.ali.id, checkout_date=date(2026, 8, 17)
        )
        self.assertEqual(
            self.library.loan_due_status(due_today, as_of=as_of), "Due today"
        )
        self.assertEqual(
            self.library.loan_due_status(self.returned, as_of=as_of),
            "Returned 2026-08-15",
        )


if __name__ == "__main__":
    unittest.main()
