"""Command-line entry point."""

from cli_library_lending_manager.persistence import StorageError

from cli_library_lending_manager.bootstrap import create_main_menu


def main() -> None:
    """Build and run the terminal application."""
    try:
        menu = create_main_menu()
    except StorageError as error:
        print(f"Could not load the saved library: {error}")
        print("The existing data file has not been changed.")
        choice = input("Start a temporary session without saving? [y/N]: ")
        if choice.strip().casefold() != "y":
            return
        menu = create_main_menu(temporary=True)
    menu.run()
