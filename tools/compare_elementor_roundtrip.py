#!/usr/bin/env python3

import argparse
import fnmatch
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

MISSING = object()
EMPTY_NORMALIZED_KEYS = {"page_settings", "settings", "editor_settings"}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize(value: Any, parent_key: str = "") -> Any:
    if isinstance(value, dict):
        normalized: Dict[str, Any] = {}
        is_element = isinstance(value.get("elType"), str)
        for key, nested in value.items():
            if is_element and key == "id":
                normalized[key] = "__VOLATILE_ELEMENT_ID__"
                continue
            normalized_value = normalize(nested, key)
            if key in EMPTY_NORMALIZED_KEYS and normalized_value == {}:
                normalized_value = []
            normalized[key] = normalized_value
        return normalized
    if isinstance(value, list):
        return [normalize(item, parent_key) for item in value]
    return value


def path_allowed(path: str, patterns: List[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def diff_values(source: Any, roundtrip: Any, path: str, differences: List[Dict[str, Any]], allow_added: List[str]) -> None:
    if isinstance(source, dict) and isinstance(roundtrip, dict):
        source_keys = set(source)
        roundtrip_keys = set(roundtrip)
        for key in sorted(source_keys - roundtrip_keys):
            differences.append({"kind": "removed", "path": f"{path}.{key}", "source": source[key]})
        for key in sorted(roundtrip_keys - source_keys):
            added_path = f"{path}.{key}"
            if not path_allowed(added_path, allow_added):
                differences.append({"kind": "added", "path": added_path, "roundtrip": roundtrip[key]})
        for key in sorted(source_keys & roundtrip_keys):
            diff_values(source[key], roundtrip[key], f"{path}.{key}", differences, allow_added)
        return
    if isinstance(source, list) and isinstance(roundtrip, list):
        common = min(len(source), len(roundtrip))
        for index in range(common):
            diff_values(source[index], roundtrip[index], f"{path}[{index}]", differences, allow_added)
        for index in range(common, len(source)):
            differences.append({"kind": "removed", "path": f"{path}[{index}]", "source": source[index]})
        for index in range(common, len(roundtrip)):
            added_path = f"{path}[{index}]"
            if not path_allowed(added_path, allow_added):
                differences.append({"kind": "added", "path": added_path, "roundtrip": roundtrip[index]})
        return
    if source != roundtrip:
        differences.append({"kind": "changed", "path": path, "source": source, "roundtrip": roundtrip})


def compare(source_path: Path, roundtrip_path: Path, allow_added: List[str]) -> Dict[str, Any]:
    try:
        source = load_json(source_path)
        roundtrip = load_json(roundtrip_path)
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema_version": "1.0",
            "status": "fail",
            "source": str(source_path),
            "roundtrip": str(roundtrip_path),
            "differences": [{"kind": "read_error", "path": "$", "message": str(exc)}],
        }

    normalized_source = normalize(source)
    normalized_roundtrip = normalize(roundtrip)
    differences: List[Dict[str, Any]] = []
    diff_values(normalized_source, normalized_roundtrip, "$", differences, allow_added)
    counts: Dict[str, int] = {"added": 0, "removed": 0, "changed": 0}
    for item in differences:
        if item.get("kind") in counts:
            counts[item["kind"]] += 1

    return {
        "schema_version": "1.0",
        "status": "pass" if not differences else "fail",
        "source": str(source_path),
        "roundtrip": str(roundtrip_path),
        "normalization": {
            "ignored": ["Element object id values only"],
            "empty_equivalence": sorted(EMPTY_NORMALIZED_KEYS),
            "allowed_added_paths": allow_added,
        },
        "summary": {"differences": len(differences), **counts},
        "differences": differences,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare Elementor source JSON with an Elementor-import/save/re-export roundtrip.")
    parser.add_argument("source", type=Path)
    parser.add_argument("roundtrip", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--allow-added-path", action="append", default=[])
    args = parser.parse_args()

    report = compare(args.source, args.roundtrip, args.allow_added_path)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"status={report['status']}")
    if "summary" in report:
        print(f"differences={report['summary']['differences']}")
    for item in report.get("differences", [])[:50]:
        print(f"{item.get('kind', 'difference').upper()} {item.get('path', '$')}")
    return 0 if report.get("status") == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
