import unittest
from unittest.mock import patch

from cli_library_lending_manager.application import Library
from cli_library_lending_manager.presentation.library_cli import LibraryCLI


class FakeTerminal:
    def __init__(self, responses: list[str]) -> None:
        self.responses = iter(responses)
        self.output: list[str] = []

    def input(self, prompt: str) -> str:
        return next(self.responses)

    def print(self, message: str) -> None:
        self.output.append(message)


class LibraryCLITests(unittest.TestCase):
    def test_main_menu_exposes_current_features(self) -> None:
        cli = LibraryCLI(Library())

        names = [item.name for item in cli.create_main_menu().get_items()]

        self.assertEqual(names, ["Books", "Members", "Loans", "Exit"])

    def test_user_can_add_entities_checkout_and_return_without_typing_ids(self) -> None:
        terminal = FakeTerminal(
            ["Dune", "Frank Herbert", "Science Fiction", "", "Sara Khan", "", "", ""]
        )
        library = Library()
        cli = LibraryCLI(library, input_fn=terminal.input, output_fn=terminal.print)

        cli.add_book()
        cli.add_member()
        book = library.list_books()[0]
        member = library.list_members()[0]
        cli.checkout_book(book, member)
        loan = library.list_active_loans()[0]
        cli.return_loan(loan)

        self.assertEqual(book.id, "B001")
        self.assertEqual(member.id, "M001")
        self.assertEqual(loan.id, "L001")
        self.assertFalse(library.get_loan("L001").is_active)
        self.assertTrue(any("Checked out Dune" in line for line in terminal.output))

    def test_book_choices_show_names_instead_of_requiring_ids(self) -> None:
        library = Library()
        library.create_book("Dune", "Frank Herbert", "Science Fiction")
        library.create_book("The Hobbit", "Tolkien", "Fantasy")
        cli = LibraryCLI(library)

        with patch(
            "cli_library_lending_manager.presentation.library_cli.Menu"
        ) as menu_class:
            cli.choose_book_to_update()

        items = menu_class.call_args.args[1]
        self.assertEqual(
            [item.name for item in items],
            ["Dune — Frank Herbert", "The Hobbit — Tolkien", "Back"],
        )

    def test_empty_selection_menu_is_readable(self) -> None:
        terminal = FakeTerminal([""])
        cli = LibraryCLI(Library(), input_fn=terminal.input, output_fn=terminal.print)

        cli.browse_books()

        self.assertEqual(terminal.output, ["No books found."])


if __name__ == "__main__":
    unittest.main()
