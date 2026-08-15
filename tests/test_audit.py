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

    def _audit_documents(self, template, inventory=None):
        with tempfile.TemporaryDirectory() as directory:
            template_path = Path(directory) / "template.json"
            template_path.write_text(json.dumps(template), encoding="utf-8")
            inventory_path = None
            if inventory is not None:
                inventory_path = Path(directory) / "inventory.json"
                inventory_path.write_text(json.dumps(inventory), encoding="utf-8")
            return audit(template_path, inventory_path)

    @staticmethod
    def _classic_widget(settings=None):
        return {
            "title": "Test",
            "type": "page",
            "version": "0.4",
            "page_settings": [],
            "content": [
                {
                    "id": "abc1234",
                    "elType": "widget",
                    "isInner": False,
                    "widgetType": "heading",
                    "settings": settings or {"title": "Hello"},
                    "elements": [],
                }
            ],
        }

    @staticmethod
    def _atomic_widget(settings=None, styles=None):
        return {
            "title": "Atomic test",
            "type": "page",
            "version": "0.4",
            "page_settings": [],
            "content": [
                {
                    "id": "atom0001",
                    "version": "0.0",
                    "elType": "widget",
                    "widgetType": "e-heading",
                    "isInner": False,
                    "settings": settings if settings is not None else {
                        "title": {"$$type": "string", "value": "Hello"}
                    },
                    "editor_settings": [],
                    "interactions": [],
                    "styles": styles if styles is not None else [],
                    "elements": [],
                }
            ],
        }

    def test_classifies_classic_template(self):
        report = audit(self.fixture, None)
        self.assertEqual("pass", report["status"])
        self.assertEqual("classic", report["document"]["editor_family"])
        self.assertEqual(1, report["summary"]["widgets"])

    def test_matches_widget_and_control_inventory(self):
        inventory = {
            "schema_version": "1.2",
            "environment": {"elementor": "test"},
            "widgets": {
                "heading": {
                    "title": "Heading",
                    "owner": "elementor-core",
                    "plugin_slug": "elementor",
                    "controls": [{"name": "title", "type": "text", "responsive": False}],
                }
            },
        }
        report = self._audit_documents(self._classic_widget(), inventory)
        self.assertEqual("pass", report["status"])
        self.assertEqual("elementor-core", report["widgets"][0]["owner"]["owner"])

    def test_missing_runtime_widget_fails(self):
        inventory = {"schema_version": "1.2", "environment": {}, "widgets": {}}
        report = self._audit_documents(self._classic_widget(), inventory)
        self.assertEqual("fail", report["status"])
        self.assertTrue(any(item["code"] == "missing_widget_dependency" for item in report["errors"]))

    def test_unrecognized_widget_setting_warns(self):
        inventory = {
            "schema_version": "1.2",
            "environment": {},
            "widgets": {
                "heading": {
                    "title": "Heading",
                    "owner": "elementor-core",
                    "plugin_slug": "elementor",
                    "controls": [{"name": "title", "type": "text", "responsive": False}],
                }
            },
        }
        report = self._audit_documents(self._classic_widget({"title": "Hello", "not_a_real_control": "x"}), inventory)
        self.assertEqual("warning", report["status"])
        self.assertTrue(any(item["code"] == "unrecognized_widget_settings" for item in report["warnings"]))

    def test_custom_breakpoint_suffix_is_accepted_for_responsive_control(self):
        inventory = {
            "schema_version": "1.2",
            "environment": {"active_devices": ["desktop", "laptop", "tablet", "mobile_extra", "mobile"]},
            "widgets": {
                "heading": {
                    "title": "Heading",
                    "owner": "elementor-core",
                    "plugin_slug": "elementor",
                    "controls": [{"name": "gap", "type": "slider", "responsive": True, "responsive_devices": []}],
                }
            },
        }
        report = self._audit_documents(self._classic_widget({"gap_mobile_extra": {"size": 18, "unit": "px"}}), inventory)
        self.assertEqual("pass", report["status"])
        self.assertIn("mobile_extra", report["responsive_devices"])

    def test_non_responsive_control_does_not_accept_device_suffix(self):
        inventory = {
            "schema_version": "1.2",
            "environment": {"active_devices": ["desktop", "tablet", "mobile"]},
            "widgets": {
                "heading": {
                    "title": "Heading",
                    "owner": "elementor-core",
                    "plugin_slug": "elementor",
                    "controls": [{"name": "title", "type": "text", "responsive": False}],
                }
            },
        }
        report = self._audit_documents(self._classic_widget({"title_mobile": "Wrong"}), inventory)
        self.assertEqual("warning", report["status"])

    def test_atomic_required_fields_are_enforced(self):
        template = self._atomic_widget()
        del template["content"][0]["version"]
        del template["content"][0]["interactions"]
        report = self._audit_documents(template)
        codes = {item["code"] for item in report["errors"]}
        self.assertIn("missing_atomic_version", codes)
        self.assertIn("invalid_atomic_interactions", codes)

    def test_atomic_typed_prop_requires_value(self):
        template = self._atomic_widget({"title": {"$$type": "string"}})
        report = self._audit_documents(template)
        self.assertTrue(any(item["code"] == "atomic_typed_prop_missing_value" for item in report["errors"]))

    def test_atomic_duplicate_style_variant_fails(self):
        style = {
            "id": "style-1",
            "label": "Style",
            "type": "class",
            "variants": [
                {"meta": {"breakpoint": "desktop", "state": None}, "props": {}},
                {"meta": {"breakpoint": "desktop", "state": None}, "props": {}},
            ],
        }
        report = self._audit_documents(self._atomic_widget(styles=[style]))
        self.assertTrue(any(item["code"] == "duplicate_style_variant" for item in report["errors"]))

    def test_atomic_style_prop_requires_typed_value_warning(self):
        style = {
            "id": "style-1",
            "label": "Style",
            "type": "class",
            "variants": [
                {"meta": {"breakpoint": "desktop", "state": None}, "props": {"color": "#fff"}},
            ],
        }
        report = self._audit_documents(self._atomic_widget(styles=[style]))
        self.assertEqual("warning", report["status"])
        self.assertTrue(any(item["code"] == "atomic_untyped_style_prop" for item in report["warnings"]))

    def test_repeater_duplicate_id_fails(self):
        template = self._classic_widget({"items": [{"_id": "same", "text": "A"}, {"_id": "same", "text": "B"}]})
        report = self._audit_documents(template)
        self.assertTrue(any(item["code"] == "duplicate_repeater_id" for item in report["errors"]))

    def test_invalid_global_reference_fails(self):
        template = self._classic_widget({"__globals__": {"title_color": "not-a-global"}})
        report = self._audit_documents(template)
        self.assertTrue(any(item["code"] == "invalid_global_reference" for item in report["errors"]))

    def test_missing_classic_global_fails_with_runtime_inventory(self):
        template = self._classic_widget({"__globals__": {"title_color": "globals/colors?id=missing"}})
        inventory = {
            "schema_version": "1.2",
            "environment": {},
            "design_system": {"classic_globals": {"colors": ["primary"], "typography": []}},
            "widgets": {
                "heading": {
                    "title": "Heading",
                    "owner": "elementor-core",
                    "plugin_slug": "elementor",
                    "controls": [],
                }
            },
        }
        report = self._audit_documents(template, inventory)
        self.assertTrue(any(item["code"] == "missing_global_dependency" for item in report["errors"]))

    def test_missing_atomic_global_class_fails_with_runtime_inventory(self):
        template = self._atomic_widget({"classes": {"$$type": "classes", "value": ["e-missing"]}})
        inventory = {
            "schema_version": "1.2",
            "environment": {},
            "design_system": {"atomic_global_classes": {"ids": ["e-existing"], "labels": {}}},
            "widgets": {
                "e-heading": {
                    "title": "Heading",
                    "owner": "elementor-core",
                    "plugin_slug": "elementor",
                    "controls": [{"name": "classes", "type": "classes", "responsive": False}],
                }
            },
        }
        report = self._audit_documents(template, inventory)
        self.assertTrue(any(item["code"] == "missing_atomic_global_class" for item in report["errors"]))

    def test_atomic_query_requires_target_context_warning(self):
        template = self._atomic_widget({"destination": {"$$type": "query", "value": {"id": {"$$type": "number", "value": 12}}}})
        report = self._audit_documents(template)
        self.assertEqual("warning", report["status"])
        self.assertTrue(any(item["code"] == "target_context_required" for item in report["warnings"]))

    def test_is_inner_is_required(self):
        template = self._classic_widget()
        del template["content"][0]["isInner"]
        report = self._audit_documents(template)
        self.assertTrue(any(item["code"] == "invalid_is_inner" for item in report["errors"]))

    def test_document_version_drift_warns(self):
        template = self._classic_widget()
        template["version"] = "0.3"
        report = self._audit_documents(template)
        self.assertEqual("warning", report["status"])
        self.assertTrue(any(item["code"] == "unexpected_document_version" for item in report["warnings"]))


if __name__ == "__main__":
    unittest.main()
