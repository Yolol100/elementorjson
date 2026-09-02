#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

SURFACES = (
    "widgets",
    "elements",
    "document_types",
    "dynamic_tags",
    "experiments",
    "atomic_style_schema",
    "atomic_dynamic_tags",
    "global_classes",
    "variables",
    "components",
    "interactions",
)
ENV_KEYS = ("wordpress", "php", "elementor", "elementor_pro", "theme", "theme_version", "active_devices", "active_breakpoints")


def load_json(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def plugins_by_basename(environment: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for item in environment.get("active_plugins", []) if isinstance(environment.get("active_plugins"), list) else []:
        if not isinstance(item, dict):
            continue
        basename = str(item.get("basename") or "")
        if basename:
            result[basename] = item
    return result


def compare_plugins(before_env: Dict[str, Any], after_env: Dict[str, Any]) -> Dict[str, Any]:
    before = plugins_by_basename(before_env)
    after = plugins_by_basename(after_env)
    common = sorted(set(before) & set(after))
    version_changed: List[Dict[str, Any]] = []
    for basename in common:
        old_version = before[basename].get("version")
        new_version = after[basename].get("version")
        if old_version != new_version:
            version_changed.append({"basename": basename, "before": old_version, "after": new_version})
    return {
        "added": sorted(set(after) - set(before)),
        "removed": sorted(set(before) - set(after)),
        "version_changed": version_changed,
    }


def compare_surface(before: Any, after: Any) -> Dict[str, Any]:
    before_map = before if isinstance(before, dict) else {}
    after_map = after if isinstance(after, dict) else {}
    before_keys = set(before_map)
    after_keys = set(after_map)
    changed = sorted(key for key in before_keys & after_keys if before_map[key] != after_map[key])
    return {
        "added": sorted(after_keys - before_keys),
        "removed": sorted(before_keys - after_keys),
        "changed": changed,
    }


def compare(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
    before_env = before.get("environment") if isinstance(before.get("environment"), dict) else {}
    after_env = after.get("environment") if isinstance(after.get("environment"), dict) else {}

    environment_changes = {
        key: {"before": before_env.get(key), "after": after_env.get(key)}
        for key in ENV_KEYS
        if before_env.get(key) != after_env.get(key)
    }
    plugin_changes = compare_plugins(before_env, after_env)
    surface_changes = {name: compare_surface(before.get(name), after.get(name)) for name in SURFACES}

    removed_capabilities = sum(len(item["removed"]) for item in surface_changes.values())
    changed_capabilities = sum(len(item["changed"]) for item in surface_changes.values())
    added_capabilities = sum(len(item["added"]) for item in surface_changes.values())
    plugin_drift = bool(plugin_changes["added"] or plugin_changes["removed"] or plugin_changes["version_changed"])
    changed = bool(environment_changes or plugin_drift or removed_capabilities or changed_capabilities or added_capabilities)

    if removed_capabilities or changed_capabilities or plugin_changes["removed"]:
        impact = "review_required"
    elif changed:
        impact = "drift_detected"
    else:
        impact = "no_change"

    return {
        "schema_version": "1.1",
        "status": "changed" if changed else "no_change",
        "impact": impact,
        "environment": environment_changes,
        "plugins": plugin_changes,
        "capabilities": surface_changes,
        "summary": {
            "added_capabilities": added_capabilities,
            "removed_capabilities": removed_capabilities,
            "changed_capabilities": changed_capabilities,
            "plugin_drift": plugin_drift,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare two Elementor runtime capability inventories.")
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--fail-on-review", action="store_true")
    args = parser.parse_args()

    try:
        report = compare(load_json(args.before), load_json(args.after))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")

    print(f"status={report['status']} impact={report['impact']}", file=sys.stderr)
    if args.fail_on_review and report["impact"] == "review_required":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
