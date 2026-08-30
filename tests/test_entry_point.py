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

    @patch("builtins.input", return_value="y")
    @patch("builtins.print")
    @patch("cli_library_lending_manager.presentation.cli.create_main_menu")
    def test_storage_failure_can_start_temporary_unsaved_session(
        self, create_main_menu: Mock, output: Mock, user_input: Mock
    ) -> None:
        from cli_library_lending_manager.persistence import InvalidDataError

        temporary_menu = Mock()
        create_main_menu.side_effect = [
            InvalidDataError("bad library data"),
            temporary_menu,
        ]

        main()

        self.assertEqual(
            create_main_menu.call_args_list,
            [unittest.mock.call(), unittest.mock.call(temporary=True)],
        )
        temporary_menu.run.assert_called_once_with()
        user_input.assert_called_once()
        self.assertTrue(output.called)


if __name__ == "__main__":
    unittest.main()
