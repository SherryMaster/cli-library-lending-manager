"""Composition root where application dependencies are connected."""

from cli_library_lending_manager.presentation.menu_manager import Menu, MenuItem


def create_main_menu() -> Menu:
    """Create the initial CLI shell without embedding domain rules in the UI."""
    return Menu(
        "Library Lending Manager",
        [MenuItem("Exit", description="Close the application", close_on_select=True)],
    )
