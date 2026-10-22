import copy
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from validate_repo_contracts import (
    validate_repository_contracts,
    validate_runtime,
    validate_toolkit,
    validate_visual_target_schema,
    validate_workflow_wiring,
)


class RepositoryContractTests(unittest.TestCase):
    def test_repository_contracts_match_elementor_runtime_boundaries(self):
        self.assertEqual(validate_repository_contracts(ROOT), [])

    def test_runtime_rejects_private_visibility_regression(self):
        runtime = json.loads((ROOT / "runtime-contract.json").read_text(encoding="utf-8"))
        runtime["privacy"]["repository_visibility_assumption"] = "private"
        errors = validate_runtime(runtime)
        self.assertTrue(any("repository_visibility_assumption" in error for error in errors), errors)

    def test_runtime_rejects_stale_private_repository_wording(self):
        runtime = json.loads((ROOT / "runtime-contract.json").read_text(encoding="utf-8"))
        runtime["inputs"]["reference_visual"] = "kept outside this private repository when confidential"
        errors = validate_runtime(runtime)
        self.assertTrue(any("stale private-repository wording" in error for error in errors), errors)

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
        for missing_tool in ["visual-target-builder", "visual-target-validator", "page-composition-auditor", "npm-audit", "hello-elementor"]:
            mutated = copy.deepcopy(toolkit)
            mutated["tools"] = [item for item in mutated["tools"] if item.get("id") != missing_tool]
            mutated["usage_assertions"] = [item for item in mutated["usage_assertions"] if item.get("tool") != missing_tool]
            errors = validate_toolkit(mutated, ROOT)
            self.assertTrue(any(missing_tool in error for error in errors), (missing_tool, errors))

    def test_toolkit_usage_assertions_are_checked_against_repo_files(self):
        toolkit = json.loads((ROOT / "toolkit-contract.json").read_text(encoding="utf-8"))
        mutated = copy.deepcopy(toolkit)
        mutated["usage_assertions"][0]["contains"] = "__definitely_missing_wiring_marker__"
        errors = validate_toolkit(mutated, ROOT)
        self.assertTrue(any("usage assertion mismatch" in error for error in errors), errors)

    def test_toolkit_rejects_malformed_ids_and_assertions_without_crashing(self):
        original = json.loads((ROOT / "toolkit-contract.json").read_text())
        for bad in [None, [], {}, 123, ""]:
            with self.subTest(bad=bad):
                mutated = copy.deepcopy(original)
                mutated["tools"][0]["id"] = bad
                self.assertTrue(validate_toolkit(mutated, ROOT))
                mutated = copy.deepcopy(original)
                mutated["usage_assertions"][0]["path"] = bad
                self.assertTrue(validate_toolkit(mutated, ROOT))

    def test_usage_assertions_cannot_read_outside_the_repository(self):
        original = json.loads((ROOT / "toolkit-contract.json").read_text())
        for path in ["../README.md", str(ROOT / "README.md"), "../elementorjson/README.md", "..\\README.md"]:
            mutated = copy.deepcopy(original)
            mutated["usage_assertions"][0]["path"] = path
            self.assertTrue(any("unsafe assertion path" in e for e in validate_toolkit(mutated, ROOT)))

    def test_unknown_assertion_tool_is_not_evidence(self):
        mutated = json.loads((ROOT / "toolkit-contract.json").read_text())
        mutated["usage_assertions"].append({"tool": "unregistered", "path": "README.md", "contains": "Elementor"})
        self.assertTrue(any("unknown assertion tool" in e for e in validate_toolkit(mutated, ROOT)))

    def test_visual_target_schema_keeps_prediction_boundary(self):
        self.assertEqual(validate_visual_target_schema(ROOT), [])
        schema = json.loads((ROOT / "contracts" / "visual-target.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["evidence_class"]["const"], "source_prediction")
        self.assertIs(schema["properties"]["render_observed"]["const"], False)
        self.assertEqual(
            schema["properties"]["provenance_labels"]["items"]["enum"],
            ["explicit", "declared", "inferred", "unknown"],
        )

    def test_composition_workflow_keeps_manual_dispatch_and_visual_target_wiring(self):
        self.assertEqual(validate_workflow_wiring(ROOT), [])
        workflow = (ROOT / ".github" / "workflows" / "composition-contract.yml").read_text(encoding="utf-8")
        self.assertIn("  workflow_dispatch:", workflow)
        for marker in [
            "audit_page_composition.py", "build_visual_target.py", "validate_visual_target.py",
            ".design-intent.json", ".content-contract.json", "visual-targets",
        ]:
            self.assertIn(marker, workflow)

    def test_toolkit_workflow_keeps_manual_dispatch(self):
        workflow = (ROOT / ".github" / "workflows" / "toolkit-contract.yml").read_text(encoding="utf-8")
        self.assertIn("  workflow_dispatch:", workflow)

    def test_reenabling_automatic_triggers_requires_complete_path_coverage(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            workflows = root / ".github" / "workflows"
            workflows.mkdir(parents=True)
            for name in ("composition-contract.yml", "toolkit-contract.yml"):
                original = (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
                self.assertIn("on:\n  workflow_dispatch:\n", original)
                # Removing mandatory path filters while automatic triggers
                # stay enabled must fail repository validation.
                workflows.joinpath(name).write_text(
                    original
                    .replace("      - 'contracts/**'\n", "")
                    .replace("      - 'sidecars/**'\n", "")
                    .replace("      - 'templates/**'\n", ""),
                    encoding="utf-8",
                )
            errors = validate_workflow_wiring(root)
            self.assertTrue(any("composition-contract.yml: required wiring missing: contracts/**" in e for e in errors), errors)
            self.assertTrue(any("composition-contract.yml: required wiring missing: sidecars/**" in e for e in errors), errors)
            self.assertTrue(any("composition-contract.yml: required wiring missing: templates/**" in e for e in errors), errors)
            self.assertTrue(any("toolkit-contract.yml: contract schema changes" in e for e in errors), errors)

    def test_public_ci_auto_triggers_cover_main_and_pull_requests(self):
        for workflow_name in (
            "validate.yml", "composition-contract.yml",
            "toolkit-contract.yml", "native-kit-contract.yml",
        ):
            workflow = (ROOT / ".github" / "workflows" / workflow_name).read_text(encoding="utf-8")
            from validate_repo_contracts import workflow_events
            events = workflow_events(workflow)
            with self.subTest(workflow=workflow_name):
                self.assertIn("workflow_dispatch", events)
                self.assertIn("push", events)
                self.assertIn("pull_request", events)
                self.assertIn("branches: [main]", workflow)

    def test_security_scan_is_automated_without_secrets(self):
        workflow = (ROOT / ".github" / "workflows" / "codeql.yml").read_text(encoding="utf-8")
        from validate_repo_contracts import workflow_events
        self.assertEqual(
            set(workflow_events(workflow)),
            {"workflow_dispatch", "push", "pull_request", "schedule"},
        )
        for item in ("security-events: write", "javascript-typescript", "python", "actions"):
            self.assertIn(item, workflow)
        self.assertNotIn("secrets.", workflow)

    def test_removing_manual_dispatch_fails_closed(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            workflows = root / ".github" / "workflows"
            workflows.mkdir(parents=True)
            for name in ("composition-contract.yml", "toolkit-contract.yml"):
                original = (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
                workflows.joinpath(name).write_text(
                    original.replace("  workflow_dispatch:\n", "", 1),
                    encoding="utf-8",
                )
            errors = validate_workflow_wiring(root)
            self.assertTrue(any("composition-contract.yml: workflow_dispatch" in e for e in errors), errors)
            self.assertTrue(any("toolkit-contract.yml: workflow_dispatch" in e for e in errors), errors)


if __name__ == "__main__":
    unittest.main()
