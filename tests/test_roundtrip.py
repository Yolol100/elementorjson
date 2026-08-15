import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from compare_elementor_roundtrip import compare  # noqa: E402


class RoundtripTests(unittest.TestCase):
    def _compare(self, source, reexport):
        with tempfile.TemporaryDirectory() as directory:
            source_path = Path(directory) / "source.json"
            reexport_path = Path(directory) / "reexport.json"
            source_path.write_text(json.dumps(source), encoding="utf-8")
            reexport_path.write_text(json.dumps(reexport), encoding="utf-8")
            return compare(source_path, reexport_path)

    def test_generated_element_ids_are_ignored(self):
        source = {
            "title": "A",
            "type": "page",
            "version": "0.4",
            "page_settings": [],
            "content": [{"id": "source-id", "elType": "container", "settings": [], "elements": []}],
        }
        reexport = {
            "title": "Imported A",
            "type": "page",
            "version": "0.4",
            "page_settings": [],
            "content": [{"id": "new-id", "elType": "container", "settings": [], "elements": []}],
        }
        report = self._compare(source, reexport)
        self.assertEqual("pass", report["status"])
        self.assertTrue(report["semantic_equal"])

    def test_semantic_setting_change_fails(self):
        source = {
            "page_settings": [],
            "content": [{
                "id": "one", "elType": "widget", "widgetType": "heading",
                "settings": {"title": "Expected"}, "elements": []
            }],
        }
        reexport = {
            "page_settings": [],
            "content": [{
                "id": "two", "elType": "widget", "widgetType": "heading",
                "settings": {"title": "Changed"}, "elements": []
            }],
        }
        report = self._compare(source, reexport)
        self.assertEqual("fail", report["status"])
        self.assertFalse(report["semantic_equal"])
        self.assertTrue(report["diff"])

    def test_missing_content_fails_closed(self):
        report = self._compare({"page_settings": []}, {"page_settings": [], "content": []})
        self.assertEqual("fail", report["status"])
        self.assertTrue(report["errors"])


if __name__ == "__main__":
    unittest.main()
