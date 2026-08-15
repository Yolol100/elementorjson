#!/usr/bin/env python3

import argparse
import difflib
import json
import sys
from pathlib import Path
from typing import Any

IGNORED_ELEMENT_FIELDS = {"id"}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def is_element_object(value: dict[str, Any]) -> bool:
    return isinstance(value.get("elType"), str) and bool(value.get("elType"))


def normalize(value: Any) -> Any:
    if isinstance(value, dict):
        element_object = is_element_object(value)
        return {
            key: normalize(child)
            for key, child in sorted(value.items())
            if not (element_object and key in IGNORED_ELEMENT_FIELDS)
        }
    if isinstance(value, list):
        return [normalize(child) for child in value]
    return value


def canonical_payload(document: Any) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise ValueError("Roundtrip documents must be JSON objects.")
    content = document.get("content")
    if not isinstance(content, list):
        raise ValueError("Roundtrip documents must contain a content array.")
    page_settings = document.get("page_settings", [])
    if not isinstance(page_settings, (list, dict)):
        raise ValueError("page_settings must be an array or object.")
    return {
        "content": normalize(content),
        "page_settings": normalize(page_settings),
    }


def compare(source: Path, reexport: Path) -> dict[str, Any]:
    try:
        source_doc = load(source)
        reexport_doc = load(reexport)
        expected = canonical_payload(source_doc)
        actual = canonical_payload(reexport_doc)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return {
            "schema_version": "1.1",
            "status": "fail",
            "source": str(source),
            "reexport": str(reexport),
            "errors": [str(exc)],
        }

    ignored_fields = ["element.id"]
    if expected == actual:
        return {
            "schema_version": "1.1",
            "status": "pass",
            "source": str(source),
            "reexport": str(reexport),
            "ignored_fields": ignored_fields,
            "semantic_equal": True,
            "diff": [],
        }

    expected_text = json.dumps(expected, indent=2, ensure_ascii=False, sort_keys=True).splitlines()
    actual_text = json.dumps(actual, indent=2, ensure_ascii=False, sort_keys=True).splitlines()
    diff = list(
        difflib.unified_diff(
            expected_text,
            actual_text,
            fromfile="source",
            tofile="imported-reexport",
            lineterm="",
        )
    )
    return {
        "schema_version": "1.1",
        "status": "fail",
        "source": str(source),
        "reexport": str(reexport),
        "ignored_fields": ignored_fields,
        "semantic_equal": False,
        "diff": diff[:300],
        "diff_truncated": len(diff) > 300,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare Elementor source JSON with a post-import semantic re-export.")
    parser.add_argument("source", type=Path)
    parser.add_argument("reexport", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = compare(args.source, args.reexport)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"status={report.get('status')}")
    print(f"semantic_equal={report.get('semantic_equal', False)}")
    for line in report.get("diff", [])[:40]:
        print(line)
    for error in report.get("errors", []):
        print(f"ERROR {error}")
    return 0 if report.get("status") == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
