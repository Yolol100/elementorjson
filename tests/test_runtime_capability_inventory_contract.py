#!/usr/bin/env python3

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "wordpress-plugin" / "elementor-json-lab" / "includes" / "class-widget-inventory.php"
ATOMIC = ROOT / "wordpress-plugin" / "elementor-json-lab" / "includes" / "class-atomic-capabilities.php"
BOOTSTRAP = ROOT / "wordpress-plugin" / "elementor-json-lab" / "elementor-json-lab.php"


class RuntimeCapabilityInventoryContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = INVENTORY.read_text(encoding="utf-8")
        cls.atomic_source = ATOMIC.read_text(encoding="utf-8")
        cls.bootstrap_source = BOOTSTRAP.read_text(encoding="utf-8")

    def test_top_level_capability_surfaces_are_exported(self):
        keys = (
            "'widgets'",
            "'elements'",
            "'document_types'",
            "'dynamic_tags'",
            "'experiments'",
            "'atomic_style_schema'",
            "'atomic_dynamic_tags'",
            "'global_classes'",
            "'variables'",
            "'components'",
            "'interactions'",
            "'warnings'",
        )
        for key in keys:
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

    def test_atomic_collector_is_loaded_before_inventory(self):
        atomic_require = "require_once __DIR__ . '/includes/class-atomic-capabilities.php';"
        inventory_require = "require_once __DIR__ . '/includes/class-widget-inventory.php';"
        self.assertIn(atomic_require, self.bootstrap_source)
        self.assertLess(self.bootstrap_source.index(atomic_require), self.bootstrap_source.index(inventory_require))

    def test_atomic_detection_uses_elementor_4_atomic_utils(self):
        self.assertIn("Elementor\\\\Modules\\\\AtomicWidgets\\\\Utils\\\\Utils", self.atomic_source)
        self.assertNotIn("Elementor\\\\Utils::is_atomic", self.atomic_source)

    def test_atomic_config_uses_runtime_props_and_controls(self):
        for key in (
            "'atomic_props_schema'",
            "'atomic_controls'",
            "'atomic_style_states'",
            "'atomic_pseudo_states'",
            "'dependencies_per_target_mapping'",
            "'allowed_child_types'",
        ):
            with self.subTest(key=key):
                self.assertIn(key, self.atomic_source)

    def test_v4_design_system_repositories_are_queried(self):
        required = (
            "Global_Classes_Repository",
            "Variables_Repository",
            "Components_Repository",
            "Style_Schema",
            "Dynamic_Tags_Module",
            "get_features()",
            "get_modules( 'interactions' )",
        )
        for expression in required:
            with self.subTest(expression=expression):
                self.assertIn(expression, self.atomic_source)

    def test_form_action_choices_are_bounded(self):
        self.assertIn("'submit_actions'", self.source)
        self.assertIn("array_slice( $keys, 0, 100 )", self.source)

    def test_inventory_remains_fail_soft_for_optional_managers_and_addons(self):
        self.assertIn("return array();", self.source)
        self.assertIn("catch ( \\Throwable $exception )", self.source)
        self.assertIn("catch ( \\Throwable $exception )", self.atomic_source)
        self.assertIn("'widget_skipped:'", self.source)
        self.assertIn("'element_skipped:'", self.source)


if __name__ == "__main__":
    unittest.main()
