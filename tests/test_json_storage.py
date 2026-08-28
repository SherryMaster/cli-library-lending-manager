import tempfile
import unittest
from pathlib import Path

from cli_library_lending_manager.json_storage import CorruptDataError, JsonStorage


class JsonStorageTests(unittest.TestCase):
    def test_missing_file_returns_an_independent_default(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            storage = JsonStorage(Path(directory) / "data.json", {"items": []})
            first = storage.load()
            first["items"].append("changed")
            self.assertEqual(storage.load(), {"items": []})

    def test_round_trip_creates_parent_directories(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            storage = JsonStorage(Path(directory) / "nested" / "data.json")
            data = {"title": "Library", "books": [1, 2]}
            storage.save(data)
            self.assertTrue(storage.exists())
            self.assertEqual(storage.load(), data)

    def test_invalid_json_raises_specific_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.json"
            path.write_text("{broken", encoding="utf-8")
            with self.assertRaises(CorruptDataError):
                JsonStorage(path).load()


if __name__ == "__main__":
    unittest.main()
