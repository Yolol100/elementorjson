import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from audit_elementor_json import MAX_ELEMENT_DEPTH, audit  # noqa: E402


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

    def _classic_widget_inventory(self, controls=None):
        return {
            "schema_version": "1.1",
            "environment": {"elementor": "test", "active_devices": ["desktop", "tablet", "mobile"]},
            "widgets": {
                "heading": {
                    "title": "Heading",
                    "owner": "elementor-core",
                    "plugin_slug": "elementor",
                    "controls": controls or [{"name": "title", "type": "text", "responsive": False}],
                }
            },
        }

    def test_classifies_classic_template(self):
        report = audit(self.fixture, None)
        self.assertEqual("pass", report["status"])
        self.assertEqual("classic", report["document"]["editor_family"])
        self.assertEqual(1, report["summary"]["widgets"])

    def test_matches_widget_and_control_inventory(self):
        inventory = self._classic_widget_inventory(
            [{"name": "title", "type": "text", "responsive": False, "dynamic_active": True}]
        )
        with tempfile.TemporaryDirectory() as directory:
            inventory_path = Path(directory) / "inventory.json"
            inventory_path.write_text(json.dumps(inventory), encoding="utf-8")
            report = audit(self.fixture, inventory_path)
        self.assertEqual("pass", report["status"])
        self.assertEqual("elementor-core", report["widgets"][0]["owner"]["owner"])
        self.assertEqual([], report["widgets"][0]["unrecognized_settings"])

    def test_missing_runtime_widget_fails(self):
        inventory = {"schema_version": "1.1", "environment": {"elementor": "test"}, "widgets": {}}
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
            "content": [{
                "id": "abc1234", "elType": "widget", "widgetType": "heading",
                "settings": {"title": "Hello", "not_a_real_control": "x"}, "elements": []
            }],
        }
        report = self._audit_documents(template, self._classic_widget_inventory())
        self.assertEqual("warning", report["status"])
        self.assertEqual(["not_a_real_control"], report["widgets"][0]["unrecognized_settings"])

    def test_third_party_widget_owner_becomes_dependency(self):
        template = {
            "title": "Add-on test", "type": "page", "version": "0.4", "page_settings": [],
            "content": [{
                "id": "def5678", "elType": "widget", "widgetType": "vendor-card",
                "settings": {"title": "Card"}, "elements": []
            }],
        }
        inventory = {
            "schema_version": "1.1", "environment": {"elementor": "test"},
            "widgets": {"vendor-card": {
                "title": "Vendor Card", "owner": "third-party", "plugin_slug": "vendor-addon",
                "controls": [{"name": "title", "type": "text"}],
            }},
        }
        report = self._audit_documents(template, inventory)
        self.assertEqual("pass", report["status"])
        self.assertEqual(1, report["dependencies"]["third-party:vendor-addon"])

    def test_custom_breakpoint_suffix_is_accepted_for_responsive_control(self):
        template = {
            "title": "Responsive test", "type": "page", "version": "0.4", "page_settings": [],
            "content": [{
                "id": "resp001", "elType": "widget", "widgetType": "heading",
                "settings": {"gap_mobile_extra": {"size": 18, "unit": "px"}}, "elements": []
            }],
        }
        inventory = self._classic_widget_inventory([{
            "name": "gap", "type": "slider", "responsive": True, "responsive_devices": []
        }])
        inventory["environment"]["active_devices"] = ["desktop", "laptop", "tablet", "mobile_extra", "mobile"]
        report = self._audit_documents(template, inventory)
        self.assertEqual("pass", report["status"])
        self.assertIn("mobile_extra", report["responsive_devices"])

    def test_non_responsive_control_does_not_accept_device_suffix(self):
        template = {
            "title": "Non-responsive test", "type": "page", "version": "0.4", "page_settings": [],
            "content": [{
                "id": "resp002", "elType": "widget", "widgetType": "heading",
                "settings": {"title_mobile": "Wrong suffix"}, "elements": []
            }],
        }
        report = self._audit_documents(template, self._classic_widget_inventory())
        self.assertEqual("warning", report["status"])
        self.assertEqual(["title_mobile"], report["widgets"][0]["unrecognized_settings"])

    def test_responsive_device_restriction_is_respected(self):
        template = {
            "title": "Restricted responsive test", "type": "page", "version": "0.4", "page_settings": [],
            "content": [{
                "id": "resp003", "elType": "widget", "widgetType": "heading",
                "settings": {"gap_laptop": {"size": 32, "unit": "px"}}, "elements": []
            }],
        }
        inventory = self._classic_widget_inventory([{
            "name": "gap", "type": "slider", "responsive": True,
            "responsive_devices": ["desktop", "tablet", "mobile"],
        }])
        inventory["environment"]["active_devices"] = ["desktop", "laptop", "tablet", "mobile"]
        report = self._audit_documents(template, inventory)
        self.assertEqual("warning", report["status"])
        self.assertEqual(["gap_laptop"], report["widgets"][0]["unrecognized_settings"])

    def test_valid_atomic_widget_requires_atomic_shape_and_typed_props(self):
        template = {
            "title": "Atomic", "type": "page", "version": "0.4", "page_settings": [],
            "content": [{
                "id": "atomic01", "version": "0.0", "elType": "e-div-block", "isInner": False,
                "settings": [], "editor_settings": [], "interactions": [], "styles": [],
                "elements": [{
                    "id": "atomic02", "version": "0.0", "elType": "widget", "widgetType": "e-heading",
                    "isInner": False,
                    "settings": {"title": {"$$type": "html-v3", "value": {"content": {"$$type": "string", "value": "Hello"}}}},
                    "editor_settings": [], "interactions": [], "styles": [], "elements": []
                }]
            }],
        }
        report = self._audit_documents(template)
        self.assertEqual("pass", report["status"])
        self.assertEqual("atomic", report["document"]["editor_family"])

    def test_atomic_missing_version_fails(self):
        template = {
            "title": "Atomic bad", "type": "page", "version": "0.4", "page_settings": [],
            "content": [{
                "id": "atomic01", "elType": "e-div-block", "isInner": False,
                "settings": [], "editor_settings": [], "interactions": [], "styles": [], "elements": []
            }],
        }
        report = self._audit_documents(template)
        self.assertEqual("fail", report["status"])
        self.assertTrue(any(item["code"] == "missing_atomic_version" for item in report["errors"]))

    def test_untyped_atomic_prop_warns(self):
        template = {
            "title": "Atomic bad prop", "type": "page", "version": "0.4", "page_settings": [],
            "content": [{
                "id": "atomic01", "version": "0.0", "elType": "widget", "widgetType": "e-heading",
                "isInner": False, "settings": {"title": "raw"}, "editor_settings": [],
                "interactions": [], "styles": [], "elements": []
            }],
        }
        report = self._audit_documents(template)
        self.assertEqual("warning", report["status"])
        self.assertTrue(any(item["code"] == "untyped_atomic_prop" for item in report["warnings"]))

    def test_duplicate_atomic_style_variant_fails(self):
        template = {
            "title": "Atomic style", "type": "page", "version": "0.4", "page_settings": [],
            "content": [{
                "id": "atomic01", "version": "0.0", "elType": "e-div-block", "isInner": False,
                "settings": [], "editor_settings": [], "interactions": [],
                "styles": [{
                    "id": "style01", "variants": [
                        {"meta": {"breakpoint": "desktop", "state": None}, "props": {}},
                        {"meta": {"breakpoint": "desktop", "state": None}, "props": {}},
                    ]
                }], "elements": []
            }],
        }
        report = self._audit_documents(template)
        self.assertEqual("fail", report["status"])
        self.assertTrue(any(item["code"] == "duplicate_style_variant" for item in report["errors"]))

    def test_duplicate_repeater_id_fails(self):
        template = {
            "title": "Repeater", "type": "page", "version": "0.4", "page_settings": [],
            "content": [{
                "id": "rep001", "elType": "widget", "widgetType": "heading",
                "settings": {"items": [{"_id": "same"}, {"_id": "same"}]}, "elements": []
            }],
        }
        report = self._audit_documents(template)
        self.assertEqual("fail", report["status"])
        self.assertTrue(any(item["code"] == "duplicate_repeater_id" for item in report["errors"]))

    def test_globals_and_dynamic_references_are_reported(self):
        template = {
            "title": "Target bound", "type": "page", "version": "0.4", "page_settings": [],
            "content": [{
                "id": "bound01", "elType": "widget", "widgetType": "heading",
                "settings": {
                    "__globals__": {"title_color": "globals/colors?id=primary"},
                    "title": "{{post_title}}",
                    "template_id": 42,
                }, "elements": []
            }],
        }
        report = self._audit_documents(template)
        self.assertEqual("warning", report["status"])
        self.assertTrue(report["globals"])
        self.assertTrue(report["dynamic_reference_paths"])
        self.assertTrue(report["site_bound_reference_paths"])

    def test_globals_remain_unverified_with_widget_inventory(self):
        template = {
            "title": "Global target bound", "type": "page", "version": "0.4", "page_settings": [],
            "content": [{
                "id": "global01", "elType": "widget", "widgetType": "heading",
                "settings": {
                    "title": "Hello",
                    "__globals__": {"title_color": "globals/colors?id=primary"},
                }, "elements": []
            }],
        }
        report = self._audit_documents(template, self._classic_widget_inventory())
        self.assertEqual("warning", report["status"])
        self.assertTrue(any(item["code"] == "unverified_global_references" for item in report["warnings"]))
        self.assertTrue(report["globals"])

    def test_element_depth_guard_fails_closed(self):
        node = {"id": "n0", "elType": "container", "settings": [], "elements": []}
        root = node
        for index in range(1, MAX_ELEMENT_DEPTH + 3):
            child = {"id": f"n{index}", "elType": "container", "settings": [], "elements": []}
            node["elements"] = [child]
            node = child
        template = {"title": "Deep", "type": "page", "version": "0.4", "page_settings": [], "content": [root]}
        report = self._audit_documents(template)
        self.assertEqual("fail", report["status"])
        self.assertTrue(any(item["code"] == "max_element_depth_exceeded" for item in report["errors"]))


if __name__ == "__main__":
    unittest.main()
