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
MAX_ELEMENT_DEPTH = 128
MAX_ELEMENTS = 20000
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
SITE_BOUND_KEY_FRAGMENTS = (
    "menu",
    "template",
    "popup",
    "query",
    "loop",
    "post_id",
    "product_id",
    "taxonomy",
    "form_id",
)


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
            if device not in {str(item) for item in allowed_devices}:
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


def nonempty(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def audit(template_path: Path, inventory_path: Optional[Path]) -> Dict[str, Any]:
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []

    try:
        document = load_json(template_path)
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema_version": "1.2",
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
            warnings.append({"code": "inventory_unreadable", "message": str(exc), "path": "$"})

    responsive_devices = runtime_responsive_devices(inventory_environment)
    if not isinstance(document, dict):
        return {
            "schema_version": "1.2",
            "template": str(template_path),
            "status": "fail",
            "errors": [{"code": "invalid_wrapper", "message": "Top-level JSON must be an object.", "path": "$"}],
            "warnings": warnings,
        }

    if not isinstance(document.get("content"), list):
        errors.append({"code": "missing_content", "message": "Top-level content must be an array.", "path": "$.content"})
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
    global_references: Set[str] = set()
    dynamic_references: Set[str] = set()
    site_bound_references: Set[str] = set()
    element_count = 0
    element_limit_reported = False

    def add_error(code: str, message: str, path: str) -> None:
        errors.append({"code": code, "message": message, "path": path})

    def add_warning(code: str, message: str, path: str) -> None:
        warnings.append({"code": code, "message": message, "path": path})

    def validate_atomic_prop(value: Any, path: str) -> None:
        if not isinstance(value, dict) or "$$type" not in value or "value" not in value:
            add_warning(
                "untyped_atomic_prop",
                "Atomic control/style values should use a typed object containing $$type and value unless a target export proves another shape.",
                path,
            )
            return
        prop_type = value.get("$$type")
        if not isinstance(prop_type, str) or not prop_type.strip():
            add_error("invalid_atomic_prop_type", "Atomic $$type must be a non-empty string.", f"{path}.$$type")

    def validate_atomic_styles(styles: Any, path: str) -> None:
        if not isinstance(styles, list):
            add_error("invalid_atomic_styles", "Atomic styles must be an array.", path)
            return
        for style_index, style in enumerate(styles):
            style_path = f"{path}[{style_index}]"
            if not isinstance(style, dict):
                add_error("invalid_atomic_style", "Atomic style entries must be objects.", style_path)
                continue
            if not isinstance(style.get("id"), str) or not style.get("id", "").strip():
                add_error("missing_atomic_style_id", "Atomic styles require a non-empty id.", f"{style_path}.id")
            variants = style.get("variants")
            if not isinstance(variants, list):
                add_error("invalid_atomic_variants", "Atomic style variants must be an array.", f"{style_path}.variants")
                continue
            for variant_index, variant in enumerate(variants):
                variant_path = f"{style_path}.variants[{variant_index}]"
                if not isinstance(variant, dict):
                    add_error("invalid_atomic_variant", "Atomic style variants must be objects.", variant_path)
                    continue
                meta = variant.get("meta")
                props = variant.get("props")
                if not isinstance(meta, dict):
                    add_error("invalid_atomic_variant_meta", "Atomic variant meta must be an object.", f"{variant_path}.meta")
                if not isinstance(props, dict):
                    add_error("invalid_atomic_variant_props", "Atomic variant props must be an object.", f"{variant_path}.props")
                    continue
                for prop_name, prop_value in props.items():
                    validate_atomic_prop(prop_value, f"{variant_path}.props.{prop_name}")

    def scan_nested_values(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}"
                if key == "__globals__":
                    if not isinstance(child, dict):
                        add_error("invalid_globals_map", "__globals__ must be an object.", child_path)
                    else:
                        for global_key, global_value in child.items():
                            if not isinstance(global_value, str) or not global_value.strip():
                                add_error("invalid_global_reference", "Global references must be non-empty strings.", f"{child_path}.{global_key}")
                            else:
                                global_references.add(global_value)
                if isinstance(child, str) and "{{" in child and "}}" in child:
                    dynamic_references.add(child_path)
                lowered = str(key).lower()
                if any(fragment in lowered for fragment in SITE_BOUND_KEY_FRAGMENTS) and nonempty(child):
                    site_bound_references.add(child_path)
                scan_nested_values(child, child_path)
        elif isinstance(value, list):
            repeater_ids: List[str] = []
            for index, child in enumerate(value):
                if isinstance(child, dict) and "_id" in child:
                    repeater_id = child.get("_id")
                    if not isinstance(repeater_id, str) or not repeater_id.strip():
                        add_error("invalid_repeater_id", "Repeater _id must be a non-empty string.", f"{path}[{index}]._id")
                    else:
                        repeater_ids.append(repeater_id)
                scan_nested_values(child, f"{path}[{index}]")
            duplicates = {item for item in repeater_ids if repeater_ids.count(item) > 1}
            for duplicate in sorted(duplicates):
                add_error("duplicate_repeater_id", f"Duplicate repeater _id: {duplicate}", path)
        elif isinstance(value, str) and "{{" in value and "}}" in value:
            dynamic_references.add(path)

    def visit(element: Any, path: str, depth: int = 0) -> None:
        nonlocal element_count, element_limit_reported
        if depth > MAX_ELEMENT_DEPTH:
            add_error("max_element_depth_exceeded", f"Element tree exceeds maximum depth {MAX_ELEMENT_DEPTH}.", path)
            return
        if not isinstance(element, dict):
            add_error("invalid_element", "Element entries must be objects.", path)
            return
        element_count += 1
        if element_count > MAX_ELEMENTS:
            if not element_limit_reported:
                add_error("max_elements_exceeded", f"Document exceeds maximum element count {MAX_ELEMENTS}.", path)
                element_limit_reported = True
            return

        element_id = element.get("id")
        el_type = element.get("elType")
        settings = element.get("settings", [])
        children = element.get("elements", [])
        widget_type = element.get("widgetType")

        if not isinstance(element_id, str) or not element_id.strip():
            add_error("missing_id", "Element id must be a non-empty string.", f"{path}.id")
        elif element_id in ids:
            add_error("duplicate_id", f"Duplicate element id: {element_id}", f"{path}.id")
        else:
            ids.add(element_id)
        if not isinstance(el_type, str) or not el_type:
            add_error("missing_el_type", "elType must be a non-empty string.", f"{path}.elType")

        if isinstance(settings, list):
            if settings:
                add_error("invalid_settings_list", "settings may be [] when empty; non-empty settings must be an object.", f"{path}.settings")
            settings_dict: Dict[str, Any] = {}
        elif isinstance(settings, dict):
            settings_dict = settings
        else:
            add_error("invalid_settings", "settings must be an object or an empty array.", f"{path}.settings")
            settings_dict = {}
        if not isinstance(children, list):
            add_error("invalid_children", "elements must be an array.", f"{path}.elements")
            children = []

        is_atomic = el_type in ATOMIC_LAYOUT_TYPES or (isinstance(widget_type, str) and widget_type.startswith("e-"))
        if is_atomic:
            families.add("atomic")
            version = element.get("version")
            if not isinstance(version, str) or not version.strip():
                add_error("missing_atomic_version", "Atomic elements/widgets require a schema version string.", f"{path}.version")
            if not isinstance(element.get("isInner"), bool):
                add_error("invalid_atomic_is_inner", "Atomic isInner must be boolean.", f"{path}.isInner")
            if not isinstance(element.get("editor_settings"), (list, dict)):
                add_error("invalid_atomic_editor_settings", "Atomic editor_settings must be an array or object.", f"{path}.editor_settings")
            if not isinstance(element.get("interactions"), list):
                add_error("invalid_atomic_interactions", "Atomic interactions must be an array.", f"{path}.interactions")
            validate_atomic_styles(element.get("styles"), f"{path}.styles")
            for setting_name, setting_value in settings_dict.items():
                if str(setting_name).startswith("_"):
                    continue
                validate_atomic_prop(setting_value, f"{path}.settings.{setting_name}")
        elif el_type in CLASSIC_LAYOUT_TYPES or (el_type == "widget" and isinstance(widget_type, str)):
            families.add("classic")

        for duplicate in style_variant_duplicates(element.get("styles")):
            add_error("duplicate_style_variant", f"Duplicate Atomic breakpoint/state variant: {duplicate}", f"{path}.styles")

        scan_nested_values(settings_dict, f"{path}.settings")
        if isinstance(element.get("editor_settings"), (dict, list)):
            scan_nested_values(element.get("editor_settings"), f"{path}.editor_settings")
        if isinstance(element.get("interactions"), list):
            scan_nested_values(element.get("interactions"), f"{path}.interactions")

        if el_type == "widget":
            if not isinstance(widget_type, str) or not widget_type:
                add_error("missing_widget_type", "Widget elements require widgetType.", f"{path}.widgetType")
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
                        "owner": classify_owner(runtime_widget) if available else {"owner": "unknown", "plugin_slug": None, "title": None},
                        "settings_used": [],
                        "unrecognized_settings": [],
                    },
                )
                finding["count"] += 1
                if inventory_supplied and not available:
                    add_error(
                        "missing_widget_dependency",
                        f"widgetType '{widget_type}' is not registered in the supplied runtime inventory.",
                        f"{path}.widgetType",
                    )
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
            visit(child, f"{path}.elements[{index}]", depth + 1)

    for index, element in enumerate(document.get("content", []) if isinstance(document.get("content"), list) else []):
        visit(element, f"$.content[{index}]")

    for widget_type, finding in widget_findings.items():
        finding["settings_used"] = sorted(widget_settings[widget_type])
        finding["unrecognized_settings"] = sorted(set(finding["unrecognized_settings"]))
        if finding["unrecognized_settings"]:
            add_warning(
                "unrecognized_widget_settings",
                f"{widget_type} uses settings not present in the runtime control inventory: " + ", ".join(finding["unrecognized_settings"]),
                "$",
            )

    if global_references and not inventory_supplied:
        add_warning(
            "unverified_global_references",
            "Template references Elementor globals; target Kit/global existence still requires target evidence.",
            "$",
        )
    if dynamic_references:
        add_warning(
            "dynamic_references_require_target",
            "Dynamic references were detected; object context, availability, escaping and privacy require target/staging verification.",
            "$",
        )
    if site_bound_references:
        add_warning(
            "site_bound_references_require_target",
            "Potential site-bound IDs/settings were detected; do not treat them as target-valid without target evidence.",
            "$",
        )

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
        "schema_version": "1.2",
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
        "globals": sorted(global_references),
        "dynamic_reference_paths": sorted(dynamic_references),
        "site_bound_reference_paths": sorted(site_bound_references),
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
