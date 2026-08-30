import unittest
from datetime import date, timedelta
from unittest.mock import patch

from cli_library_lending_manager.application import (
    BookAlreadyLoanedError,
    InvalidLoanDateError,
    Library,
    LoanAlreadyReturnedError,
)
from cli_library_lending_manager.domain import (
    DuplicateIdentifierError,
    UnknownIdentifierError,
)


class LoanLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.library = Library()
        self.book = self.library.add_book(
            "B001", "Dune", "Frank Herbert", "Science Fiction"
        )
        self.second_book = self.library.add_book(
            "B002", "The Hobbit", "Tolkien", "Fantasy"
        )
        self.member = self.library.add_member("M001", "Sara Khan")

    def test_checkout_creates_a_14_day_active_loan(self) -> None:
        checkout_date = date(2026, 8, 30)

        loan = self.library.checkout_book(
            " L001 ", " b001 ", " m001 ", checkout_date=checkout_date
        )

        self.assertEqual(loan.id, "L001")
        self.assertEqual(loan.book_id, self.book.id)
        self.assertEqual(loan.member_id, self.member.id)
        self.assertEqual(loan.checkout_date, checkout_date)
        self.assertEqual(loan.due_date, checkout_date + timedelta(days=14))
        self.assertIsNone(loan.returned_date)
        self.assertTrue(loan.is_active)

    def test_checkout_uses_today_when_no_date_is_supplied(self) -> None:
        today = date(2026, 8, 30)
        with patch(
            "cli_library_lending_manager.application.library.date"
        ) as mocked_date:
            mocked_date.today.return_value = today
            loan = self.library.checkout_book("L001", "B001", "M001")

        self.assertEqual(loan.checkout_date, today)
        self.assertEqual(loan.due_date, date(2026, 9, 13))

    def test_checkout_rejects_unknown_relationships_without_mutation(self) -> None:
        with self.assertRaises(UnknownIdentifierError):
            self.library.checkout_book("L001", "B999", "M001")
        with self.assertRaises(UnknownIdentifierError):
            self.library.checkout_book("L001", "B001", "M999")

        self.assertEqual(self.library.state.loans, [])

    def test_checkout_rejects_duplicate_loan_id_without_mutation(self) -> None:
        original = self.library.checkout_book(
            "L001", "B001", "M001", checkout_date=date(2026, 8, 30)
        )

        with self.assertRaises(DuplicateIdentifierError):
            self.library.checkout_book(
                " l001 ", "B002", "M001", checkout_date=date(2026, 8, 30)
            )

        self.assertEqual(self.library.state.loans, [original])

    def test_book_cannot_have_two_active_loans(self) -> None:
        original = self.library.checkout_book(
            "L001", "B001", "M001", checkout_date=date(2026, 8, 30)
        )

        with self.assertRaises(BookAlreadyLoanedError):
            self.library.checkout_book(
                "L002", "b001", "M001", checkout_date=date(2026, 8, 31)
            )

        self.assertEqual(self.library.state.loans, [original])

    def test_member_can_have_multiple_different_books(self) -> None:
        first = self.library.checkout_book(
            "L001", "B001", "M001", checkout_date=date(2026, 8, 30)
        )
        second = self.library.checkout_book(
            "L002", "B002", "M001", checkout_date=date(2026, 8, 30)
        )

        self.assertEqual(
            self.library.active_loans_for_member("m001"), [first, second]
        )

    def test_return_replaces_record_and_preserves_history(self) -> None:
        original = self.library.checkout_book(
            "L001", "B001", "M001", checkout_date=date(2026, 8, 30)
        )

        returned = self.library.return_loan(
            " l001 ", returned_date=date(2026, 9, 2)
        )

        self.assertIsNot(returned, original)
        self.assertEqual(returned.id, original.id)
        self.assertEqual(returned.book_id, original.book_id)
        self.assertEqual(returned.member_id, original.member_id)
        self.assertEqual(returned.checkout_date, original.checkout_date)
        self.assertEqual(returned.due_date, original.due_date)
        self.assertEqual(returned.returned_date, date(2026, 9, 2))
        self.assertFalse(returned.is_active)
        self.assertEqual(self.library.state.loans, [returned])

    def test_return_uses_today_when_no_date_is_supplied(self) -> None:
        self.library.checkout_book(
            "L001", "B001", "M001", checkout_date=date(2026, 8, 30)
        )
        today = date(2026, 9, 2)

        with patch(
            "cli_library_lending_manager.application.library.date"
        ) as mocked_date:
            mocked_date.today.return_value = today
            returned = self.library.return_loan("L001")

        self.assertEqual(returned.returned_date, today)

    def test_repeated_return_is_rejected_without_mutation(self) -> None:
        self.library.checkout_book(
            "L001", "B001", "M001", checkout_date=date(2026, 8, 30)
        )
        returned = self.library.return_loan(
            "L001", returned_date=date(2026, 9, 2)
        )

        with self.assertRaises(LoanAlreadyReturnedError):
            self.library.return_loan("L001", returned_date=date(2026, 9, 3))

        self.assertEqual(self.library.state.loans, [returned])

    def test_invalid_return_date_is_rejected_without_mutation(self) -> None:
        original = self.library.checkout_book(
            "L001", "B001", "M001", checkout_date=date(2026, 8, 30)
        )

        with self.assertRaises(InvalidLoanDateError):
            self.library.return_loan("L001", returned_date=date(2026, 8, 29))

        self.assertEqual(self.library.state.loans, [original])

    def test_unknown_loan_return_is_rejected(self) -> None:
        with self.assertRaises(UnknownIdentifierError):
            self.library.return_loan("L999", returned_date=date(2026, 8, 30))

    def test_availability_is_derived_from_active_loans(self) -> None:
        self.assertTrue(self.library.is_book_available("b001"))
        loan = self.library.checkout_book(
            "L001", "B001", "M001", checkout_date=date(2026, 8, 30)
        )

        self.assertFalse(self.library.is_book_available("B001"))
        self.assertIs(self.library.active_loan_for_book("b001"), loan)

        self.library.return_loan("L001", returned_date=date(2026, 9, 2))

        self.assertTrue(self.library.is_book_available("B001"))
        self.assertIsNone(self.library.active_loan_for_book("B001"))


if __name__ == "__main__":
    unittest.main()
