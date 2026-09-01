#!/usr/bin/env python3
"""Build a deterministic source-level visual target from Elementor JSON.

The output is a prediction contract for ChatGPT/review tooling. It never claims
that a browser actually rendered the predicted result. Values are labelled as
explicit, declared, inferred, or unknown to keep uncertainty visible.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "1.0"
TEXT_KEYS = {
    "title", "text", "editor", "description", "button_text", "heading", "paragraph",
    "ekit_funfact_title_text", "testimonial_content", "testimonial_name",
}
MEDIA_KEYS = {"image", "background_image", "background_video", "video", "media", "icon"}
LAYOUT_KEYS = {
    "display": ("display", "container_type", "layout_type"),
    "direction": ("flex_direction", "direction"),
    "justify": ("flex_justify_content", "justify_content", "content_position"),
    "align": ("flex_align_items", "align_items", "align", "text_align"),
    "wrap": ("flex_wrap", "wrap"),
    "gap": ("gap", "flex_gap", "grid_gap", "column_gap", "row_gap"),
    "width": ("width", "_element_width", "content_width", "flex_basis"),
    "min_height": ("min_height", "height"),
    "grid_columns": ("grid_columns", "grid_template_columns", "columns"),
    "position": ("position", "_position"),
}
STYLE_KEYS = {
    "background": ("background_background", "background_color", "background_overlay_color"),
    "padding": ("padding", "_padding"),
    "margin": ("margin", "_margin"),
    "border_radius": ("border_radius", "_border_radius"),
    "color": ("color", "text_color", "title_color"),
    "typography": ("typography_typography", "typography_font_family", "typography_font_size"),
}
RESPONSIVE_SUFFIXES = {"desktop": "", "tablet": "_tablet", "mobile": "_mobile"}


def _load(path: str | None) -> Any:
    if not path:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _walk(node: Any) -> Iterable[dict[str, Any]]:
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk(value)


def _unwrap(value: Any) -> Any:
    """Unwrap common Atomic typed-property envelopes without inventing semantics."""
    if isinstance(value, dict):
        if "$$type" in value and "value" in value:
            typed = value.get("value")
            if value.get("$$type") == "html-v3" and isinstance(typed, dict):
                content = typed.get("content")
                if isinstance(content, dict) and "value" in content:
                    return _unwrap(content)
            return _unwrap(typed)
        if "$type" in value and "value" in value:
            return _unwrap(value.get("value"))
        return {k: _unwrap(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_unwrap(v) for v in value]
    return value


def _settings(node: dict[str, Any]) -> dict[str, Any]:
    raw = node.get("settings")
    if isinstance(raw, dict):
        return _unwrap(raw)
    return {}


def _first(settings: dict[str, Any], keys: Iterable[str], suffix: str = "") -> tuple[Any, str | None]:
    for key in keys:
        candidate = f"{key}{suffix}"
        if candidate in settings and settings[candidate] not in (None, "", [], {}):
            return settings[candidate], candidate
    return None, None


def _value_repr(value: Any) -> Any:
    value = _unwrap(value)
    if isinstance(value, dict):
        unit = value.get("unit")
        if "size" in value and unit:
            return f"{value.get('size')}{unit}"
        sides = {k: value.get(k) for k in ("top", "right", "bottom", "left") if k in value}
        if sides:
            out = {k: v for k, v in sides.items()}
            if unit:
                out["unit"] = unit
            return out
        simple = {k: v for k, v in value.items() if isinstance(v, (str, int, float, bool, type(None)))}
        return simple if simple else "complex-value"
    if isinstance(value, list):
        return value[:8]
    return value


def _extract_group(settings: dict[str, Any], mapping: dict[str, Iterable[str]], suffix: str = "") -> dict[str, Any]:
    result: dict[str, Any] = {}
    for label, keys in mapping.items():
        value, source_key = _first(settings, keys, suffix)
        if source_key:
            result[label] = {"value": _value_repr(value), "provenance": "explicit", "source_key": source_key}
        else:
            result[label] = {"value": None, "provenance": "unknown"}
    return result


def _text_value(value: Any) -> str | None:
    value = _unwrap(value)
    if isinstance(value, str):
        text = re.sub(r"<[^>]+>", " ", value)
        text = re.sub(r"\s+", " ", text).strip()
        return text or None
    return None


def _node_text(node: dict[str, Any]) -> list[str]:
    settings = _settings(node)
    parts: list[str] = []
    for key, value in settings.items():
        if key in TEXT_KEYS:
            text = _text_value(value)
            if text:
                parts.append(text)
    return parts


def _content_summary(section: dict[str, Any]) -> dict[str, Any]:
    widget_types: list[str] = []
    text: list[str] = []
    media: list[dict[str, Any]] = []
    dynamic_markers: list[str] = []
    element_count = 0
    max_depth = 0

    def visit(node: Any, depth: int = 0):
        nonlocal element_count, max_depth
        if not isinstance(node, dict):
            return
        if node.get("elType") or node.get("widgetType"):
            element_count += 1
            max_depth = max(max_depth, depth)
        if node.get("widgetType"):
            widget_types.append(str(node.get("widgetType")))
        text.extend(_node_text(node))
        settings = _settings(node)
        for key, value in settings.items():
            if key in MEDIA_KEYS and value not in (None, "", [], {}):
                media.append({"key": key, "value": _value_repr(value)})
            rendered = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
            if "dynamic" in key.lower() or "dynamic" in rendered.lower() or "{{" in rendered:
                dynamic_markers.append(key)
        for child in node.get("elements", []) if isinstance(node.get("elements"), list) else []:
            visit(child, depth + 1)

    visit(section)
    return {
        "element_count": element_count,
        "max_depth": max_depth,
        "widget_types": widget_types,
        "widget_counts": dict(Counter(widget_types)),
        "text_snippets": text[:8],
        "media": media[:8],
        "dynamic_keys": sorted(set(dynamic_markers))[:12],
    }


def _role_hint(content: dict[str, Any], index: int, total: int) -> tuple[str, str, str]:
    widgets = set(content.get("widget_types", []))
    counts = content.get("widget_counts", {})
    if any("accordion" in w or "toggle" in w for w in widgets):
        return "faq", "inferred", "medium"
    if any("form" in w for w in widgets):
        return "form/contact", "inferred", "medium"
    if any("testimonial" in w for w in widgets):
        return "proof/testimonial", "inferred", "medium"
    if any("counter" in w or "progress" in w for w in widgets):
        return "stats/proof", "inferred", "medium"
    has_heading = any("heading" in w for w in widgets)
    has_button = any("button" in w for w in widgets)
    has_image = any("image" in w for w in widgets)
    if index == 0 and has_heading and (has_button or has_image):
        return "hero-like", "inferred", "low"
    if index == total - 1 and has_heading and has_button:
        return "cta-like", "inferred", "low"
    if counts and sum(counts.values()) >= 3:
        return "content-section", "inferred", "low"
    return "unspecified", "unknown", "low"


def _responsive(settings: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for viewport, suffix in RESPONSIVE_SUFFIXES.items():
        layout = _extract_group(settings, LAYOUT_KEYS, suffix)
        style = _extract_group(settings, STYLE_KEYS, suffix)
        explicit = any(v.get("provenance") == "explicit" for v in layout.values()) or any(
            v.get("provenance") == "explicit" for v in style.values()
        )
        result[viewport] = {
            "layout": layout,
            "style": style,
            "has_explicit_overrides": explicit if suffix else None,
        }
    return result


def _intent_map(intent: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(intent, dict):
        return {}
    out = {}
    for section in intent.get("sections", []) if isinstance(intent.get("sections"), list) else []:
        if isinstance(section, dict) and section.get("section_id"):
            out[str(section["section_id"])] = section
    return out


def _apply_intent(section_target: dict[str, Any], declared: dict[str, Any] | None) -> None:
    if not declared:
        return
    for field in ("section_role", "selected_pattern", "visual_anchor", "background_mode", "alignment", "density", "component_model", "cta_tier"):
        if declared.get(field) not in (None, ""):
            section_target["declared_intent"][field] = {"value": declared[field], "provenance": "declared"}
    if isinstance(declared.get("responsive_plan"), dict):
        section_target["declared_intent"]["responsive_plan"] = {"value": declared["responsive_plan"], "provenance": "declared"}
    if isinstance(declared.get("layout_contract"), dict):
        section_target["declared_intent"]["layout_contract"] = {"value": declared["layout_contract"], "provenance": "declared"}


def _unknowns(section_target: dict[str, Any]) -> list[str]:
    items = []
    desktop = section_target["responsive"]["desktop"]
    for group_name in ("layout", "style"):
        group = desktop[group_name]
        for key, item in group.items():
            if item.get("provenance") == "unknown" and key in {"direction", "justify", "align", "gap", "width", "background", "padding"}:
                items.append(f"desktop.{group_name}.{key}")
    if section_target["content"]["dynamic_keys"]:
        items.append("dynamic-content-runtime-value")
    if section_target["content"]["media"]:
        for item in section_target["content"]["media"]:
            if isinstance(item.get("value"), dict) and item["value"].get("id") and not item["value"].get("url"):
                items.append("media-id-without-rendered-url")
                break
    return sorted(set(items))


def build_visual_target(template: Any, intent: Any = None, source_name: str | None = None, source_sha256: str | None = None) -> dict[str, Any]:
    warnings: list[dict[str, str]] = []
    if not isinstance(template, dict):
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "fail",
            "evidence_class": "source_prediction",
            "render_observed": False,
            "warnings": [{"code": "invalid_root", "message": "Elementor JSON root must be an object."}],
            "sections": [],
        }
    content = template.get("content", [])
    if not isinstance(content, list):
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "fail",
            "evidence_class": "source_prediction",
            "render_observed": False,
            "warnings": [{"code": "invalid_content", "message": "Elementor JSON content must be an array."}],
            "sections": [],
        }

    ids = [str(x.get("id")) for x in content if isinstance(x, dict) and x.get("id")]
    duplicates = sorted(k for k, v in Counter(ids).items() if v > 1)
    if duplicates:
        warnings.append({"code": "duplicate_top_level_ids", "message": f"Duplicate top-level IDs: {', '.join(duplicates)}"})

    intent_by_id = _intent_map(intent)
    sections: list[dict[str, Any]] = []
    total = len(content)
    for index, section in enumerate(content):
        if not isinstance(section, dict):
            warnings.append({"code": "invalid_section", "message": f"Top-level content item {index} is not an object."})
            continue
        sid = str(section.get("id") or f"index-{index}")
        settings = _settings(section)
        csummary = _content_summary(section)
        role, role_provenance, role_confidence = _role_hint(csummary, index, total)
        target = {
            "index": index,
            "section_id": sid,
            "el_type": section.get("elType"),
            "is_inner": section.get("isInner"),
            "role_hint": {"value": role, "provenance": role_provenance, "confidence": role_confidence},
            "responsive": _responsive(settings),
            "content": csummary,
            "declared_intent": {},
            "adjacency": {
                "previous_section_id": str(content[index - 1].get("id")) if index > 0 and isinstance(content[index - 1], dict) and content[index - 1].get("id") else None,
                "next_section_id": str(content[index + 1].get("id")) if index + 1 < total and isinstance(content[index + 1], dict) and content[index + 1].get("id") else None,
            },
            "unknowns": [],
        }
        _apply_intent(target, intent_by_id.get(sid))
        target["unknowns"] = _unknowns(target)
        explicit_count = sum(
            1
            for viewport in target["responsive"].values()
            for group in (viewport["layout"], viewport["style"])
            for item in group.values()
            if item.get("provenance") == "explicit"
        )
        target["prediction_confidence"] = "high" if explicit_count >= 6 else "medium" if explicit_count >= 2 else "low"
        sections.append(target)

    whole_page = {
        "title": template.get("title"),
        "document_type": template.get("type"),
        "elementor_export_version": template.get("version"),
        "section_count": len(sections),
        "section_order": [s["section_id"] for s in sections],
        "widget_count": sum(len(s["content"]["widget_types"]) for s in sections),
        "dynamic_sections": [s["section_id"] for s in sections if s["content"]["dynamic_keys"]],
        "model_rule": "Whole-page model is assembled first; section predictions are then checked in page order and against adjacent sections.",
    }
    unresolved = sum(len(s["unknowns"]) for s in sections)
    status = "warn" if warnings or unresolved else "pass"
    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "evidence_class": "source_prediction",
        "render_observed": False,
        "claim_boundary": "This artifact predicts structure/appearance from source and declared intent; it is not screenshot, browser, staging, target or production proof.",
        "provenance_labels": ["explicit", "declared", "inferred", "unknown"],
        "source": {"name": source_name, "sha256": source_sha256},
        "whole_page": whole_page,
        "sections": sections,
        "warnings": warnings,
        "summary": {
            "sections": len(sections),
            "unresolved_fields": unresolved,
            "warnings": len(warnings),
            "prediction_complete": bool(sections) and unresolved == 0 and not warnings,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template")
    parser.add_argument("--design-intent")
    parser.add_argument("--output")
    args = parser.parse_args()
    template_path = Path(args.template)
    try:
        template = _load(args.template)
        intent = _load(args.design_intent)
        result = build_visual_target(template, intent, template_path.name, _sha256(template_path))
    except (OSError, json.JSONDecodeError) as exc:
        result = {
            "schema_version": SCHEMA_VERSION,
            "status": "fail",
            "evidence_class": "source_prediction",
            "render_observed": False,
            "warnings": [{"code": "unreadable_input", "message": str(exc)}],
            "sections": [],
        }
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 1 if result.get("status") == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
