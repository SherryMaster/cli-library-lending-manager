import unittest

from readchar import key

from cli_library_lending_manager.presentation.menu_manager import (
    Menu,
    MenuItem,
    resolve_text,
)


class MenuManagerTests(unittest.TestCase):
    def test_arrow_navigation_wraps_and_enter_executes(self) -> None:
        calls: list[str] = []
        inputs = iter([key.UP, key.ENTER])
        menu = Menu(
            "Test",
            [MenuItem("First"), MenuItem("Second", lambda: calls.append("second"))],
            key_reader=lambda: next(inputs),
            screen_clearer=lambda: None,
        )
        menu._visible_items = menu.get_items()
        menu.handle_input()
        menu.handle_input()
        self.assertEqual(calls, ["second"])

    def test_menu_item_passes_arguments_to_action(self) -> None:
        calls: list[str] = []
        MenuItem("Save", calls.append, args=("saved",)).execute()
        self.assertEqual(calls, ["saved"])

    def test_dynamic_text_and_items_are_resolved_lazily(self) -> None:
        state = {"name": "Books"}
        menu = Menu("Test", lambda: [MenuItem(lambda: state["name"])])
        self.assertEqual(resolve_text(menu.get_items()[0].name), "Books")
        state["name"] = "Members"
        self.assertEqual(resolve_text(menu.get_items()[0].name), "Members")


if __name__ == "__main__":
    unittest.main()
