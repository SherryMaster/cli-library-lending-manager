"""Compatibility imports for the JSON persistence API."""

from .persistence.json_storage import CorruptDataError, JsonStorage, StorageError

__all__ = ["CorruptDataError", "JsonStorage", "StorageError"]
