import unittest
from datetime import date

from cli_library_lending_manager.application import Library


class GeneratedIdentifierTests(unittest.TestCase):
    def test_application_generates_readable_entity_ids(self) -> None:
        library = Library()

        first_book = library.create_book("Dune", "Frank Herbert", "Fiction")
        second_book = library.create_book("The Hobbit", "Tolkien", "Fantasy")
        first_member = library.create_member("Sara Khan")
        second_member = library.create_member("Ali Ahmed")
        first_loan = library.create_loan(
            first_book.id, first_member.id, checkout_date=date(2026, 8, 30)
        )
        second_loan = library.create_loan(
            second_book.id, second_member.id, checkout_date=date(2026, 8, 30)
        )

        self.assertEqual((first_book.id, second_book.id), ("B001", "B002"))
        self.assertEqual((first_member.id, second_member.id), ("M001", "M002"))
        self.assertEqual((first_loan.id, second_loan.id), ("L001", "L002"))

    def test_removed_historical_references_are_not_reused(self) -> None:
        library = Library()
        book = library.create_book("Dune", "Frank Herbert", "Fiction")
        member = library.create_member("Sara Khan")
        loan = library.create_loan(
            book.id, member.id, checkout_date=date(2026, 8, 30)
        )
        library.return_loan(loan.id, returned_date=date(2026, 9, 1))
        library.remove_book(book.id)
        library.remove_member(member.id)

        new_book = library.create_book("The Hobbit", "Tolkien", "Fantasy")
        new_member = library.create_member("Ali Ahmed")

        self.assertEqual(new_book.id, "B002")
        self.assertEqual(new_member.id, "M002")


if __name__ == "__main__":
    unittest.main()
