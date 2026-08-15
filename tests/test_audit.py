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

    def test_unrecognized_widget_setting_warns(self):
        template = {
            "title": "Settings test",
            "type": "page",
            "version": "0.4",
            "page_settings": [],
            "content": [
                {
                    "id": "abc1234",
                    "elType": "widget",
                    "widgetType": "heading",
                    "settings": {"title": "Hello", "not_a_real_control": "x"},
                    "elements": [],
                }
            ],
        }
        inventory = {
            "schema_version": "1.0",
            "environment": {"elementor": "test"},
            "widgets": {
                "heading": {
                    "title": "Heading",
                    "owner": "elementor-core",
                    "plugin_slug": "elementor",
                    "controls": [{"name": "title", "type": "text"}],
                }
            },
        }

        with tempfile.TemporaryDirectory() as directory:
            template_path = Path(directory) / "template.json"
            inventory_path = Path(directory) / "inventory.json"
            template_path.write_text(json.dumps(template), encoding="utf-8")
            inventory_path.write_text(json.dumps(inventory), encoding="utf-8")
            report = audit(template_path, inventory_path)

        self.assertEqual("warning", report["status"])
        self.assertEqual(["not_a_real_control"], report["widgets"][0]["unrecognized_settings"])
        self.assertTrue(any(item["code"] == "unrecognized_widget_settings" for item in report["warnings"]))

    def test_third_party_widget_owner_becomes_dependency(self):
        template = {
            "title": "Add-on test",
            "type": "page",
            "version": "0.4",
            "page_settings": [],
            "content": [
                {
                    "id": "def5678",
                    "elType": "widget",
                    "widgetType": "vendor-card",
                    "settings": {"title": "Card"},
                    "elements": [],
                }
            ],
        }
        inventory = {
            "schema_version": "1.0",
            "environment": {"elementor": "test"},
            "widgets": {
                "vendor-card": {
                    "title": "Vendor Card",
                    "owner": "third-party",
                    "plugin_slug": "vendor-addon",
                    "controls": [{"name": "title", "type": "text"}],
                }
            },
        }

        with tempfile.TemporaryDirectory() as directory:
            template_path = Path(directory) / "template.json"
            inventory_path = Path(directory) / "inventory.json"
            template_path.write_text(json.dumps(template), encoding="utf-8")
            inventory_path.write_text(json.dumps(inventory), encoding="utf-8")
            report = audit(template_path, inventory_path)

        self.assertEqual("pass", report["status"])
        self.assertEqual("third-party", report["widgets"][0]["owner"]["owner"])
        self.assertEqual("vendor-addon", report["widgets"][0]["owner"]["plugin_slug"])
        self.assertEqual(1, report["dependencies"]["third-party:vendor-addon"])


if __name__ == "__main__":
    unittest.main()
