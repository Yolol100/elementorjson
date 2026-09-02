#!/usr/bin/env python3

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "v4-runtime-capability-inventory.md"


class V4RuntimeCapabilityDocsTest(unittest.TestCase):
    def test_v4_surfaces_and_evidence_boundary_are_documented(self):
        text = DOC.read_text(encoding="utf-8")
        for term in (
            "atomic_config",
            "atomic_style_schema",
            "atomic_dynamic_tags",
            "global_classes",
            "variables",
            "components",
            "interactions",
            "controlled runtime only",
            "private Bridge inventory",
        ):
            with self.subTest(term=term):
                self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
