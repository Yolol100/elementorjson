import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from compare_elementor_roundtrip import compare  # noqa: E402


class RoundtripComparisonTests(unittest.TestCase):
    def _compare(self, source, roundtrip, allow_added=None):
        with tempfile.TemporaryDirectory() as directory:
            source_path = Path(directory) / "source.json"
            roundtrip_path = Path(directory) / "roundtrip.json"
            source_path.write_text(json.dumps(source), encoding="utf-8")
            roundtrip_path.write_text(json.dumps(roundtrip), encoding="utf-8")
            return compare(source_path, roundtrip_path, allow_added or [])

    @staticmethod
    def _document(element_id="abc1234"):
        return {
            "title": "Roundtrip",
            "type": "page",
            "version": "0.4",
            "page_settings": [],
            "content": [
                {
                    "id": element_id,
                    "elType": "widget",
                    "widgetType": "heading",
                    "isInner": False,
                    "settings": {"title": "Hello"},
                    "elements": [],
                }
            ],
        }

    def test_only_element_ids_are_volatile(self):
        report = self._compare(self._document("source-id"), self._document("new-id"))
        self.assertEqual("pass", report["status"])

    def test_content_change_fails(self):
        source = self._document()
        target = self._document()
        target["content"][0]["settings"]["title"] = "Changed"
        report = self._compare(source, target)
        self.assertEqual("fail", report["status"])
        self.assertTrue(any(item["kind"] == "changed" for item in report["differences"]))

    def test_style_ids_are_not_volatile(self):
        source = self._document()
        target = self._document()
        source["content"][0]["styles"] = [{"id": "style-a", "type": "class", "variants": []}]
        target["content"][0]["styles"] = [{"id": "style-b", "type": "class", "variants": []}]
        report = self._compare(source, target)
        self.assertEqual("fail", report["status"])

    def test_repeater_ids_are_not_volatile(self):
        source = self._document()
        target = self._document()
        source["content"][0]["settings"]["items"] = [{"_id": "rep-a", "text": "A"}]
        target["content"][0]["settings"]["items"] = [{"_id": "rep-b", "text": "A"}]
        report = self._compare(source, target)
        self.assertEqual("fail", report["status"])

    def test_target_added_data_fails_by_default(self):
        source = self._document()
        target = self._document()
        target["content"][0]["settings"]["new_default"] = "x"
        report = self._compare(source, target)
        self.assertEqual("fail", report["status"])
        self.assertTrue(any(item["kind"] == "added" for item in report["differences"]))

    def test_explicit_added_path_allowlist_is_supported(self):
        source = self._document()
        target = self._document()
        target["content"][0]["settings"]["new_default"] = "x"
        report = self._compare(source, target, ["$.content[0].settings.new_default"])
        self.assertEqual("pass", report["status"])

    def test_empty_settings_object_and_array_are_semantically_equal(self):
        source = self._document()
        target = self._document()
        source["content"][0]["settings"] = []
        target["content"][0]["settings"] = {}
        report = self._compare(source, target)
        self.assertEqual("pass", report["status"])


if __name__ == "__main__":
    unittest.main()
