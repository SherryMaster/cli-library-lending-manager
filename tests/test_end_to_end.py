import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from cli_library_lending_manager.application import ActiveLoanError, Library
from cli_library_lending_manager.persistence import JsonLibraryStore


class EndToEndLifecycleTests(unittest.TestCase):
    def test_complete_lifecycle_survives_multiple_restarts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data" / "library.json"
            store = JsonLibraryStore(path)
            library = Library(store.load(), on_change=store.save)

            dune = library.create_book("Dune", "Frank Herbert", "Science Fiction")
            hobbit = library.create_book("The Hobbit", "Tolkien", "Fantasy")
            foundation = library.create_book(
                "Foundation", "Isaac Asimov", "Science Fiction"
            )
            sara = library.create_member("Sara Khan")
            ali = library.create_member("Ali Ahmed")
            old_loan = library.create_loan(
                dune.id, sara.id, checkout_date=date(2026, 8, 1)
            )
            current_loan = library.create_loan(
                hobbit.id, ali.id, checkout_date=date(2026, 8, 20)
            )

            restarted = Library(store.load(), on_change=store.save)
            self.assertEqual(len(restarted.list_books()), 3)
            self.assertEqual(len(restarted.list_members()), 2)
            self.assertEqual(len(restarted.list_active_loans()), 2)
            self.assertEqual(
                restarted.list_overdue_loans(as_of=date(2026, 8, 31)),
                [old_loan],
            )

            restarted.return_loan(old_loan.id, returned_date=date(2026, 8, 31))
            restarted.remove_book(dune.id)
            with self.assertRaises(ActiveLoanError):
                restarted.remove_book(hobbit.id)
            with self.assertRaises(ActiveLoanError):
                restarted.remove_member(ali.id)

            final = Library(store.load(), on_change=store.save)
            self.assertEqual(final.list_books(), [foundation, hobbit])
            self.assertEqual(final.list_active_loans(), [current_loan])
            self.assertEqual(len(final.list_returned_loans()), 1)
            self.assertEqual(final.statistics(as_of=date(2026, 8, 31)).total_books, 2)

            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(set(saved), {"books", "members", "loans"})
            self.assertNotIn("is_available", json.dumps(saved))
            self.assertNotIn("is_overdue", json.dumps(saved))


if __name__ == "__main__":
    unittest.main()
