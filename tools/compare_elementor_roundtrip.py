#!/usr/bin/env python3

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


# Elementor's official Template Library importer materializes a small set of
# empty control defaults that are not semantically different from an omitted
# control. Keep this list deliberately narrow: unknown keys and every non-empty
# value remain strict roundtrip differences.
EMPTY_IMPORTER_DEFAULT_SETTING_KEYS = {
    "_background_image",
    "_background_slideshow_gallery",
    "_background_hover_image",
    "_background_hover_slideshow_gallery",
    "background_image",
    "background_slideshow_gallery",
    "background_hover_image",
    "background_hover_slideshow_gallery",
    "background_overlay_image",
    "background_overlay_slideshow_gallery",
    "background_overlay_hover_image",
    "background_overlay_hover_slideshow_gallery",
    "button_background_hover_slideshow_gallery",
    "selected_icon",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def is_empty_importer_default(value: Any) -> bool:
    if value is None or value == "":
        return True
    if isinstance(value, list):
        return not value
    if isinstance(value, dict):
        return all(is_empty_importer_default(child) for child in value.values())
    return False


def normalize_settings(value: Any) -> Any:
    # Elementor can convert an empty settings array into an object containing
    # only empty control defaults. Canonicalize the empty container to {}.
    if value == []:
        return {}
    if not isinstance(value, dict):
        return normalize(value)

    result: Dict[str, Any] = {}
    for key, child in value.items():
        if key in EMPTY_IMPORTER_DEFAULT_SETTING_KEYS and is_empty_importer_default(child):
            continue
        result[key] = normalize(child)
    return result


def normalize(value: Any) -> Any:
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if isinstance(value, dict):
        result = {}
        is_element = isinstance(value.get("elType"), str)
        for key, child in value.items():
            if is_element and key == "id":
                result[key] = "<volatile-element-id>"
            elif is_element and key == "settings":
                result[key] = normalize_settings(child)
            else:
                result[key] = normalize(child)

        # Elementor's official Template Library importer can omit an explicit
        # `isInner: false` on stored child elements. Preserve `true` strictly,
        # but normalize a missing false/default only on actual element objects.
        if is_element and "isInner" not in result:
            result["isInner"] = False
        return result
    return value


def semantic_fingerprint(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def compare(source: Dict[str, Any], imported: Dict[str, Any]) -> Dict[str, Any]:
    source_semantic = normalize({
        "content": source.get("content", []),
        "page_settings": source.get("page_settings", []),
    })
    imported_semantic = normalize({
        "content": imported.get("content", []),
        "page_settings": imported.get("page_settings", []),
    })

    differences: List[Dict[str, Any]] = []

    def walk(left: Any, right: Any, path: str) -> None:
        if len(differences) >= 25:
            return
        if type(left) is not type(right):
            differences.append({"path": path, "source": left, "imported": right, "reason": "type_mismatch"})
            return
        if isinstance(left, dict):
            left_keys = set(left.keys())
            right_keys = set(right.keys())
            for key in sorted(left_keys - right_keys):
                differences.append({"path": f"{path}.{key}", "source": left[key], "imported": None, "reason": "missing_after_import"})
                if len(differences) >= 25:
                    return
            for key in sorted(right_keys - left_keys):
                differences.append({"path": f"{path}.{key}", "source": None, "imported": right[key], "reason": "added_by_import"})
                if len(differences) >= 25:
                    return
            for key in sorted(left_keys & right_keys):
                walk(left[key], right[key], f"{path}.{key}")
                if len(differences) >= 25:
                    return
            return
        if isinstance(left, list):
            if len(left) != len(right):
                differences.append({"path": path, "source": len(left), "imported": len(right), "reason": "length_mismatch"})
                return
            for index, (left_item, right_item) in enumerate(zip(left, right)):
                walk(left_item, right_item, f"{path}[{index}]")
                if len(differences) >= 25:
                    return
            return
        if left != right:
            differences.append({"path": path, "source": left, "imported": right, "reason": "value_mismatch"})

    walk(source_semantic, imported_semantic, "$")
    return {
        "schema_version": "1.2",
        "status": "pass" if not differences else "fail",
        "normalization": (
            "Element IDs are volatile; on actual Elementor element objects only, a missing isInner is normalized to false. "
            "Only explicitly whitelisted empty Template Library control defaults are ignored; non-empty and unknown controls remain strict."
        ),
        "semantic_fingerprints": {
            "algorithm": "sha256",
            "source": semantic_fingerprint(source_semantic),
            "imported": semantic_fingerprint(imported_semantic),
        },
        "differences": differences,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare Elementor source JSON with the semantic result of an official Template Library import.")
    parser.add_argument("source", type=Path)
    parser.add_argument("imported", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        source = load_json(args.source)
        imported = load_json(args.imported)
    except (OSError, json.JSONDecodeError) as exc:
        report = {"schema_version": "1.2", "status": "fail", "differences": [{"path": "$", "reason": "read_error", "message": str(exc)}]}
    else:
        if not isinstance(source, dict) or not isinstance(imported, dict):
            report = {"schema_version": "1.2", "status": "fail", "differences": [{"path": "$", "reason": "invalid_wrapper"}]}
        else:
            report = compare(source, imported)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"roundtrip_status={report.get('status')} differences={len(report.get('differences', []))}")
    for item in report.get("differences", [])[:25]:
        print(f"DIFF {item.get('path')}: {item.get('reason')}")
    return 0 if report.get("status") == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())