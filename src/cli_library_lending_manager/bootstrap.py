"""Composition root where application dependencies are connected."""

from pathlib import Path

from cli_library_lending_manager.application import Library
from cli_library_lending_manager.persistence import JsonLibraryStore
from cli_library_lending_manager.presentation.library_cli import LibraryCLI
from cli_library_lending_manager.presentation.menu_manager import Menu

DEFAULT_DATA_PATH = Path("data") / "library.json"


def create_main_menu(
    *, data_path: Path = DEFAULT_DATA_PATH, temporary: bool = False
) -> Menu:
    """Load the library and connect persistence to the terminal UI."""
    if temporary:
        library = Library()
        backup = None
    else:
        store = JsonLibraryStore(data_path)
        library = Library(store.load(), on_change=store.save)
        backup = lambda: store.backup(library.state)
    return LibraryCLI(library, backup_fn=backup).create_main_menu()
