"""Command-line entry point."""

from cli_library_lending_manager.bootstrap import create_main_menu


def main() -> None:
    """Build and run the terminal application."""
    create_main_menu().run()
