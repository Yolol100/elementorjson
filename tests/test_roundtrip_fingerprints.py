import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from compare_elementor_roundtrip import compare  # noqa: E402


class RoundtripFingerprintTests(unittest.TestCase):
    def test_equivalent_import_has_same_semantic_fingerprint(self):
        source = {
            "content": [{"id": "source-id", "elType": "widget", "widgetType": "heading", "settings": {"title": "Hallo"}}],
            "page_settings": [],
        }
        imported = {
            "content": [{"id": "new-id", "elType": "widget", "widgetType": "heading", "settings": {"title": "Hallo", "selected_icon": {}}}],
            "page_settings": [],
        }
        report = compare(source, imported)
        self.assertEqual("pass", report["status"])
        self.assertEqual(report["semantic_fingerprints"]["source"], report["semantic_fingerprints"]["imported"])

    def test_semantic_change_changes_fingerprint(self):
        source = {"content": [{"id": "a", "elType": "widget", "settings": {"title": "A"}}], "page_settings": []}
        imported = {"content": [{"id": "b", "elType": "widget", "settings": {"title": "B"}}], "page_settings": []}
        report = compare(source, imported)
        self.assertEqual("fail", report["status"])
        self.assertNotEqual(report["semantic_fingerprints"]["source"], report["semantic_fingerprints"]["imported"])


if __name__ == "__main__":
    unittest.main()
