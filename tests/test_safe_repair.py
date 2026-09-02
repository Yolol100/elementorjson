import importlib.util
import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
SPEC = importlib.util.spec_from_file_location("repair_elementor_json", TOOLS / "repair_elementor_json.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class SafeRepairTests(unittest.TestCase):
    def inventory(self):
        return {
            "schema_version": "1.1",
            "environment": {
                "elementor": "4.2.4",
                "elementor_pro": "4.2.0",
                "active_devices": ["desktop", "tablet", "mobile"],
            },
            "widgets": {
                "heading": {
                    "owner": "elementor-core",
                    "controls": [
                        {"name": "title", "type": "text", "responsive": False, "responsive_devices": []},
                        {"name": "align", "type": "choose", "responsive": True, "responsive_devices": ["tablet", "mobile"]},
                    ],
                }
            },
        }

    def document(self, settings):
        return {
            "content": [
                {
                    "id": "abc123",
                    "elType": "widget",
                    "widgetType": "heading",
                    "settings": settings,
                    "elements": [],
                }
            ],
            "page_settings": [],
        }

    def test_removes_only_empty_unrecognized_setting(self):
        patched, report = MODULE.repair_document(
            self.document({"title": "Hello", "legacy_empty": ""}), self.inventory()
        )
        settings = patched["content"][0]["settings"]
        self.assertEqual({"title": "Hello"}, settings)
        self.assertEqual("changed", report["status"])
        self.assertEqual("EJL-SAFE-001", report["repairs"][0]["rule_id"])
        self.assertEqual([], report["blocked"])

    def test_preserves_nonempty_unknown_setting_and_blocks(self):
        patched, report = MODULE.repair_document(
            self.document({"title": "Hello", "legacy_unknown": "keep-me"}), self.inventory()
        )
        self.assertEqual("keep-me", patched["content"][0]["settings"]["legacy_unknown"])
        self.assertEqual("blocked", report["status"])
        self.assertEqual("nonempty_unrecognized_setting", report["blocked"][0]["code"])

    def test_preserves_supported_responsive_setting(self):
        patched, report = MODULE.repair_document(self.document({"align_tablet": "center"}), self.inventory())
        self.assertEqual("center", patched["content"][0]["settings"]["align_tablet"])
        self.assertEqual("no_change", report["status"])

    def test_never_substitutes_missing_widget(self):
        doc = self.document({})
        doc["content"][0]["widgetType"] = "not-installed"
        patched, report = MODULE.repair_document(doc, self.inventory())
        self.assertEqual("not-installed", patched["content"][0]["widgetType"])
        self.assertEqual("missing_widget_dependency", report["blocked"][0]["code"])


if __name__ == "__main__":
    unittest.main()
