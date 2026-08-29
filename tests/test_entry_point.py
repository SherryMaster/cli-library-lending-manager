import unittest
from unittest.mock import Mock, patch

from cli_library_lending_manager.presentation.cli import main


class EntryPointTests(unittest.TestCase):
    @patch("cli_library_lending_manager.presentation.cli.create_main_menu")
    def test_main_builds_and_runs_the_application(self, create_main_menu: Mock) -> None:
        menu = create_main_menu.return_value

        main()

        create_main_menu.assert_called_once_with()
        menu.run.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
