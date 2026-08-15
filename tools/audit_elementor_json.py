#!/usr/bin/env python3

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

ATOMIC_LAYOUT_TYPES = {"e-div-block", "e-flexbox", "e-grid"}
CLASSIC_LAYOUT_TYPES = {"section", "column", "container"}
LEGACY_RESPONSIVE_DEVICES = ("tablet", "mobile")
MAX_ELEMENTS = 10000
MAX_DEPTH = 100
GLOBAL_REF_RE = re.compile(r"^globals/(colors|typography)\?id=([^&]+)$")
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


def classify_owner(widget: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "owner": widget.get("owner", "unknown"),
        "plugin_slug": widget.get("plugin_slug"),
        "title": widget.get("title"),
    }


def append_issue(collection: List[Dict[str, Any]], code: str, message: str, path: str) -> None:
    collection.append({"code": code, "message": message, "path": path})


def audit(template_path: Path, inventory_path: Optional[Path]) -> Dict[str, Any]:
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    site_bound_references: List[Dict[str, Any]] = []

    try:
        document = load_json(template_path)
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema_version": "1.2",
            "template": str(template_path),
            "status": "fail",
            "errors": [{"code": "invalid_json", "message": str(exc), "path": "$"}],
            "warnings": [],
            "site_bound_references": [],
        }

    inventory: Dict[str, Any] = {}
    inventory_environment: Dict[str, Any] = {}
    inventory_design_system: Dict[str, Any] = {}
    inventory_supplied = False

    if inventory_path:
        try:
            inventory_doc = load_json(inventory_path)
            if not isinstance(inventory_doc, dict) or not isinstance(inventory_doc.get("widgets"), dict):
                append_issue(warnings, "invalid_inventory_shape", "Inventory must be an object containing a widgets object.", "$")
            else:
                inventory = inventory_doc["widgets"]
                inventory_environment = inventory_doc.get("environment", {}) if isinstance(inventory_doc.get("environment"), dict) else {}
                inventory_design_system = inventory_doc.get("design_system", {}) if isinstance(inventory_doc.get("design_system"), dict) else {}
                inventory_supplied = True
        except (OSError, json.JSONDecodeError) as exc:
            append_issue(warnings, "inventory_unreadable", str(exc), "$")

    responsive_devices = runtime_responsive_devices(inventory_environment)

    if not isinstance(document, dict):
        return {
            "schema_version": "1.2",
            "template": str(template_path),
            "status": "fail",
            "errors": [{"code": "invalid_wrapper", "message": "Top-level JSON must be an object.", "path": "$"}],
            "warnings": warnings,
            "site_bound_references": [],
        }

    for key in ("title", "type", "version"):
        if not isinstance(document.get(key), str) or not document.get(key, "").strip():
            append_issue(errors, f"missing_{key}", f"Top-level {key} must be a non-empty string.", f"$.{key}")
    if isinstance(document.get("version"), str) and document.get("version") != "0.4":
        append_issue(warnings, "unexpected_document_version", "Current portable Elementor JSON uses document version 0.4; verify this export against its target runtime.", "$.version")
    if not isinstance(document.get("content"), list):
        append_issue(errors, "missing_content", "Top-level content must be an array.", "$.content")
    if "page_settings" not in document:
        append_issue(errors, "missing_page_settings", "Top-level page_settings is required.", "$.page_settings")
    elif not isinstance(document.get("page_settings"), (list, dict)):
        append_issue(errors, "invalid_page_settings", "page_settings must be an empty array or an object.", "$.page_settings")

    classic_globals = inventory_design_system.get("classic_globals", {}) if isinstance(inventory_design_system.get("classic_globals"), dict) else {}
    atomic_classes_block = inventory_design_system.get("atomic_global_classes", {}) if isinstance(inventory_design_system.get("atomic_global_classes"), dict) else {}
    atomic_class_inventory_known = inventory_supplied and isinstance(atomic_classes_block.get("ids"), list)
    atomic_class_ids = {str(item) for item in atomic_classes_block.get("ids", []) if str(item)} if atomic_class_inventory_known else set()

    ids: Set[str] = set()
    widget_counts: Counter[str] = Counter()
    widget_settings: Dict[str, Set[str]] = defaultdict(set)
    widget_findings: Dict[str, Dict[str, Any]] = {}
    families: Set[str] = set()
    element_count = 0
    stopped_for_limit = False

    def validate_typed_value(value: Any, path: str) -> None:
        if isinstance(value, dict):
            if "$$type" in value:
                prop_type = value.get("$$type")
                if not isinstance(prop_type, str) or not prop_type:
                    append_issue(errors, "invalid_atomic_prop_type", "Atomic $$type must be a non-empty string.", f"{path}.$$type")
                if "value" not in value:
                    append_issue(errors, "atomic_typed_prop_missing_value", "Atomic typed props require a value key.", path)
                    return
                if prop_type == "classes":
                    class_values = value.get("value")
                    if not isinstance(class_values, list) or not all(isinstance(item, str) and item for item in class_values):
                        append_issue(errors, "invalid_atomic_classes_prop", "Atomic classes props require a list of non-empty class IDs.", path)
                    else:
                        for class_id in class_values:
                            site_bound_references.append({"kind": "atomic_global_class", "id": class_id, "path": path})
                            if atomic_class_inventory_known and class_id not in atomic_class_ids:
                                append_issue(errors, "missing_atomic_global_class", f"Atomic global class '{class_id}' is not present in the supplied runtime inventory.", path)
                if prop_type in {"query", "dynamic"}:
                    site_bound_references.append({"kind": f"atomic_{prop_type}", "path": path})
                validate_typed_value(value.get("value"), f"{path}.value")
                return
            for key, nested in value.items():
                validate_typed_value(nested, f"{path}.{key}")
        elif isinstance(value, list):
            for index, nested in enumerate(value):
                validate_typed_value(nested, f"{path}[{index}]")

    def validate_repeaters(settings: Dict[str, Any], path: str) -> None:
        for setting_name, value in settings.items():
            if not isinstance(value, list) or not value:
                continue
            if not any(isinstance(item, dict) and "_id" in item for item in value):
                continue
            seen: Set[str] = set()
            for index, item in enumerate(value):
                item_path = f"{path}.{setting_name}[{index}]"
                if not isinstance(item, dict):
                    append_issue(errors, "invalid_repeater_item", "Repeater items must be objects.", item_path)
                    continue
                repeater_id = item.get("_id")
                if not isinstance(repeater_id, str) or not repeater_id.strip():
                    append_issue(errors, "missing_repeater_id", "Classic repeater items require a non-empty _id.", f"{item_path}._id")
                elif repeater_id in seen:
                    append_issue(errors, "duplicate_repeater_id", f"Duplicate repeater _id: {repeater_id}", f"{item_path}._id")
                else:
                    seen.add(repeater_id)

    def validate_globals(settings: Dict[str, Any], path: str) -> None:
        globals_value = settings.get("__globals__")
        if globals_value is None:
            return
        if not isinstance(globals_value, dict):
            append_issue(errors, "invalid_globals_shape", "settings.__globals__ must be an object.", f"{path}.__globals__")
            return
        for control_name, reference in globals_value.items():
            ref_path = f"{path}.__globals__.{control_name}"
            if not isinstance(reference, str):
                append_issue(errors, "invalid_global_reference", "Global references must be strings.", ref_path)
                continue
            match = GLOBAL_REF_RE.match(reference)
            if not match:
                append_issue(errors, "invalid_global_reference", f"Unsupported global reference: {reference}", ref_path)
                continue
            global_type, global_id = match.groups()
            site_bound_references.append({"kind": f"classic_global_{global_type}", "id": global_id, "path": ref_path})
            if inventory_supplied and isinstance(classic_globals.get(global_type), list):
                available = {str(item) for item in classic_globals[global_type]}
                if global_id not in available:
                    append_issue(errors, "missing_global_dependency", f"Global {global_type} ID '{global_id}' is not present in the supplied runtime Kit.", ref_path)

    def validate_atomic_styles(styles: Any, path: str) -> None:
        if isinstance(styles, list):
            style_items: Iterable[Any] = styles
        elif isinstance(styles, dict):
            style_items = styles.values()
        else:
            append_issue(errors, "invalid_atomic_styles", "Atomic styles must be an array or object.", path)
            return
        for style_index, style in enumerate(style_items):
            style_path = f"{path}[{style_index}]"
            if not isinstance(style, dict):
                append_issue(errors, "invalid_atomic_style", "Atomic style entries must be objects.", style_path)
                continue
            style_id = style.get("id")
            if not isinstance(style_id, str) or not style_id:
                append_issue(errors, "missing_atomic_style_id", "Atomic styles require a non-empty id.", f"{style_path}.id")
            if not isinstance(style.get("type"), str) or not style.get("type"):
                append_issue(errors, "missing_atomic_style_type", "Atomic styles require a non-empty type.", f"{style_path}.type")
            variants = style.get("variants")
            if not isinstance(variants, list):
                append_issue(errors, "invalid_atomic_style_variants", "Atomic style variants must be an array.", f"{style_path}.variants")
                continue
            seen: Set[Tuple[str, str]] = set()
            for variant_index, variant in enumerate(variants):
                variant_path = f"{style_path}.variants[{variant_index}]"
                if not isinstance(variant, dict):
                    append_issue(errors, "invalid_atomic_style_variant", "Atomic style variants must be objects.", variant_path)
                    continue
                meta = variant.get("meta")
                props = variant.get("props")
                if not isinstance(meta, dict) or "breakpoint" not in meta or "state" not in meta:
                    append_issue(errors, "invalid_atomic_style_meta", "Atomic style variant meta requires breakpoint and state keys.", f"{variant_path}.meta")
                    meta = {}
                if not isinstance(props, dict):
                    append_issue(errors, "invalid_atomic_style_props", "Atomic style variant props must be an object.", f"{variant_path}.props")
                    props = {}
                key = (str(meta.get("breakpoint", "")), json.dumps(meta.get("state"), sort_keys=True))
                if key in seen:
                    append_issue(errors, "duplicate_style_variant", f"Duplicate Atomic breakpoint/state variant: {key[0]}:{meta.get('state')}", f"{style_path}.variants")
                seen.add(key)
                for prop_name, prop_value in props.items():
                    prop_path = f"{variant_path}.props.{prop_name}"
                    if not isinstance(prop_value, dict) or "$$type" not in prop_value:
                        append_issue(warnings, "atomic_untyped_style_prop", "Atomic style props are expected to use typed $$type/value values; verify this value against the target schema.", prop_path)
                    validate_typed_value(prop_value, prop_path)

    def visit(element: Any, path: str, depth: int = 0) -> None:
        nonlocal element_count, stopped_for_limit
        if stopped_for_limit:
            return
        if depth > MAX_DEPTH:
            append_issue(errors, "maximum_depth_exceeded", f"Element nesting exceeds the safety limit of {MAX_DEPTH}.", path)
            stopped_for_limit = True
            return
        if not isinstance(element, dict):
            append_issue(errors, "invalid_element", "Element entries must be objects.", path)
            return
        element_count += 1
        if element_count > MAX_ELEMENTS:
            append_issue(errors, "maximum_elements_exceeded", f"Template exceeds the safety limit of {MAX_ELEMENTS} elements.", path)
            stopped_for_limit = True
            return

        element_id = element.get("id")
        el_type = element.get("elType")
        settings = element.get("settings", [])
        children = element.get("elements", [])
        widget_type = element.get("widgetType")

        if not isinstance(element_id, str) or not element_id.strip():
            append_issue(errors, "missing_id", "Element id must be a non-empty string.", f"{path}.id")
        elif element_id in ids:
            append_issue(errors, "duplicate_id", f"Duplicate element id: {element_id}", f"{path}.id")
        else:
            ids.add(element_id)
        if not isinstance(el_type, str) or not el_type:
            append_issue(errors, "missing_el_type", "elType must be a non-empty string.", f"{path}.elType")
        if "isInner" not in element or not isinstance(element.get("isInner"), bool):
            append_issue(errors, "invalid_is_inner", "isInner must be present and boolean.", f"{path}.isInner")

        if isinstance(settings, list):
            if settings:
                append_issue(errors, "invalid_settings_list", "settings may be [] when empty; non-empty settings must be an object.", f"{path}.settings")
            settings_dict: Dict[str, Any] = {}
        elif isinstance(settings, dict):
            settings_dict = settings
        else:
            append_issue(errors, "invalid_settings", "settings must be an object or an empty array.", f"{path}.settings")
            settings_dict = {}
        if not isinstance(children, list):
            append_issue(errors, "invalid_children", "elements must be an array.", f"{path}.elements")
            children = []

        is_atomic = (
            (isinstance(el_type, str) and el_type.startswith("e-"))
            or (isinstance(widget_type, str) and widget_type.startswith("e-"))
        )
        if is_atomic:
            families.add("atomic")
            version = element.get("version")
            if not isinstance(version, str) or not version:
                append_issue(errors, "missing_atomic_version", "Atomic elements require a non-empty version.", f"{path}.version")
            editor_settings = element.get("editor_settings")
            if not isinstance(editor_settings, (list, dict)):
                append_issue(errors, "invalid_atomic_editor_settings", "Atomic editor_settings must be an array or object.", f"{path}.editor_settings")
            interactions = element.get("interactions")
            if not isinstance(interactions, list):
                append_issue(errors, "invalid_atomic_interactions", "Atomic interactions must be an array.", f"{path}.interactions")
            if "styles" not in element:
                append_issue(errors, "missing_atomic_styles", "Atomic elements require styles, even when empty.", f"{path}.styles")
            else:
                validate_atomic_styles(element.get("styles"), f"{path}.styles")
            for setting_name, value in settings_dict.items():
                if setting_name in SPECIAL_SETTING_KEYS:
                    continue
                if not isinstance(value, dict) or "$$type" not in value:
                    append_issue(warnings, "atomic_untyped_setting", "Atomic control values are normally typed; verify this setting against the target widget schema.", f"{path}.settings.{setting_name}")
                validate_typed_value(value, f"{path}.settings.{setting_name}")
        elif el_type in CLASSIC_LAYOUT_TYPES or (el_type == "widget" and isinstance(widget_type, str)):
            families.add("classic")

        validate_repeaters(settings_dict, f"{path}.settings")
        validate_globals(settings_dict, f"{path}.settings")

        if el_type == "widget":
            if not isinstance(widget_type, str) or not widget_type:
                append_issue(errors, "missing_widget_type", "Widget elements require widgetType.", f"{path}.widgetType")
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
                    append_issue(errors, "missing_widget_dependency", f"widgetType '{widget_type}' is not registered in the supplied runtime inventory.", f"{path}.widgetType")
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
            append_issue(
                warnings,
                "unrecognized_widget_settings",
                f"{widget_type} uses settings not present in the runtime control inventory: " + ", ".join(finding["unrecognized_settings"]),
                "$",
            )

    if any(ref.get("kind") in {"atomic_query", "atomic_dynamic"} for ref in site_bound_references):
        append_issue(warnings, "target_context_required", "Dynamic/query references require target data/context evidence beyond this portable runtime.", "$")

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
        "inventory_design_system": inventory_design_system,
        "responsive_devices": list(responsive_devices),
        "summary": {
            "elements": element_count,
            "unique_ids": len(ids),
            "widgets": sum(widget_counts.values()),
            "widget_types": len(widget_counts),
            "site_bound_references": len(site_bound_references),
            "errors": len(errors),
            "warnings": len(warnings),
        },
        "dependencies": dict(sorted(dependency_counts.items())),
        "widgets": sorted(widget_findings.values(), key=lambda item: item["widget_type"]),
        "site_bound_references": site_bound_references,
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
            "elements={elements} widgets={widgets} widget_types={widget_types} site_bound={site_bound_references} errors={errors} warnings={warnings}".format(
                elements=summary.get("elements", 0),
                widgets=summary.get("widgets", 0),
                widget_types=summary.get("widget_types", 0),
                site_bound_references=summary.get("site_bound_references", 0),
                errors=summary.get("errors", 0),
                warnings=summary.get("warnings", 0),
            )
        )
    for finding in report.get("errors", []):
        print(f"ERROR {finding.get('code')}: {finding.get('message')}")
    for finding in report.get("warnings", []):
        print(f"WARN {finding.get('code')}: {finding.get('message')}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit an Elementor JSON export against an optional runtime widget/design-system inventory.")
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
