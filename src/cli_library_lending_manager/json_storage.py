"""Small, reliable JSON-file storage for application data."""

from __future__ import annotations

import copy
import json
import os
import tempfile
from pathlib import Path
from typing import Any


class StorageError(Exception):
    """Raised when data cannot be read from or written to storage."""


class CorruptDataError(StorageError):
    """Raised when a storage file does not contain valid JSON."""


class JsonStorage:
    """Persist JSON-compatible data in a file.

    Writes use a temporary file in the destination directory followed by an
    atomic replacement, so an interrupted save cannot leave a partial file.
    """

    def __init__(self, filepath: str | Path, default_data: Any = None) -> None:
        self.file_path = Path(filepath)
        self.default_data = default_data

    def exists(self) -> bool:
        return self.file_path.is_file()

    def save(self, data: Any) -> None:
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            file_descriptor, temporary_name = tempfile.mkstemp(
                dir=self.file_path.parent,
                prefix=f".{self.file_path.name}.",
                suffix=".tmp",
                text=True,
            )
        except OSError as error:
            raise StorageError(f"Could not prepare storage file: {self.file_path}") from error

        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(file_descriptor, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
                file.write("\n")
                file.flush()
                os.fsync(file.fileno())
            temporary_path.replace(self.file_path)
        except (OSError, TypeError, ValueError) as error:
            raise StorageError(f"Could not save JSON data to: {self.file_path}") from error
        finally:
            temporary_path.unlink(missing_ok=True)

    def load(self) -> Any:
        if not self.file_path.exists():
            return copy.deepcopy(self.default_data)

        try:
            with self.file_path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise CorruptDataError(
                f"Storage file contains invalid JSON: {self.file_path}"
            ) from error
        except OSError as error:
            raise StorageError(f"Could not read storage file: {self.file_path}") from error
