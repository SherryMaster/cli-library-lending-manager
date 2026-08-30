"""Interfaces required by application operations."""

from typing import Any, Protocol


class Storage(Protocol):
    """Anything capable of loading and saving application data."""

    def load(self) -> Any: ...

    def save(self, data: Any) -> None: ...
