"""Persistence adapters for application data."""

from .json_storage import CorruptDataError, JsonStorage, StorageError

__all__ = ["CorruptDataError", "JsonStorage", "StorageError"]
