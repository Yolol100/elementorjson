import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from audit_elementor_json import audit  # noqa: E402


class AuditElementorJsonTests(unittest.TestCase):
    def setUp(self):
        self.fixture = ROOT / "tests" / "fixtures" / "classic-heading.json"

    def test_classifies_classic_template(self):
        report = audit(self.fixture, None)
        self.assertEqual("pass", report["status"])
        self.assertEqual("classic", report["document"]["editor_family"])
        self.assertEqual(1, report["summary"]["widgets"])

    def test_matches_widget_and_control_inventory(self):
        inventory = {
            "schema_version": "1.0",
            "environment": {"elementor": "test"},
            "widgets": {
                "heading": {
                    "title": "Heading",
                    "owner": "elementor-core",
                    "plugin_slug": "elementor",
                    "controls": [
                        {"name": "title", "type": "text", "responsive": False, "dynamic_active": True}
                    ],
                }
            },
        }

        with tempfile.TemporaryDirectory() as directory:
            inventory_path = Path(directory) / "inventory.json"
            inventory_path.write_text(json.dumps(inventory), encoding="utf-8")
            report = audit(self.fixture, inventory_path)

        self.assertEqual("pass", report["status"])
        self.assertEqual("elementor-core", report["widgets"][0]["owner"]["owner"])
        self.assertEqual([], report["widgets"][0]["unrecognized_settings"])

    def test_missing_runtime_widget_fails(self):
        inventory = {
            "schema_version": "1.0",
            "environment": {"elementor": "test"},
            "widgets": {},
        }

        with tempfile.TemporaryDirectory() as directory:
            inventory_path = Path(directory) / "inventory.json"
            inventory_path.write_text(json.dumps(inventory), encoding="utf-8")
            report = audit(self.fixture, inventory_path)

        self.assertEqual("fail", report["status"])
        self.assertTrue(any(item["code"] == "missing_widget_dependency" for item in report["errors"]))


if __name__ == "__main__":
    unittest.main()
