import unittest

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

    def test_user_can_add_entities_checkout_and_return(self) -> None:
        terminal = FakeTerminal(
            [
                "B001", "Dune", "Frank Herbert", "Science Fiction", "",
                "M001", "Sara Khan", "",
                "L001", "B001", "M001", "",
                "L001", "",
            ]
        )
        library = Library()
        cli = LibraryCLI(
            library, input_fn=terminal.input, output_fn=terminal.print
        )

        cli.add_book()
        cli.add_member()
        cli.checkout_book()
        cli.return_loan()

        self.assertEqual(library.get_book("B001").title, "Dune")
        self.assertEqual(library.get_member("M001").name, "Sara Khan")
        self.assertFalse(library.get_loan("L001").is_active)
        self.assertTrue(any("Checked out B001" in line for line in terminal.output))
        self.assertTrue(any("Returned loan L001" in line for line in terminal.output))

    def test_invalid_input_reports_error_and_returns_control(self) -> None:
        terminal = FakeTerminal(["B999", ""])
        cli = LibraryCLI(
            Library(), input_fn=terminal.input, output_fn=terminal.print
        )

        cli.return_loan()

        self.assertTrue(terminal.output[0].startswith("Could not return loan:"))

    def test_empty_views_are_readable(self) -> None:
        terminal = FakeTerminal(["", "", ""])
        cli = LibraryCLI(
            Library(), input_fn=terminal.input, output_fn=terminal.print
        )

        cli.list_books()
        cli.list_members()
        cli.list_active_loans()

        self.assertEqual(
            terminal.output,
            ["No books found.", "No members found.", "No loans found."],
        )


if __name__ == "__main__":
    unittest.main()
