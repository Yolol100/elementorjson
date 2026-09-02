#!/usr/bin/env python3

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SPECIAL_SETTING_KEYS = {
    "__globals__", "_css_classes", "_element_id", "_animation", "_animation_delay",
    "_background_background", "_border_border", "_position", "_transform_rotate_popover",
    "_transform_scale_popover", "_transform_translate_popover",
}
LEGACY_RESPONSIVE_DEVICES = ("tablet", "mobile")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def runtime_responsive_devices(environment: Dict[str, Any]) -> Tuple[str, ...]:
    devices: List[str] = []
    active_devices = environment.get("active_devices")
    if isinstance(active_devices, list):
        devices.extend(str(d) for d in active_devices if str(d) and str(d) != "desktop")
    if not devices:
        active_breakpoints = environment.get("active_breakpoints")
        if isinstance(active_breakpoints, dict):
            devices.extend(str(d) for d in active_breakpoints if str(d) and str(d) != "desktop")
    if not devices:
        devices.extend(LEGACY_RESPONSIVE_DEVICES)
    return tuple(sorted(set(devices), key=lambda item: (-len(item), item)))


def normalize_control_name(setting_name: str, controls: Dict[str, Dict[str, Any]], responsive_devices: Tuple[str, ...]) -> Optional[str]:
    if setting_name in controls:
        return setting_name
    for device in responsive_devices:
        suffix = f"_{device}"
        if not setting_name.endswith(suffix):
            continue
        base = setting_name[:-len(suffix)]
        control = controls.get(base)
        if not isinstance(control, dict) or not control.get("responsive"):
            continue
        allowed = control.get("responsive_devices")
        if isinstance(allowed, list) and allowed and device not in {str(x) for x in allowed}:
            continue
        return base
    return None


def is_empty_noop(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repair_document(document: Dict[str, Any], inventory_doc: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    patched = copy.deepcopy(document)
    widgets = inventory_doc.get("widgets") if isinstance(inventory_doc, dict) else None
    environment = inventory_doc.get("environment", {}) if isinstance(inventory_doc, dict) else {}
    if not isinstance(widgets, dict):
        raise ValueError("Inventory must contain a widgets object.")

    responsive_devices = runtime_responsive_devices(environment if isinstance(environment, dict) else {})
    repairs: List[Dict[str, Any]] = []
    blocked: List[Dict[str, Any]] = []

    def visit(element: Any, path: str) -> None:
        if not isinstance(element, dict):
            return

        el_type = element.get("elType")
        widget_type = element.get("widgetType")
        settings = element.get("settings")

        if el_type == "widget" and isinstance(widget_type, str) and widget_type:
            runtime_widget = widgets.get(widget_type)
            if not isinstance(runtime_widget, dict):
                blocked.append({
                    "code": "missing_widget_dependency",
                    "path": f"{path}.widgetType",
                    "widget_type": widget_type,
                    "reason": "Widget is not registered in the exact runtime inventory; substitution is not safe.",
                })
            elif widget_type.startswith("e-"):
                # Atomic props/styles require their own typed schema/target proof.
                pass
            elif isinstance(settings, dict):
                controls = {
                    str(control.get("name")): control
                    for control in runtime_widget.get("controls", [])
                    if isinstance(control, dict) and control.get("name")
                }
                for setting_name in list(settings.keys()):
                    key = str(setting_name)
                    if key in SPECIAL_SETTING_KEYS or key.startswith("_"):
                        continue
                    if normalize_control_name(key, controls, responsive_devices) is not None:
                        continue
                    value = settings.get(setting_name)
                    if is_empty_noop(value):
                        before = copy.deepcopy(value)
                        del settings[setting_name]
                        repairs.append({
                            "code": "remove_empty_unrecognized_classic_setting",
                            "rule_id": "EJL-SAFE-001",
                            "path": f"{path}.settings.{key}",
                            "widget_type": widget_type,
                            "before": before,
                            "after": None,
                            "evidence": {
                                "elementor": environment.get("elementor") if isinstance(environment, dict) else None,
                                "elementor_pro": environment.get("elementor_pro") if isinstance(environment, dict) else None,
                                "inventory_schema": inventory_doc.get("schema_version"),
                            },
                        })
                    else:
                        blocked.append({
                            "code": "nonempty_unrecognized_setting",
                            "path": f"{path}.settings.{key}",
                            "widget_type": widget_type,
                            "value": copy.deepcopy(value),
                            "reason": "Unknown non-empty settings may carry behavior or compatibility data and are never auto-deleted.",
                        })

        children = element.get("elements")
        if isinstance(children, list):
            for index, child in enumerate(children):
                visit(child, f"{path}.elements[{index}]")

    content = patched.get("content")
    if isinstance(content, list):
        for index, element in enumerate(content):
            visit(element, f"$.content[{index}]")

    return patched, {
        "schema_version": "1.0",
        "status": "changed" if repairs else ("blocked" if blocked else "no_change"),
        "repairs": repairs,
        "blocked": blocked,
        "runtime": {
            "elementor": environment.get("elementor") if isinstance(environment, dict) else None,
            "elementor_pro": environment.get("elementor_pro") if isinstance(environment, dict) else None,
            "active_plugins": environment.get("active_plugins") if isinstance(environment, dict) else None,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply only allowlisted, reversible Elementor JSON repairs proven by an exact runtime widget/control inventory."
    )
    parser.add_argument("template", type=Path)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="Write patched JSON to a separate path; source is never modified.")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    try:
        document = load_json(args.template)
        inventory_doc = load_json(args.inventory)
        if not isinstance(document, dict):
            raise ValueError("Template root must be an object.")
        if not isinstance(inventory_doc, dict):
            raise ValueError("Inventory root must be an object.")
        patched, report = repair_document(document, inventory_doc)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"repair failed: {exc}", file=sys.stderr)
        return 2

    report["source"] = {
        "path": str(args.template),
        "sha256": sha256_path(args.template),
    }
    report["rollback"] = {
        "strategy": "restore_source_artifact",
        "source_sha256": report["source"]["sha256"],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(patched, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"status={report['status']} repairs={len(report['repairs'])} blocked={len(report['blocked'])}")
    return 0 if not report["blocked"] else 3


if __name__ == "__main__":
    sys.exit(main())
