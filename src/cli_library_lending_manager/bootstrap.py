"""Composition root where application dependencies are connected."""

from cli_library_lending_manager.application import Library
from cli_library_lending_manager.presentation.library_cli import LibraryCLI
from cli_library_lending_manager.presentation.menu_manager import Menu


def create_main_menu() -> Menu:
    """Create one in-memory library and connect it to the terminal UI."""
    return LibraryCLI(Library()).create_main_menu()
