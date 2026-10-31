"""Regression guard: the manual importer probe defaults to the supported QA baseline.

The legacy importer remains selectable to reproduce genuine Atomic data loss;
the diagnostic must not silently accept, normalize, or repair missing content.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ImporterDiagnosticVersionTests(unittest.TestCase):
    def test_diagnostic_defaults_to_supported_version_without_hiding_legacy_failure(self):
        qa = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
        diagnostic = (ROOT / ".github/workflows/diagnose-importer.yml").read_text(encoding="utf-8")

        core = re.search(r"^  ELEMENTOR_CORE_VERSION: '([^']+)'$", qa, re.M)
        hello = re.search(r"^  HELLO_ELEMENTOR_VERSION: '([^']+)'$", qa, re.M)
        self.assertIsNotNone(core)
        self.assertIsNotNone(hello)

        self.assertIn("  workflow_dispatch:\n    inputs:\n", diagnostic)
        self.assertIn("type: choice", diagnostic)
        self.assertIn("default: '" + core.group(1) + "'", diagnostic)
        self.assertIn("          - '4.2.3'", diagnostic)
        self.assertIn("  ELEMENTOR_CORE_VERSION: ${{ inputs.elementor_core_version || '4.3.1' }}", diagnostic)
        self.assertIn("  pull_request:\n    branches: [main]\n", diagnostic)
        self.assertIn("      - 'templates/**'", diagnostic)
        self.assertIn("          persist-credentials: false", diagnostic)
        self.assertIn("  HELLO_ELEMENTOR_VERSION: '" + hello.group(1) + "'", diagnostic)
        self.assertIn("node-version: '24.18.0'", diagnostic)
        self.assertIn('--version="$ELEMENTOR_CORE_VERSION"', diagnostic)
        self.assertIn('--version="$HELLO_ELEMENTOR_VERSION"', diagnostic)

        # The importer and comparator both execute; a mismatch exits nonzero.
        self.assertIn("elementor library import", diagnostic)
        self.assertIn("tools/compare_elementor_roundtrip.py", diagnostic)
        self.assertIn('overall=1', diagnostic)
        self.assertIn('exit "$overall"', diagnostic)
        self.assertNotIn("|| true\n\n            echo \"===== ${filename}: SEMANTIC ROUNDTRIP", diagnostic)


if __name__ == "__main__":
    unittest.main()
