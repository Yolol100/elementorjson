import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from validate_repo_contracts import validate_repository_contracts, validate_runtime, validate_toolkit


class RepositoryContractTests(unittest.TestCase):
    def test_repository_contracts_match_elementor_runtime_boundaries(self):
        self.assertEqual(validate_repository_contracts(ROOT), [])

    def test_runtime_rejects_missing_negative_evidence_boundaries(self):
        runtime = json.loads((ROOT / "runtime-contract.json").read_text(encoding="utf-8"))
        runtime["evidence"]["does_not_prove"] = []
        errors = validate_runtime(runtime)
        self.assertTrue(any("does_not_prove" in error for error in errors), errors)

    def test_runtime_rejects_loss_of_production_or_accessibility_limitations(self):
        runtime = json.loads((ROOT / "runtime-contract.json").read_text(encoding="utf-8"))
        runtime["evidence"]["does_not_prove"] = [
            item
            for item in runtime["evidence"]["does_not_prove"]
            if "production" not in item.lower() and "accessibility" not in item.lower()
        ]
        errors = validate_runtime(runtime)
        self.assertTrue(any("production" in error for error in errors), errors)
        self.assertTrue(any("accessibility" in error for error in errors), errors)

    def test_runtime_scopes_optional_pro_to_run_specific_version_evidence(self):
        runtime = json.loads((ROOT / "runtime-contract.json").read_text(encoding="utf-8"))
        limitations = "\n".join(runtime["evidence"]["does_not_prove"]).lower()
        policy = runtime["baseline"]["dependency_policy"].lower()
        self.assertIn("cross-run elementor pro version reproducibility", limitations)
        self.assertIn("runtime-inventory.json", policy)
        self.assertIn("exact installed pro version", policy)

    def test_toolkit_rejects_loss_of_mandatory_runtime_tools_and_assertions(self):
        toolkit = json.loads((ROOT / "toolkit-contract.json").read_text(encoding="utf-8"))
        for missing_tool in ["npm-audit", "hello-elementor"]:
            mutated = copy.deepcopy(toolkit)
            mutated["tools"] = [item for item in mutated["tools"] if item.get("id") != missing_tool]
            mutated["usage_assertions"] = [item for item in mutated["usage_assertions"] if item.get("tool") != missing_tool]
            errors = validate_toolkit(mutated)
            self.assertTrue(any(missing_tool in error for error in errors), (missing_tool, errors))


if __name__ == "__main__":
    unittest.main()
