import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build", ROOT / "build.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class DatabasePersistenceTests(unittest.TestCase):
    def test_merge_database_items_keeps_history_and_appends_new_entries(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "database.json"
            existing = [
                {
                    "headline": "Existing item",
                    "url": "https://example.com/old",
                    "source": "Example",
                    "published": "2024-01-01",
                    "summary": "Old summary",
                    "practiceArea": "Pricing",
                    "businessLine": "Commercial Insurance",
                    "itemType": "Article",
                    "section": "actuarial",
                    "sortOrder": 1,
                    "firstSeen": "2024-01-01",
                    "lastSeen": "2024-01-01",
                    "seenIn": ["2024-01-01"],
                }
            ]
            build.write_database_file(existing, db_path)

            new_items = [
                {
                    "headline": "New item",
                    "url": "https://example.com/new",
                    "source": "Example",
                    "published": "2026-07-28",
                    "summary": "New summary",
                    "practiceArea": "AI/ML/Deep Learning",
                    "businessLine": None,
                    "itemType": "Research",
                    "section": "data_science",
                    "sortOrder": 2,
                    "firstSeen": "2026-07-28",
                    "lastSeen": "2026-07-28",
                    "seenIn": ["2026-07-28"],
                }
            ]
            merged = build.merge_database_items(existing, new_items)

            self.assertEqual(len(merged), 2)
            self.assertEqual(merged[0]["headline"], "Existing item")
            self.assertEqual(merged[1]["headline"], "New item")


if __name__ == "__main__":
    unittest.main()
