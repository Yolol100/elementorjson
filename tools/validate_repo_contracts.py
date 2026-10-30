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

AUTO_COMPOSITION_PATH_MARKERS = ["contracts/**", "sidecars/**", "templates/**"]

COMPOSITION_WORKFLOW_MARKERS = [
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
        ["contract_version", "repository", "default_branch", "workflow", "role", "caller", "trigger", "activation", "evidence", "privacy"],
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

    privacy = value.get("privacy") if isinstance(value.get("privacy"), dict) else {}
    if privacy.get("repository_visibility_assumption") != "public":
        errors.append("runtime-contract.json: privacy.repository_visibility_assumption must remain public")
    privacy_rule = privacy.get("rule") if isinstance(privacy.get("rule"), str) else ""
    if "public repository visibility" not in privacy_rule.lower():
        errors.append("runtime-contract.json: privacy rule must state that public visibility does not waive the data boundary")
    if "private repository" in json.dumps(value, ensure_ascii=False).lower():
        errors.append("runtime-contract.json: stale private-repository wording is not allowed for the public runtime")
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
        ids = [item.get("id") for item in tools if isinstance(item, dict) and isinstance(item.get("id"), str) and item["id"].strip()]
        if len(ids) != len(tools):
            errors.append("toolkit-contract.json: every tool requires a non-empty string ID")
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
            if not isinstance(assertion, dict) or not all(isinstance(assertion.get(key), str) and assertion[key].strip() for key in ("tool", "path", "contains")):
                errors.append("toolkit-contract.json: every usage assertion must bind tool/path/contains")
                continue
            assertion_tools.add(assertion["tool"])
            if assertion["tool"] not in ids:
                errors.append(f"toolkit-contract.json: unknown assertion tool at index {index}")
                continue
            relative = Path(assertion["path"])
            try:
                assertion_path = (root / relative).resolve()
                assertion_path.relative_to(root.resolve())
                if relative.is_absolute() or '..' in relative.parts or '\\' in assertion['path']:
                    raise ValueError('not a repository-relative path')
            except (ValueError, OSError, RuntimeError):
                errors.append(f"toolkit-contract.json: unsafe assertion path at index {index}")
                continue
            if not assertion_path.is_file():
                errors.append(f"toolkit-contract.json: usage assertion path missing at index {index}: {assertion['path']}")
                continue
            try:
                text = assertion_path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
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


def workflow_events(workflow: str):
    """Read event names from the top-level YAML 'on' block without a YAML dependency."""
    lines = workflow.splitlines()
    if "on:" not in lines:
        return []
    events = []
    for line in lines[lines.index("on:") + 1:]:
        if line and line[0] not in " \t#":
            break
        if line.startswith("  ") and not line.startswith(("   ", "  #")) and ":" in line:
            events.append(line.strip().split(":", 1)[0])
    return events


def workflow_event_body(workflow: str, event: str):
    """Return the source body of a top-level GitHub Actions event.

    Deliberately parse the simple literal on block used by this repository.
    If an event is moved or loses its branches or paths, acceptance must fail.
    """
    lines = workflow.splitlines()
    if "on:" not in lines:
        return ""
    started = False
    body = []
    for line in lines[lines.index("on:") + 1:]:
        if line and line[0] not in " \t#":
            break
        if line == f"  {event}:":
            started = True
            continue
        if started and line.startswith("  ") and not line.startswith(("   ", "  #")):
            break
        if started:
            body.append(line)
    return "\n".join(body)


def validate_workflow_wiring(root: Path):
    errors = []
    workflows = {}
    names = ("composition-contract.yml", "toolkit-contract.yml", "validate.yml",
             "native-kit-contract.yml", "codeql.yml")
    for name in names:
        path = root / ".github" / "workflows" / name
        if not path.is_file():
            errors.append(f"{name}: workflow missing")
            continue
        text = path.read_text(encoding="utf-8")
        workflows[name] = text
        events = workflow_events(text)
        required = ("workflow_dispatch", "push", "pull_request")
        if name == "codeql.yml":
            required += ("schedule",)
        for event in required:
            if event not in events:
                errors.append(f"{name}: {event} must remain available")
        for event in ("push", "pull_request"):
            body = workflow_event_body(text, event)
            if "    branches: [main]" not in body.splitlines():
                errors.append(f"{name}: {event} must target main explicitly")

    composition = workflows.get("composition-contract.yml", "")
    for marker in COMPOSITION_WORKFLOW_MARKERS:
        if marker not in composition:
            errors.append(f"composition-contract.yml: required wiring missing: {marker}")
    for event in ("push", "pull_request"):
        body = workflow_event_body(composition, event)
        for marker in AUTO_COMPOSITION_PATH_MARKERS:
            if f"      - '{marker}'" not in body.splitlines():
                errors.append(f"composition-contract.yml: required wiring missing: {marker} ({event})")

    toolkit = workflows.get("toolkit-contract.yml", "")
    for event in ("push", "pull_request"):
        body = workflow_event_body(toolkit, event)
        if "      - 'contracts/**'" not in body.splitlines():
            errors.append(
                f"toolkit-contract.yml: contract schema changes must trigger toolkit validation ({event})"
            )

    native = workflows.get("native-kit-contract.yml", "")
    for event in ("push", "pull_request"):
        body = workflow_event_body(native, event)
        for marker in (".wp-env.json", "wordpress-plugin/**", "templates/**",
                       "package.json", "package-lock.json"):
            if f"      - '{marker}'" not in body.splitlines():
                errors.append(f"native-kit-contract.yml: {event} path missing: {marker}")

    codeql = workflows.get("codeql.yml", "")
    for marker in ("security-events: write", "javascript-typescript",
                   "python", "actions", "security-extended"):
        if marker not in codeql:
            errors.append(f"codeql.yml: required scanning marker missing: {marker}")
    if "secrets." in codeql:
        errors.append("codeql.yml: do not access secrets in pull request analysis")

    # On a public repository, automatic pull_request/push checks execute
    # checked-out code; no Pro license may flow to those events. Preserve the
    # optional Pro contract exclusively for deliberate main-branch dispatch.
    qa = workflows.get("validate.yml", "")
    protected_pro_secret = "ELEMENTOR_PRO_LICENSE_KEY: ${{ github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/main' && secrets.ELEMENTOR_PRO_LICENSE_KEY || '' }}"
    if qa.count("secrets.ELEMENTOR_PRO_LICENSE_KEY") != 2 or qa.count(protected_pro_secret) != 2:
        errors.append(
            "validate.yml: Elementor Pro secret must be gated to manual workflow_dispatch on main"
        )
    return errors


def validate_dependency_security_override(root: Path):
    """Guard audited, exact transitive security pins in the existing npm dependency graph."""
    package, package_errors = load_object(root / "package.json")
    lock, lock_errors = load_object(root / "package-lock.json")
    errors = package_errors + lock_errors
    if package is not None:
        overrides = package.get("overrides")
        if not isinstance(overrides, dict) or overrides.get("argparse") != "2.0.1":
            errors.append("package.json: argparse must be overridden to 2.0.1")
        for name, version in (("body-parser", "1.20.9"), ("fast-uri", "3.1.9"), ("qs", "6.17.1")):
            if not isinstance(overrides, dict) or overrides.get(name) != version:
                errors.append(f"package.json: {name} must be overridden to {version}")
    if lock is not None:
        packages = lock.get("packages")
        if not isinstance(packages, dict):
            errors.append("package-lock.json: packages map missing")
        else:
            if "node_modules/sprintf-js" in packages:
                errors.append("package-lock.json: unpatched sprintf-js must not be installed")
            argparse = packages.get("node_modules/argparse")
            if not isinstance(argparse, dict) or argparse.get("version") != "2.0.1":
                errors.append("package-lock.json: pinned argparse version must be 2.0.1")
            for name, version in (("body-parser", "1.20.9"), ("fast-uri", "3.1.9"), ("qs", "6.17.1")):
                entry = packages.get(f"node_modules/{name}")
                if not isinstance(entry, dict) or entry.get("version") != version:
                    errors.append(f"package-lock.json: {name} must be pinned to {version}")
                elif not isinstance(entry.get("integrity"), str) or not entry["integrity"].startswith("sha512-"):
                    errors.append(f"package-lock.json: {name} must retain npm sha512 integrity")
            qs = packages.get("node_modules/qs")
            if isinstance(qs, dict) and qs.get("integrity") != "sha512-jd3COkaKVgGUW+ZHyEHCG9bH7RoaaiWuMgzsIBjUMVjLAaWGWpoUAVwljVvBHxRu/2qEHnadLGZrkutYUBPQJA==":
                errors.append("package-lock.json: qs must retain audited sha512 integrity")
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
    integration_path = root / "docs" / "project-elementor-integration.md"
    if not integration_path.is_file():
        errors.append("project-elementor-integration.md: file missing")
    else:
        integration = integration_path.read_text(encoding="utf-8")
        if "repository is private" in integration.lower():
            errors.append("project-elementor-integration.md: stale private repository statement")
        if "the repository is public." not in integration.lower():
            errors.append("project-elementor-integration.md: public repository boundary must remain explicit")
    errors.extend(validate_workflow_wiring(root))
    errors.extend(validate_dependency_security_override(root))
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
