import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from compare_elementor_roundtrip import compare  # noqa: E402
from validate_elementor_deep import validate_document  # noqa: E402


ATOMIC_TEMPLATE = {
    "title": "Atomic fixture",
    "type": "page",
    "version": "0.4",
    "page_settings": [],
    "content": [
        {
            "id": "atomic01",
            "version": "0.0",
            "elType": "e-div-block",
            "isInner": False,
            "settings": [],
            "editor_settings": [],
            "interactions": [],
            "styles": [],
            "elements": [
                {
                    "id": "atomic02",
                    "version": "0.0",
                    "elType": "widget",
                    "widgetType": "e-heading",
                    "isInner": False,
                    "settings": {
                        "tag": {"$$type": "string", "value": "h3"},
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
    ],
}


class DeepValidationTests(unittest.TestCase):
    def test_valid_atomic_structure_passes(self):
        report = validate_document(copy.deepcopy(ATOMIC_TEMPLATE))
        self.assertEqual("pass", report["status"])
        self.assertEqual("atomic", report["editor_family"])
        self.assertEqual(2, report["summary"]["atomic_elements"])

    def test_atomic_missing_version_fails(self):
        template = copy.deepcopy(ATOMIC_TEMPLATE)
        del template["content"][0]["elements"][0]["version"]
        report = validate_document(template)
        self.assertEqual("fail", report["status"])
        self.assertTrue(any(item["code"] == "atomic_missing_version" for item in report["errors"]))

    def test_atomic_untyped_setting_fails(self):
        template = copy.deepcopy(ATOMIC_TEMPLATE)
        template["content"][0]["elements"][0]["settings"]["tag"] = "h3"
        report = validate_document(template)
        self.assertEqual("fail", report["status"])
        self.assertTrue(any(item["code"] == "atomic_untyped_setting" for item in report["errors"]))

    def test_atomic_untyped_style_prop_fails(self):
        template = copy.deepcopy(ATOMIC_TEMPLATE)
        template["content"][0]["styles"] = [
            {
                "id": "style-one",
                "type": "class",
                "variants": [
                    {
                        "meta": {"breakpoint": "desktop", "state": None},
                        "props": {"color": "#111111"},
                    }
                ],
            }
        ]
        report = validate_document(template)
        self.assertEqual("fail", report["status"])
        self.assertTrue(any(item["code"] == "atomic_untyped_style_prop" for item in report["errors"]))

    def test_duplicate_repeater_id_fails(self):
        template = {
            "title": "Repeater",
            "type": "page",
            "version": "0.4",
            "page_settings": [],
            "content": [
                {
                    "id": "classic01",
                    "elType": "widget",
                    "widgetType": "icon-list",
                    "isInner": False,
                    "settings": {"icon_list": [{"_id": "same"}, {"_id": "same"}]},
                    "elements": [],
                }
            ],
        }
        report = validate_document(template)
        self.assertEqual("fail", report["status"])
        self.assertTrue(any(item["code"] == "duplicate_repeater_id" for item in report["errors"]))

    def test_globals_require_target_warning(self):
        template = {
            "title": "Globals",
            "type": "page",
            "version": "0.4",
            "page_settings": [],
            "content": [
                {
                    "id": "classic02",
                    "elType": "widget",
                    "widgetType": "heading",
                    "isInner": False,
                    "settings": {"__globals__": {"title_color": "globals/colors?id=primary"}},
                    "elements": [],
                }
            ],
        }
        report = validate_document(template)
        self.assertEqual("warning", report["status"])
        self.assertTrue(any(item["code"] == "unverified_global_references" for item in report["warnings"]))

    def test_roundtrip_ignores_only_element_ids(self):
        imported = copy.deepcopy(ATOMIC_TEMPLATE)
        imported["content"][0]["id"] = "newouter"
        imported["content"][0]["elements"][0]["id"] = "newinner"
        report = compare(copy.deepcopy(ATOMIC_TEMPLATE), imported)
        self.assertEqual("pass", report["status"])

    def test_roundtrip_preserves_nested_reference_ids(self):
        source = copy.deepcopy(ATOMIC_TEMPLATE)
        imported = copy.deepcopy(ATOMIC_TEMPLATE)
        source["content"][0]["elements"][0]["settings"]["reference"] = {
            "$$type": "query",
            "value": {"id": {"$$type": "number", "value": 42}},
        }
        imported["content"][0]["elements"][0]["settings"]["reference"] = {
            "$$type": "query",
            "value": {"id": {"$$type": "number", "value": 43}},
        }
        report = compare(source, imported)
        self.assertEqual("fail", report["status"])
        self.assertTrue(report["differences"])


if __name__ == "__main__":
    unittest.main()
