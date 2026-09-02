#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from compare_runtime_capabilities import compare  # noqa: E402


class CompareRuntimeCapabilitiesTest(unittest.TestCase):
    def inventory(self):
        return {
            "environment": {
                "elementor": "4.2.4",
                "elementor_pro": "4.2.0",
                "active_plugins": [
                    {"basename": "elementor/elementor.php", "name": "Elementor", "version": "4.2.4"},
                    {"basename": "addon/addon.php", "name": "Addon", "version": "1.0.0"},
                ],
            },
            "widgets": {"heading": {"controls": [{"name": "title"}]}},
            "elements": {"e-heading": {"atomic": True, "atomic_config": {"atomic_props_schema": {"text": {"type": "string"}}}}},
            "document_types": {"page": {"class": "Page"}},
            "dynamic_tags": {"post-title": {"categories": ["text"]}},
            "experiments": {"e_atomic_elements": {"active": True}},
            "atomic_style_schema": {"width": {"type": "size"}},
            "atomic_dynamic_tags": {"post-title": {"categories": ["text"]}},
            "global_classes": {"e-gc-1": {"id": "e-gc-1", "styles": {"color": "red"}}},
            "variables": {"e-gv-1": {"id": "e-gv-1", "value": "1rem"}},
            "components": {"component-1": {"uid": "component-1", "styles": []}},
            "interactions": {"constants": {"effects": ["fade"]}},
        }

    def test_identical_inventory_is_no_change(self):
        before = self.inventory()
        after = self.inventory()
        report = compare(before, after)
        self.assertEqual("1.1", report["schema_version"])
        self.assertEqual("no_change", report["status"])
        self.assertEqual("no_change", report["impact"])

    def test_addon_version_change_is_drift(self):
        before = self.inventory()
        after = self.inventory()
        after["environment"]["active_plugins"][1]["version"] = "1.1.0"
        report = compare(before, after)
        self.assertEqual("changed", report["status"])
        self.assertEqual("drift_detected", report["impact"])
        self.assertEqual("addon/addon.php", report["plugins"]["version_changed"][0]["basename"])

    def test_removed_widget_requires_review(self):
        before = self.inventory()
        after = self.inventory()
        after["widgets"] = {}
        report = compare(before, after)
        self.assertEqual("review_required", report["impact"])
        self.assertEqual(["heading"], report["capabilities"]["widgets"]["removed"])

    def test_changed_controls_require_review(self):
        before = self.inventory()
        after = self.inventory()
        after["widgets"]["heading"]["controls"].append({"name": "size"})
        report = compare(before, after)
        self.assertEqual("review_required", report["impact"])
        self.assertEqual(["heading"], report["capabilities"]["widgets"]["changed"])

    def test_changed_atomic_props_require_review(self):
        before = self.inventory()
        after = self.inventory()
        after["elements"]["e-heading"]["atomic_config"]["atomic_props_schema"]["text"]["type"] = "union"
        report = compare(before, after)
        self.assertEqual("review_required", report["impact"])
        self.assertEqual(["e-heading"], report["capabilities"]["elements"]["changed"])

    def test_changed_variable_requires_review(self):
        before = self.inventory()
        after = self.inventory()
        after["variables"]["e-gv-1"]["value"] = "2rem"
        report = compare(before, after)
        self.assertEqual("review_required", report["impact"])
        self.assertEqual(["e-gv-1"], report["capabilities"]["variables"]["changed"])

    def test_added_component_is_drift(self):
        before = self.inventory()
        after = self.inventory()
        after["components"]["component-2"] = {"uid": "component-2", "styles": []}
        report = compare(before, after)
        self.assertEqual("drift_detected", report["impact"])
        self.assertEqual(["component-2"], report["capabilities"]["components"]["added"])

    def test_experiment_state_change_requires_review(self):
        before = self.inventory()
        after = self.inventory()
        after["experiments"]["e_atomic_elements"]["active"] = False
        report = compare(before, after)
        self.assertEqual("review_required", report["impact"])
        self.assertEqual(["e_atomic_elements"], report["capabilities"]["experiments"]["changed"])


if __name__ == "__main__":
    unittest.main()
