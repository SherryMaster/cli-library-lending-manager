import json
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path

from cli_library_lending_manager.application import Library
from cli_library_lending_manager.domain import Book, LibraryState, Loan, Member
from cli_library_lending_manager.persistence import (
    CorruptDataError,
    InvalidDataError,
    JsonLibraryStore,
)


class JsonLibraryStoreTests(unittest.TestCase):
    def test_missing_file_loads_an_empty_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = JsonLibraryStore(Path(directory) / "nested" / "library.json")

            self.assertEqual(store.load(), LibraryState())

    def test_complete_state_round_trips_with_iso_dates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "library.json"
            store = JsonLibraryStore(path)
            state = LibraryState(
                [Book("B001", "Dune", "Frank Herbert", "Fiction")],
                [Member("M001", "Sara Khan")],
                [
                    Loan(
                        "L001",
                        "B001",
                        "M001",
                        date(2026, 8, 30),
                        date(2026, 9, 13),
                        date(2026, 9, 2),
                    )
                ],
            )

            store.save(state)

            self.assertEqual(store.load(), state)
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(saved["loans"][0]["checkout_date"], "2026-08-30")
            self.assertNotIn("is_available", saved["books"][0])
            self.assertNotIn("is_active", saved["loans"][0])

    def test_successful_mutations_persist_across_restart(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = JsonLibraryStore(Path(directory) / "library.json")
            library = Library(store.load(), on_change=store.save)
            book = library.create_book("Dune", "Frank Herbert", "Fiction")
            member = library.create_member("Sara Khan")
            loan = library.create_loan(
                book.id, member.id, checkout_date=date(2026, 8, 30)
            )
            library.return_loan(loan.id, returned_date=date(2026, 9, 2))

            restarted = Library(store.load(), on_change=store.save)

            self.assertEqual(restarted.list_books(), library.list_books())
            self.assertEqual(restarted.list_members(), library.list_members())
            self.assertEqual(restarted.list_loans(), library.list_loans())

    def test_failed_save_rolls_back_the_in_memory_mutation(self) -> None:
        def fail_to_save(state: LibraryState) -> None:
            raise OSError("disk unavailable")

        library = Library(on_change=fail_to_save)

        with self.assertRaises(OSError):
            library.create_book("Dune", "Frank Herbert", "Fiction")

        self.assertEqual(library.state, LibraryState())

    def test_backup_exports_state_without_changing_canonical_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "library.json"
            store = JsonLibraryStore(path)
            state = LibraryState(
                [Book("B001", "Dune", "Frank Herbert", "Fiction")], [], []
            )
            store.save(state)
            canonical_before = path.read_text(encoding="utf-8")

            backup = store.backup(
                state, now=datetime(2026, 8, 31, 12, 30, 45)
            )

            self.assertEqual(
                backup.name, "library-backup-20260831-123045.json"
            )
            self.assertEqual(JsonLibraryStore(backup).load(), state)
            self.assertEqual(path.read_text(encoding="utf-8"), canonical_before)

    def test_invalid_top_level_shapes_are_rejected(self) -> None:
        invalid_values = [
            [],
            {},
            {"books": {}, "members": [], "loans": []},
            {"books": ["not an object"], "members": [], "loans": []},
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "library.json"
            store = JsonLibraryStore(path)
            for value in invalid_values:
                with self.subTest(value=value):
                    path.write_text(json.dumps(value), encoding="utf-8")
                    with self.assertRaises(InvalidDataError):
                        store.load()

    def test_invalid_records_dates_and_duplicates_are_rejected(self) -> None:
        base = {
            "books": [
                {"id": "B001", "title": "Dune", "author": "Herbert", "category": "Fiction"}
            ],
            "members": [{"id": "M001", "name": "Sara"}],
            "loans": [],
        }
        invalid_values = [
            {**base, "books": [*base["books"], {**base["books"][0], "id": "b001"}]},
            {**base, "members": [{"id": "M001", "name": "   "}]},
            {
                **base,
                "loans": [
                    {
                        "id": "L001",
                        "book_id": "B001",
                        "member_id": "M001",
                        "checkout_date": "not-a-date",
                        "due_date": "2026-09-13",
                        "returned_date": None,
                    }
                ],
            },
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "library.json"
            store = JsonLibraryStore(path)
            for value in invalid_values:
                with self.subTest(value=value):
                    path.write_text(json.dumps(value), encoding="utf-8")
                    with self.assertRaises(InvalidDataError):
                        store.load()

    def test_active_relationship_invariants_are_validated(self) -> None:
        loan = {
            "id": "L001",
            "book_id": "B001",
            "member_id": "M001",
            "checkout_date": "2026-08-30",
            "due_date": "2026-09-13",
            "returned_date": None,
        }
        base = {
            "books": [{"id": "B001", "title": "Dune", "author": "Herbert", "category": "Fiction"}],
            "members": [{"id": "M001", "name": "Sara"}],
            "loans": [loan],
        }
        invalid_values = [
            {**base, "books": []},
            {**base, "members": []},
            {**base, "loans": [loan, {**loan, "id": "L002"}]},
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "library.json"
            store = JsonLibraryStore(path)
            for value in invalid_values:
                with self.subTest(value=value):
                    path.write_text(json.dumps(value), encoding="utf-8")
                    with self.assertRaises(InvalidDataError):
                        store.load()

    def test_malformed_json_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "library.json"
            original = "{broken"
            path.write_text(original, encoding="utf-8")

            with self.assertRaises(CorruptDataError):
                JsonLibraryStore(path).load()

            self.assertEqual(path.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
