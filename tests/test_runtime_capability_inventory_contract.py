#!/usr/bin/env python3

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "wordpress-plugin" / "elementor-json-lab" / "includes" / "class-widget-inventory.php"


class RuntimeCapabilityInventoryContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = INVENTORY.read_text(encoding="utf-8")

    def test_top_level_capability_surfaces_are_exported(self):
        for key in ("'widgets'", "'elements'", "'document_types'", "'dynamic_tags'"):
            with self.subTest(key=key):
                self.assertIn(key, self.source)

    def test_runtime_managers_are_queried(self):
        required = (
            "widgets_manager->get_widget_types()",
            "elements_manager->get_element_types()",
            "documents->get_document_types()",
            "dynamic_tags->get_tags()",
        )
        for expression in required:
            with self.subTest(expression=expression):
                self.assertIn(expression, self.source)

    def test_atomic_detection_uses_elementor_4_atomic_utils(self):
        self.assertIn("Elementor\\\\Modules\\\\AtomicWidgets\\\\Utils\\\\Utils", self.source)
        self.assertNotIn("Elementor\\\\Utils::is_atomic", self.source)

    def test_form_action_choices_are_bounded(self):
        self.assertIn("'submit_actions'", self.source)
        self.assertIn("array_slice( $keys, 0, 100 )", self.source)

    def test_inventory_remains_fail_soft_for_optional_managers(self):
        self.assertIn("return array();", self.source)
        self.assertIn("catch ( \\Throwable $exception )", self.source)


if __name__ == "__main__":
    unittest.main()
