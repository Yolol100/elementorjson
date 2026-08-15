#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize(value: Any) -> Any:
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if isinstance(value, dict):
        result = {}
        is_element = isinstance(value.get("elType"), str)
        for key, child in value.items():
            if is_element and key == "id":
                result[key] = "<volatile-element-id>"
            else:
                result[key] = normalize(child)
        return result
    return value


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
        "schema_version": "1.0",
        "status": "pass" if not differences else "fail",
        "normalization": "only id fields on actual Elementor element objects are treated as volatile",
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
        report = {"schema_version": "1.0", "status": "fail", "differences": [{"path": "$", "reason": "read_error", "message": str(exc)}]}
    else:
        if not isinstance(source, dict) or not isinstance(imported, dict):
            report = {"schema_version": "1.0", "status": "fail", "differences": [{"path": "$", "reason": "invalid_wrapper"}]}
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
