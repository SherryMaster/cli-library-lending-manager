from .json_storage import CorruptDataError, JsonStorage, StorageError
from .menu_manager import Menu, MenuItem

__all__ = [
    "CorruptDataError",
    "JsonStorage",
    "Menu",
    "MenuItem",
    "StorageError",
    "main",
]


def main() -> None:
    print("Hello from cli-library-lending-manager!")
