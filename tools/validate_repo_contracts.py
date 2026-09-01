#!/usr/bin/env python3
import json
import sys
from pathlib import Path


REQUIRED_TOOL_IDS = [
    "elementor-json-auditor",
    "deep-json-validator",
    "page-composition-auditor",
    "visual-target-builder",
    "visual-target-validator",
    "npm-audit",
    "wp-env",
    "elementor-core",
    "hello-elementor",
    "template-library-import",
    "semantic-roundtrip",
    "playwright",
]

REQUIRED_NEGATIVE_EVIDENCE_MARKERS = [
    "staging",
    "target_verified",
    "production",
    "accessibility",
]

COMPOSITION_WORKFLOW_MARKERS = [
    "contracts/**",
    "sidecars/**",
    "templates/**",
    "audit_page_composition.py",
    "build_visual_target.py",
    "validate_visual_target.py",
    ".design-intent.json",
    ".content-contract.json",
    "visual-targets",
]


def load_object(path: Path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return None, [f"{path}: invalid JSON: {exc}"]
    if not isinstance(value, dict):
        return None, [f"{path}: root must be an object"]
    return value, []


def require_keys(filename, value, keys):
    return [f"{filename}: required key missing: {key}" for key in keys if key not in value]


def validate_runtime(value):
    errors = require_keys(
        "runtime-contract.json",
        value,
        ["contract_version", "repository", "default_branch", "workflow", "role", "caller", "trigger", "activation", "evidence"],
    )
    if value.get("repository") != "Yolol100/elementorjson":
        errors.append("runtime-contract.json: repository must be Yolol100/elementorjson")
    if value.get("default_branch") != "main":
        errors.append("runtime-contract.json: default_branch must be main")
    if value.get("workflow") != ".github/workflows/validate.yml":
        errors.append("runtime-contract.json: workflow must point to validate.yml")
    if value.get("role") != "controlled_runtime":
        errors.append("runtime-contract.json: role must remain controlled_runtime")

    caller = value.get("caller") if isinstance(value.get("caller"), dict) else {}
    if caller.get("project") != "project-elementor" or caller.get("domain_owner") != "elementor":
        errors.append("runtime-contract.json: caller must remain project-elementor/elementor")
    if caller.get("connector") != "GitHub":
        errors.append("runtime-contract.json: caller connector must remain GitHub")

    trigger = value.get("trigger") if isinstance(value.get("trigger"), dict) else {}
    if not trigger.get("required_when") or not trigger.get("forbidden_when"):
        errors.append("runtime-contract.json: trigger boundaries must be populated")

    activation = value.get("activation") if isinstance(value.get("activation"), dict) else {}
    if not activation.get("before_run") or not activation.get("readback"):
        errors.append("runtime-contract.json: activation before_run/readback must be populated")

    evidence = value.get("evidence") if isinstance(value.get("evidence"), dict) else {}
    if evidence.get("level") != "controlled_runtime":
        errors.append("runtime-contract.json: evidence.level must remain controlled_runtime")
    if evidence.get("source_prediction_level") != "source_prediction":
        errors.append("runtime-contract.json: evidence.source_prediction_level must remain source_prediction")
    does_not_prove = evidence.get("does_not_prove")
    if not isinstance(does_not_prove, list) or not does_not_prove or not all(isinstance(item, str) and item.strip() for item in does_not_prove):
        errors.append("runtime-contract.json: evidence.does_not_prove must remain a non-empty list of explicit limitations")
    else:
        normalized = "\n".join(does_not_prove).lower()
        for marker in REQUIRED_NEGATIVE_EVIDENCE_MARKERS:
            if marker not in normalized:
                errors.append(f"runtime-contract.json: evidence.does_not_prove must preserve the {marker!r} limitation")
    return errors


def validate_toolkit(value, root=Path(".")):
    errors = require_keys(
        "toolkit-contract.json",
        value,
        ["schema_version", "owner_skill", "project_id", "repository", "evidence_role", "requires_account", "requires_api_key", "requires_mcp", "tools", "usage_assertions", "boundaries"],
    )
    expected = {
        "owner_skill": "elementor",
        "project_id": "project-elementor",
        "repository": "Yolol100/elementorjson",
        "requires_account": False,
        "requires_api_key": False,
        "requires_mcp": False,
    }
    for key, expected_value in expected.items():
        if value.get(key) != expected_value:
            errors.append(f"toolkit-contract.json: {key} must be {expected_value!r}")

    tools = value.get("tools")
    ids = []
    if not isinstance(tools, list) or not tools:
        errors.append("toolkit-contract.json: tools must be a non-empty list")
    else:
        ids = [item.get("id") for item in tools if isinstance(item, dict)]
        if len(ids) != len(set(ids)):
            errors.append("toolkit-contract.json: tool IDs must be unique")
        for required_tool in REQUIRED_TOOL_IDS:
            if required_tool not in ids:
                errors.append(f"toolkit-contract.json: required tool missing: {required_tool}")

    assertions = value.get("usage_assertions")
    assertion_tools = set()
    if not isinstance(assertions, list) or not assertions:
        errors.append("toolkit-contract.json: usage_assertions must be a non-empty list")
    else:
        for index, assertion in enumerate(assertions):
            if not isinstance(assertion, dict) or not assertion.get("tool") or not assertion.get("path") or not assertion.get("contains"):
                errors.append("toolkit-contract.json: every usage assertion must bind tool/path/contains")
                continue
            assertion_tools.add(assertion["tool"])
            assertion_path = root / assertion["path"]
            if not assertion_path.is_file():
                errors.append(f"toolkit-contract.json: usage assertion path missing at index {index}: {assertion['path']}")
                continue
            try:
                text = assertion_path.read_text(encoding="utf-8")
            except OSError as exc:
                errors.append(f"toolkit-contract.json: could not read usage assertion path {assertion['path']}: {exc}")
                continue
            if assertion["contains"] not in text:
                errors.append(
                    f"toolkit-contract.json: usage assertion mismatch for {assertion['tool']} in {assertion['path']}: "
                    f"missing {assertion['contains']!r}"
                )
        for required_tool in REQUIRED_TOOL_IDS:
            if required_tool not in assertion_tools:
                errors.append(f"toolkit-contract.json: usage assertion missing for required tool: {required_tool}")

    boundaries = value.get("boundaries")
    if not isinstance(boundaries, list) or not boundaries or not all(isinstance(item, str) and item.strip() for item in boundaries):
        errors.append("toolkit-contract.json: boundaries must remain a non-empty list")
    else:
        normalized_boundaries = "\n".join(boundaries).lower()
        if "staging" not in normalized_boundaries and "production" not in normalized_boundaries:
            errors.append("toolkit-contract.json: controlled-runtime staging/production boundary must remain explicit")
        if "accessibility" not in normalized_boundaries:
            errors.append("toolkit-contract.json: accessibility ownership boundary must remain explicit")
    return errors


def validate_visual_target_schema(root: Path):
    path = root / "contracts" / "visual-target.schema.json"
    if not path.is_file():
        return ["visual-target.schema.json: contract schema missing"]
    value, errors = load_object(path)
    if value is None:
        return errors
    required = value.get("required") if isinstance(value.get("required"), list) else []
    for key in ["evidence_class", "render_observed", "sections"]:
        if key not in required:
            errors.append(f"visual-target.schema.json: required boundary missing: {key}")
    properties = value.get("properties") if isinstance(value.get("properties"), dict) else {}
    if properties.get("evidence_class", {}).get("const") != "source_prediction":
        errors.append("visual-target.schema.json: evidence_class must be const source_prediction")
    if properties.get("render_observed", {}).get("const") is not False:
        errors.append("visual-target.schema.json: render_observed must be const false")
    labels = properties.get("provenance_labels", {}).get("items", {}).get("enum", [])
    if labels != ["explicit", "declared", "inferred", "unknown"]:
        errors.append("visual-target.schema.json: provenance labels must remain explicit/declared/inferred/unknown")
    return errors


def validate_workflow_wiring(root: Path):
    errors = []
    composition_path = root / ".github" / "workflows" / "composition-contract.yml"
    if not composition_path.is_file():
        return ["composition-contract.yml: workflow missing"]
    composition = composition_path.read_text(encoding="utf-8")
    for marker in COMPOSITION_WORKFLOW_MARKERS:
        if marker not in composition:
            errors.append(f"composition-contract.yml: required wiring missing: {marker}")

    toolkit_workflow_path = root / ".github" / "workflows" / "toolkit-contract.yml"
    if not toolkit_workflow_path.is_file():
        errors.append("toolkit-contract.yml: workflow missing")
    else:
        toolkit_workflow = toolkit_workflow_path.read_text(encoding="utf-8")
        if "contracts/**" not in toolkit_workflow:
            errors.append("toolkit-contract.yml: contract schema changes must trigger toolkit validation")
    return errors


def validate_repository_contracts(root=Path(".")):
    errors = []
    runtime_path = root / "runtime-contract.json"
    toolkit_path = root / "toolkit-contract.json"
    for path in [runtime_path, toolkit_path]:
        if not path.exists():
            errors.append(f"{path.name}: file missing")
    if errors:
        return errors

    runtime, runtime_errors = load_object(runtime_path)
    toolkit, toolkit_errors = load_object(toolkit_path)
    errors.extend(runtime_errors)
    errors.extend(toolkit_errors)
    if runtime is not None:
        errors.extend(validate_runtime(runtime))
    if toolkit is not None:
        errors.extend(validate_toolkit(toolkit, root))
    errors.extend(validate_visual_target_schema(root))
    errors.extend(validate_workflow_wiring(root))
    return errors


def main():
    errors = validate_repository_contracts()
    if errors:
        print("Repository contract validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Elementor repository contracts: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
