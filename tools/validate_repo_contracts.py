#!/usr/bin/env python3
import json
import sys
from pathlib import Path


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
    return errors


def validate_toolkit(value):
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
    if not isinstance(tools, list) or not tools:
        errors.append("toolkit-contract.json: tools must be a non-empty list")
    else:
        ids = [item.get("id") for item in tools if isinstance(item, dict)]
        for required_tool in ["elementor-json-auditor", "deep-json-validator", "wp-env", "elementor-core", "template-library-import", "semantic-roundtrip", "playwright"]:
            if required_tool not in ids:
                errors.append(f"toolkit-contract.json: required tool missing: {required_tool}")
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
        errors.extend(validate_toolkit(toolkit))
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
