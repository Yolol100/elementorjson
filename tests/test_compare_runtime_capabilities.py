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
            "elements": {"container": {"controls": []}},
            "document_types": {"page": {"class": "Page"}},
            "dynamic_tags": {"post-title": {"categories": ["text"]}},
        }

    def test_identical_inventory_is_no_change(self):
        before = self.inventory()
        after = self.inventory()
        report = compare(before, after)
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


if __name__ == "__main__":
    unittest.main()
