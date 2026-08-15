#!/usr/bin/env python3

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

ATOMIC_LAYOUT_TYPES = {"e-div-block", "e-flexbox", "e-grid"}
CLASSIC_LAYOUT_TYPES = {"section", "column", "container"}
LEGACY_RESPONSIVE_DEVICES = ("tablet", "mobile")
SPECIAL_SETTING_KEYS = {
    "__globals__",
    "_css_classes",
    "_element_id",
    "_animation",
    "_animation_delay",
    "_background_background",
    "_border_border",
    "_position",
    "_transform_rotate_popover",
    "_transform_scale_popover",
    "_transform_translate_popover",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def runtime_responsive_devices(environment: Dict[str, Any]) -> Tuple[str, ...]:
    devices: List[str] = []

    active_devices = environment.get("active_devices")
    if isinstance(active_devices, list):
        devices.extend(
            str(device)
            for device in active_devices
            if isinstance(device, (str, int)) and str(device) and str(device) != "desktop"
        )

    if not devices:
        active_breakpoints = environment.get("active_breakpoints")
        if isinstance(active_breakpoints, dict):
            devices.extend(str(device) for device in active_breakpoints.keys() if str(device) and str(device) != "desktop")

    if not devices:
        devices.extend(LEGACY_RESPONSIVE_DEVICES)

    # Longest first so `mobile_extra` is tested before `mobile`.
    return tuple(sorted(set(devices), key=lambda item: (-len(item), item)))


def normalize_control_name(
    setting_name: str,
    controls: Dict[str, Dict[str, Any]],
    responsive_devices: Tuple[str, ...],
) -> Optional[str]:
    if setting_name in controls:
        return setting_name

    for device in responsive_devices:
        suffix = f"_{device}"
        if not setting_name.endswith(suffix):
            continue

        base = setting_name[: -len(suffix)]
        control = controls.get(base)
        if not isinstance(control, dict) or not control.get("responsive"):
            continue

        allowed_devices = control.get("responsive_devices")
        if isinstance(allowed_devices, list) and allowed_devices:
            normalized_allowed = {str(item) for item in allowed_devices}
            if device not in normalized_allowed:
                continue

        return base

    return None


def style_variant_duplicates(styles: Any) -> List[str]:
    duplicates: List[str] = []
    style_items: Iterable[Any]

    if isinstance(styles, list):
        style_items = styles
    elif isinstance(styles, dict):
        style_items = styles.values()
    else:
        return duplicates

    for style in style_items:
        if not isinstance(style, dict):
            continue

        style_id = str(style.get("id", "unknown-style"))
        variants = style.get("variants")
        if not isinstance(variants, list):
            continue

        seen: Set[Tuple[str, str]] = set()
        for variant in variants:
            if not isinstance(variant, dict):
                continue
            meta = variant.get("meta") if isinstance(variant.get("meta"), dict) else {}
            key = (str(meta.get("breakpoint", "")), str(meta.get("state", "")))
            if key in seen:
                duplicates.append(f"{style_id}:{key[0]}:{key[1]}")
            seen.add(key)

    return duplicates


def classify_owner(widget: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "owner": widget.get("owner", "unknown"),
        "plugin_slug": widget.get("plugin_slug"),
        "title": widget.get("title"),
    }


def audit(template_path: Path, inventory_path: Optional[Path]) -> Dict[str, Any]:
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []

    try:
        document = load_json(template_path)
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema_version": "1.0",
            "template": str(template_path),
            "status": "fail",
            "errors": [{"code": "invalid_json", "message": str(exc), "path": "$"}],
            "warnings": [],
        }

    inventory: Dict[str, Any] = {}
    inventory_environment: Dict[str, Any] = {}
    inventory_supplied = False

    if inventory_path:
        try:
            inventory_doc = load_json(inventory_path)
            if not isinstance(inventory_doc, dict) or not isinstance(inventory_doc.get("widgets"), dict):
                warnings.append({
                    "code": "invalid_inventory_shape",
                    "message": "Inventory must be an object containing a widgets object.",
                    "path": "$",
                })
            else:
                inventory = inventory_doc["widgets"]
                inventory_environment = inventory_doc.get("environment", {}) if isinstance(inventory_doc.get("environment"), dict) else {}
                inventory_supplied = True
        except (OSError, json.JSONDecodeError) as exc:
            warnings.append({
                "code": "inventory_unreadable",
                "message": str(exc),
                "path": "$",
            })

    responsive_devices = runtime_responsive_devices(inventory_environment)

    if not isinstance(document, dict):
        return {
            "schema_version": "1.0",
            "template": str(template_path),
            "status": "fail",
            "errors": [{"code": "invalid_wrapper", "message": "Top-level JSON must be an object.", "path": "$"}],
            "warnings": warnings,
        }

    if not isinstance(document.get("content"), list):
        errors.append({
            "code": "missing_content",
            "message": "Top-level content must be an array.",
            "path": "$.content",
        })

    if "page_settings" in document and not isinstance(document.get("page_settings"), (list, dict)):
        errors.append({
            "code": "invalid_page_settings",
            "message": "page_settings must be an empty array or an object.",
            "path": "$.page_settings",
        })

    ids: Set[str] = set()
    widget_counts: Counter[str] = Counter()
    widget_settings: Dict[str, Set[str]] = defaultdict(set)
    widget_findings: Dict[str, Dict[str, Any]] = {}
    families: Set[str] = set()
    element_count = 0

    def visit(element: Any, path: str) -> None:
        nonlocal element_count

        if not isinstance(element, dict):
            errors.append({
                "code": "invalid_element",
                "message": "Element entries must be objects.",
                "path": path,
            })
            return

        element_count += 1
        element_id = element.get("id")
        el_type = element.get("elType")
        settings = element.get("settings", [])
        children = element.get("elements", [])
        widget_type = element.get("widgetType")

        if not isinstance(element_id, str) or not element_id.strip():
            errors.append({
                "code": "missing_id",
                "message": "Element id must be a non-empty string.",
                "path": f"{path}.id",
            })
        elif element_id in ids:
            errors.append({
                "code": "duplicate_id",
                "message": f"Duplicate element id: {element_id}",
                "path": f"{path}.id",
            })
        else:
            ids.add(element_id)

        if not isinstance(el_type, str) or not el_type:
            errors.append({
                "code": "missing_el_type",
                "message": "elType must be a non-empty string.",
                "path": f"{path}.elType",
            })

        if isinstance(settings, list):
            if settings:
                errors.append({
                    "code": "invalid_settings_list",
                    "message": "settings may be [] when empty; non-empty settings must be an object.",
                    "path": f"{path}.settings",
                })
            settings_dict: Dict[str, Any] = {}
        elif isinstance(settings, dict):
            settings_dict = settings
        else:
            errors.append({
                "code": "invalid_settings",
                "message": "settings must be an object or an empty array.",
                "path": f"{path}.settings",
            })
            settings_dict = {}

        if not isinstance(children, list):
            errors.append({
                "code": "invalid_children",
                "message": "elements must be an array.",
                "path": f"{path}.elements",
            })
            children = []

        if el_type in ATOMIC_LAYOUT_TYPES or (isinstance(widget_type, str) and widget_type.startswith("e-")):
            families.add("atomic")
        elif el_type in CLASSIC_LAYOUT_TYPES or (el_type == "widget" and isinstance(widget_type, str)):
            families.add("classic")

        duplicates = style_variant_duplicates(element.get("styles"))
        for duplicate in duplicates:
            errors.append({
                "code": "duplicate_style_variant",
                "message": f"Duplicate Atomic breakpoint/state variant: {duplicate}",
                "path": f"{path}.styles",
            })

        if el_type == "widget":
            if not isinstance(widget_type, str) or not widget_type:
                errors.append({
                    "code": "missing_widget_type",
                    "message": "Widget elements require widgetType.",
                    "path": f"{path}.widgetType",
                })
            else:
                widget_counts[widget_type] += 1
                widget_settings[widget_type].update(str(key) for key in settings_dict.keys())

                runtime_widget = inventory.get(widget_type) if inventory_supplied else None
                available = isinstance(runtime_widget, dict)
                finding = widget_findings.setdefault(
                    widget_type,
                    {
                        "widget_type": widget_type,
                        "count": 0,
                        "available": available if inventory_supplied else None,
                        "owner": classify_owner(runtime_widget) if available else {
                            "owner": "unknown",
                            "plugin_slug": None,
                            "title": None,
                        },
                        "settings_used": [],
                        "unrecognized_settings": [],
                    },
                )
                finding["count"] += 1

                if inventory_supplied and not available:
                    errors.append({
                        "code": "missing_widget_dependency",
                        "message": f"widgetType '{widget_type}' is not registered in the supplied runtime inventory.",
                        "path": f"{path}.widgetType",
                    })

                if available:
                    controls = {
                        str(control.get("name")): control
                        for control in runtime_widget.get("controls", [])
                        if isinstance(control, dict) and control.get("name")
                    }
                    for setting_name in settings_dict.keys():
                        setting_name = str(setting_name)
                        if setting_name in SPECIAL_SETTING_KEYS or setting_name.startswith("_"):
                            continue
                        if normalize_control_name(setting_name, controls, responsive_devices) is None:
                            finding["unrecognized_settings"].append(setting_name)

        for index, child in enumerate(children):
            visit(child, f"{path}.elements[{index}]")

    for index, element in enumerate(document.get("content", []) if isinstance(document.get("content"), list) else []):
        visit(element, f"$.content[{index}]")

    for widget_type, finding in widget_findings.items():
        finding["settings_used"] = sorted(widget_settings[widget_type])
        finding["unrecognized_settings"] = sorted(set(finding["unrecognized_settings"]))
        if finding["unrecognized_settings"]:
            warnings.append({
                "code": "unrecognized_widget_settings",
                "message": (
                    f"{widget_type} uses settings not present in the runtime control inventory: "
                    + ", ".join(finding["unrecognized_settings"])
                ),
                "path": "$",
            })

    if families == {"classic", "atomic"}:
        editor_family = "mixed"
    elif families == {"atomic"}:
        editor_family = "atomic"
    elif families == {"classic"}:
        editor_family = "classic"
    else:
        editor_family = "unknown"

    dependency_counts: Counter[str] = Counter()
    for finding in widget_findings.values():
        owner = finding["owner"].get("owner", "unknown")
        plugin_slug = finding["owner"].get("plugin_slug")
        key = owner if not plugin_slug or owner in {"elementor-core", "elementor-pro"} else f"{owner}:{plugin_slug}"
        dependency_counts[key] += finding["count"]

    status = "fail" if errors else ("warning" if warnings else "pass")

    return {
        "schema_version": "1.1",
        "template": str(template_path),
        "status": status,
        "document": {
            "title": document.get("title"),
            "type": document.get("type"),
            "version": document.get("version"),
            "editor_family": editor_family,
        },
        "inventory_environment": inventory_environment,
        "responsive_devices": list(responsive_devices),
        "summary": {
            "elements": element_count,
            "unique_ids": len(ids),
            "widgets": sum(widget_counts.values()),
            "widget_types": len(widget_counts),
            "errors": len(errors),
            "warnings": len(warnings),
        },
        "dependencies": dict(sorted(dependency_counts.items())),
        "widgets": sorted(widget_findings.values(), key=lambda item: item["widget_type"]),
        "errors": errors,
        "warnings": warnings,
    }


def print_summary(report: Dict[str, Any]) -> None:
    summary = report.get("summary", {})
    print(f"status={report.get('status', 'unknown')}")
    print(f"template={report.get('template', '')}")
    document = report.get("document", {})
    if document:
        print(f"editor_family={document.get('editor_family', 'unknown')}")
    if summary:
        print(
            "elements={elements} widgets={widgets} widget_types={widget_types} errors={errors} warnings={warnings}".format(
                elements=summary.get("elements", 0),
                widgets=summary.get("widgets", 0),
                widget_types=summary.get("widget_types", 0),
                errors=summary.get("errors", 0),
                warnings=summary.get("warnings", 0),
            )
        )

    for finding in report.get("errors", []):
        print(f"ERROR {finding.get('code')}: {finding.get('message')}")
    for finding in report.get("warnings", []):
        print(f"WARN {finding.get('code')}: {finding.get('message')}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit an Elementor JSON export against an optional runtime widget inventory.")
    parser.add_argument("template", type=Path)
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--fail-on-warning", action="store_true")
    args = parser.parse_args()

    report = audit(args.template, args.inventory)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print_summary(report)

    if report.get("status") == "fail":
        return 1
    if args.fail_on_warning and report.get("status") == "warning":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
