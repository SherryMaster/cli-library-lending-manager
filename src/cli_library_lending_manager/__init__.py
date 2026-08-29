from .persistence import CorruptDataError, JsonStorage, StorageError
from .presentation import Menu, MenuItem

__all__ = [
    "CorruptDataError",
    "JsonStorage",
    "Menu",
    "MenuItem",
    "StorageError",
    "main",
]


def main() -> None:
    """Run the command-line application (backward-compatible entry point)."""
    from .presentation.cli import main as run_cli

    run_cli()
