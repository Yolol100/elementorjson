import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from audit_elementor_json import audit  # noqa: E402


class AtomicAuditTests(unittest.TestCase):
    def test_atomic_typed_props_do_not_use_legacy_control_name_warnings(self):
        template = {
            "title": "Atomic runtime controls",
            "type": "page",
            "version": "0.4",
            "page_settings": [],
            "content": [
                {
                    "id": "atomic01",
                    "version": "0.0",
                    "elType": "widget",
                    "widgetType": "e-heading",
                    "isInner": False,
                    "settings": {
                        "tag": {"$$type": "string", "value": "h2"},
                        "title": {
                            "$$type": "html-v3",
                            "value": {
                                "content": {"$$type": "string", "value": "Atomic heading"},
                                "children": [],
                            },
                        },
                        "link": {"$$type": "link", "value": []},
                    },
                    "editor_settings": [],
                    "interactions": [],
                    "styles": [],
                    "elements": [],
                }
            ],
        }
        inventory = {
            "schema_version": "1.1",
            "environment": {"elementor": "4.2.2"},
            "widgets": {
                "e-heading": {
                    "title": "Heading",
                    "owner": "elementor-core",
                    "plugin_slug": "elementor",
                    "controls": [],
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
        self.assertEqual("atomic", report["document"]["editor_family"])
        self.assertEqual([], report["widgets"][0]["unrecognized_settings"])
        self.assertFalse(any(item["code"] == "unrecognized_widget_settings" for item in report["warnings"]))
        self.assertEqual("elementor-core", report["widgets"][0]["owner"]["owner"])


    def _assert_elementor_431_escaped_html(self, widget, field):
        value = widget["settings"][field]
        self.assertEqual("escaped-html", value["$" + "$type"])
        self.assertIsInstance(value["value"], str)
        self.assertTrue(value["value"].strip())

    def test_smoke_atomic_props_match_elementor_431(self):
        template = json.loads((ROOT / "templates/smoke-atomic.json").read_text(encoding="utf-8"))
        widgets = template["content"][0]["elements"]
        self.assertEqual(["e-heading", "e-paragraph"], [w["widgetType"] for w in widgets])
        self._assert_elementor_431_escaped_html(widgets[0], "title")
        self._assert_elementor_431_escaped_html(widgets[1], "paragraph")

    def test_smoke_atomic_does_not_claim_nonexistent_optional_roundtrip_fields(self):
        template = json.loads((ROOT / "templates/smoke-atomic.json").read_text(encoding="utf-8"))
        container = template["content"][0]
        for element in [container, *container["elements"]]:
            for optional in ("settings", "editor_settings", "interactions", "styles"):
                if optional in element:
                    self.assertNotEqual([], element[optional], f"{element['id']}: {optional} is a native importer no-op")
        for widget in container["elements"]:
            self.assertNotIn("link", widget["settings"])

    def test_legacy_html_v3_rejected_as_431_smoke_value(self):
        heading = {"settings": {"title": {
            "$" + "$type": "html-v3",
            "value": {"content": {"$" + "$type": "string", "value": "Legacy"}, "children": []},
        }}}
        with self.assertRaises(AssertionError):
            self._assert_elementor_431_escaped_html(heading, "title")


if __name__ == "__main__":
    unittest.main()
