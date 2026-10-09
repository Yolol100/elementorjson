import copy
import json
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


    def _atomic_smoke_source(self):
        return json.loads((ROOT / "templates" / "smoke-atomic.json").read_text(encoding="utf-8"))

    def test_atomic_empty_importer_omissions_are_equivalent(self):
        source = self._atomic_smoke_source()
        imported = copy.deepcopy(source)
        for element in [imported["content"][0], *imported["content"][0]["elements"]]:
            for key in ("editor_settings", "interactions", "styles"):
                self.assertEqual([], element.pop(key))
            if element.get("settings") == []:
                element.pop("settings")
            element["id"] = "imported-" + element["id"]
        report = compare(source, imported)
        self.assertEqual("pass", report["status"], report["differences"])
        self.assertEqual(report["semantic_fingerprints"]["source"], report["semantic_fingerprints"]["imported"])

    def test_atomic_nonempty_content_and_custom_fields_remain_strict(self):
        base = self._atomic_smoke_source()
        cases = [
            ("interactions", [{"event": "click"}]),
            ("styles", [{"id": "keep", "variants": []}]),
            ("editor_settings", {"custom": True}),
            ("settings", {"custom": {"$type": "string", "value": "important"}}),
        ]
        for key, value in cases:
            with self.subTest(key=key):
                source = copy.deepcopy(base)
                imported = copy.deepcopy(base)
                source["content"][0][key] = value
                imported["content"][0].pop(key)
                report = compare(source, imported)
                self.assertEqual("fail", report["status"], report["differences"])
                self.assertIn(f"$.content[0].{key}", [d["path"] for d in report["differences"]])

    def test_classic_and_unknown_empty_fields_are_not_suppressed(self):
        base = self._atomic_smoke_source()
        source = copy.deepcopy(base)
        imported = copy.deepcopy(base)
        source["content"][0]["unexpected_empty_field"] = []
        self.assertEqual("fail", compare(source, imported)["status"])

        classic = {
            "content": [{"elType": "widget", "widgetType": "heading", "id": "a", "settings": {"title": "A"}, "editor_settings": []}],
            "page_settings": [],
        }
        imported_classic = copy.deepcopy(classic)
        imported_classic["content"][0].pop("editor_settings")
        report = compare(classic, imported_classic)
        self.assertEqual("fail", report["status"])
        self.assertEqual("$.content[0].editor_settings", report["differences"][0]["path"])



if __name__ == "__main__":
    unittest.main()
