import tempfile
import unittest
from pathlib import Path

from cli_library_lending_manager.application import Storage
from cli_library_lending_manager.persistence import JsonStorage


def round_trip(storage: Storage, data: object) -> object:
    """Use only the operations promised by the Storage interface."""
    storage.save(data)
    return storage.load()


class ApplicationPortTests(unittest.TestCase):
    def test_json_storage_satisfies_the_storage_interface(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            storage = JsonStorage(Path(directory) / "library.json")

            result = round_trip(storage, {"books": []})

            self.assertEqual(result, {"books": []})


if __name__ == "__main__":
    unittest.main()
