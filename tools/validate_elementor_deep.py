#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

ATOMIC_LAYOUT_TYPES = {"e-div-block", "e-flexbox", "e-grid"}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def is_typed_prop(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and isinstance(value.get("$$type"), str)
        and bool(value.get("$$type"))
        and "value" in value
    )


def iter_styles(styles: Any) -> Iterable[Tuple[str, Dict[str, Any]]]:
    if isinstance(styles, list):
        for index, style in enumerate(styles):
            if isinstance(style, dict):
                yield f"[{index}]", style
    elif isinstance(styles, dict):
        for key, style in styles.items():
            if isinstance(style, dict):
                yield f".{key}", style


def validate_document(document: Any) -> Dict[str, Any]:
    errors: List[Dict[str, str]] = []
    warnings: List[Dict[str, str]] = []
    families = set()
    atomic_elements = 0
    repeater_ids = 0

    def error(code: str, message: str, path: str) -> None:
        errors.append({"code": code, "message": message, "path": path})

    def warning(code: str, message: str, path: str) -> None:
        warnings.append({"code": code, "message": message, "path": path})

    def scan_repeaters(value: Any, path: str) -> None:
        nonlocal repeater_ids
        if isinstance(value, list):
            ids = []
            for index, item in enumerate(value):
                if isinstance(item, dict) and "_id" in item:
                    item_id = item.get("_id")
                    if isinstance(item_id, str) and item_id:
                        ids.append((item_id, f"{path}[{index}]._id"))
                        repeater_ids += 1
                scan_repeaters(item, f"{path}[{index}]")
            seen = set()
            for item_id, item_path in ids:
                if item_id in seen:
                    error(
                        "duplicate_repeater_id",
                        f"Duplicate repeater _id '{item_id}'.",
                        item_path,
                    )
                seen.add(item_id)
        elif isinstance(value, dict):
            for key, child in value.items():
                scan_repeaters(child, f"{path}.{key}")

    def validate_atomic(element: Dict[str, Any], path: str) -> None:
        nonlocal atomic_elements
        atomic_elements += 1

        version = element.get("version")
        if not isinstance(version, str) or not version:
            error("atomic_missing_version", "Atomic elements require a non-empty version string.", f"{path}.version")

        if not isinstance(element.get("isInner"), bool):
            error("atomic_invalid_is_inner", "Atomic elements require boolean isInner.", f"{path}.isInner")

        editor_settings = element.get("editor_settings")
        if not isinstance(editor_settings, (list, dict)):
            error(
                "atomic_invalid_editor_settings",
                "Atomic editor_settings must be an array or object.",
                f"{path}.editor_settings",
            )

        interactions = element.get("interactions")
        if not isinstance(interactions, list):
            error("atomic_invalid_interactions", "Atomic interactions must be an array.", f"{path}.interactions")

        settings = element.get("settings")
        if isinstance(settings, list):
            if settings:
                error("atomic_invalid_settings", "Atomic settings may be [] only when empty.", f"{path}.settings")
        elif isinstance(settings, dict):
            for key, value in settings.items():
                if not is_typed_prop(value):
                    error(
                        "atomic_untyped_setting",
                        f"Atomic setting '{key}' must use a typed {{$$type, value}} prop.",
                        f"{path}.settings.{key}",
                    )
        else:
            error("atomic_invalid_settings", "Atomic settings must be an object or empty array.", f"{path}.settings")

        styles = element.get("styles")
        if not isinstance(styles, (list, dict)):
            error("atomic_invalid_styles", "Atomic styles must be an array or object.", f"{path}.styles")
            return

        for suffix, style in iter_styles(styles):
            style_path = f"{path}.styles{suffix}"
            style_id = style.get("id")
            if not isinstance(style_id, str) or not style_id:
                error("atomic_style_missing_id", "Atomic styles require a non-empty id.", f"{style_path}.id")

            variants = style.get("variants")
            if not isinstance(variants, list):
                error("atomic_style_invalid_variants", "Atomic style variants must be an array.", f"{style_path}.variants")
                continue

            seen_variants = set()
            for index, variant in enumerate(variants):
                variant_path = f"{style_path}.variants[{index}]"
                if not isinstance(variant, dict):
                    error("atomic_style_invalid_variant", "Atomic style variants must be objects.", variant_path)
                    continue
                meta = variant.get("meta")
                props = variant.get("props")
                if not isinstance(meta, dict) or "breakpoint" not in meta or "state" not in meta:
                    error(
                        "atomic_style_invalid_meta",
                        "Atomic style variant meta requires breakpoint and state keys.",
                        f"{variant_path}.meta",
                    )
                else:
                    variant_key = (str(meta.get("breakpoint")), json.dumps(meta.get("state"), sort_keys=True))
                    if variant_key in seen_variants:
                        error(
                            "duplicate_style_variant",
                            "Atomic style contains a duplicate breakpoint/state variant.",
                            f"{variant_path}.meta",
                        )
                    seen_variants.add(variant_key)

                if not isinstance(props, dict):
                    error("atomic_style_invalid_props", "Atomic style variant props must be an object.", f"{variant_path}.props")
                    continue
                for prop_name, prop_value in props.items():
                    if not is_typed_prop(prop_value):
                        error(
                            "atomic_untyped_style_prop",
                            f"Atomic style prop '{prop_name}' must use a typed {{$$type, value}} prop.",
                            f"{variant_path}.props.{prop_name}",
                        )

    def visit(element: Any, path: str) -> None:
        if not isinstance(element, dict):
            return

        el_type = element.get("elType")
        widget_type = element.get("widgetType")
        atomic = el_type in ATOMIC_LAYOUT_TYPES or (
            el_type == "widget" and isinstance(widget_type, str) and widget_type.startswith("e-")
        )

        if atomic:
            families.add("atomic")
            validate_atomic(element, path)
        elif isinstance(el_type, str):
            families.add("classic")

        settings = element.get("settings")
        if isinstance(settings, dict):
            globals_map = settings.get("__globals__")
            if isinstance(globals_map, dict) and globals_map:
                warning(
                    "unverified_global_references",
                    "Classic __globals__ references require a target Kit/design-system check.",
                    f"{path}.settings.__globals__",
                )
            scan_repeaters(settings, f"{path}.settings")

        children = element.get("elements")
        if isinstance(children, list):
            for index, child in enumerate(children):
                visit(child, f"{path}.elements[{index}]")

    if not isinstance(document, dict):
        error("invalid_wrapper", "Top-level JSON must be an object.", "$")
    else:
        content = document.get("content")
        if isinstance(content, list):
            for index, element in enumerate(content):
                visit(element, f"$.content[{index}]")

    if families == {"classic", "atomic"}:
        editor_family = "mixed"
    elif families == {"atomic"}:
        editor_family = "atomic"
    elif families == {"classic"}:
        editor_family = "classic"
    else:
        editor_family = "unknown"

    return {
        "schema_version": "1.0",
        "status": "fail" if errors else ("warning" if warnings else "pass"),
        "editor_family": editor_family,
        "summary": {
            "atomic_elements": atomic_elements,
            "repeater_ids": repeater_ids,
            "errors": len(errors),
            "warnings": len(warnings),
        },
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Deep structural checks for Classic and Atomic Elementor JSON.")
    parser.add_argument("template", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--fail-on-warning", action="store_true")
    args = parser.parse_args()

    try:
        document = load_json(args.template)
    except (OSError, json.JSONDecodeError) as exc:
        report = {
            "schema_version": "1.0",
            "status": "fail",
            "editor_family": "unknown",
            "summary": {"atomic_elements": 0, "repeater_ids": 0, "errors": 1, "warnings": 0},
            "errors": [{"code": "invalid_json", "message": str(exc), "path": "$"}],
            "warnings": [],
        }
    else:
        report = validate_document(document)

    report["template"] = str(args.template)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"status={report['status']} editor_family={report['editor_family']} errors={report['summary']['errors']} warnings={report['summary']['warnings']}")
    for item in report["errors"]:
        print(f"ERROR {item['code']}: {item['message']} ({item['path']})")
    for item in report["warnings"]:
        print(f"WARN {item['code']}: {item['message']} ({item['path']})")

    if report["status"] == "fail":
        return 1
    if args.fail_on_warning and report["status"] == "warning":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
