"""Reusable arrow-key menus for command-line applications."""

from __future__ import annotations

import os
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any, TypeAlias

from readchar import key, readkey

TextValue: TypeAlias = str | Callable[[], object]
Action: TypeAlias = Callable[..., Any]
ItemSource: TypeAlias = Iterable["MenuItem"] | Callable[[], Iterable["MenuItem"]]


def clear_screen() -> None:
    """Clear the active terminal on Windows, macOS, or Linux."""
    os.system("cls" if os.name == "nt" else "clear")


def resolve_text(value: TextValue) -> str:
    """Return live text from a callback, or stringify a static value."""
    return str(value() if callable(value) else value)


@dataclass(slots=True)
class MenuItem:
    name: TextValue
    action: Action | None = None
    description: TextValue = ""
    close_on_select: bool = False
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] = field(default_factory=dict)

    def display(self, index: int, focused: bool) -> None:
        print(f"{'>>' if focused else '  '} {index}) {resolve_text(self.name)}")

    def execute(self) -> Any:
        if self.action is None:
            return None
        return self.action(*self.args, **self.kwargs)


class Menu:
    """An interactive menu controlled with arrow keys and Enter."""

    def __init__(
        self,
        title: TextValue,
        items: ItemSource | None = None,
        *,
        key_reader: Callable[[], str] = readkey,
        screen_clearer: Callable[[], None] = clear_screen,
    ) -> None:
        self.title = title
        self.items: ItemSource = [] if items is None else items
        self.footer = "↑/↓ Navigate • Enter Select • Q Back/Quit"
        self.current_item = 0
        self.is_running = False
        self._visible_items: list[MenuItem] = []
        self._key_reader = key_reader
        self._screen_clearer = screen_clearer

    def get_items(self) -> list[MenuItem]:
        """Resolve a dynamic item provider or copy the static items."""
        return list(self.items() if callable(self.items) else self.items)

    @classmethod
    def confirm(
        cls,
        title: TextValue,
        on_confirm: Action,
        confirm_description: TextValue = "Confirm",
        cancel_description: TextValue = "Cancel",
        **menu_options: Any,
    ) -> None:
        """Open a Yes/No submenu that closes after either selection."""
        cls(
            title,
            [
                MenuItem("Yes", on_confirm, confirm_description, close_on_select=True),
                MenuItem("No", description=cancel_description, close_on_select=True),
            ],
            **menu_options,
        ).run()

    def display(self) -> None:
        self._screen_clearer()
        self._visible_items = self.get_items()
        if self._visible_items:
            self.current_item = min(self.current_item, len(self._visible_items) - 1)
        else:
            self.current_item = 0

        title = resolve_text(self.title)
        print(title)
        print("-" * len(title))
        print()

        for index, item in enumerate(self._visible_items, start=1):
            item.display(index, index - 1 == self.current_item)

        print()
        if self._visible_items:
            print(resolve_text(self._visible_items[self.current_item].description))
        else:
            print("No options available.")
        print()
        print(self.footer)

    def handle_input(self) -> None:
        entered_key = self._key_reader()
        if entered_key == key.DOWN and self._visible_items:
            self.current_item = (self.current_item + 1) % len(self._visible_items)
        elif entered_key == key.UP and self._visible_items:
            self.current_item = (self.current_item - 1) % len(self._visible_items)
        elif entered_key == key.ENTER and self._visible_items:
            selected_item = self._visible_items[self.current_item]
            selected_item.execute()
            if selected_item.close_on_select:
                self.close()
        elif entered_key.casefold() == "q":
            self.close()

    def run(self) -> None:
        self.is_running = True
        while self.is_running:
            self.display()
            self.handle_input()

    def close(self) -> None:
        self.is_running = False

    def add_menu_item(self, item: MenuItem) -> None:
        if callable(self.items):
            raise TypeError("Cannot append to a menu that uses a dynamic item provider")
        if not isinstance(self.items, list):
            self.items = list(self.items)
        self.items.append(item)
