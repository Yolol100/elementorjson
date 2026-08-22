#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,79}$")
ALLOWED_KEYS = {
    "schema_version",
    "request_id",
    "enabled",
    "owner",
    "project_id",
    "for",
    "task",
    "why",
    "trigger_when",
    "do_not_trigger_when",
    "requested_by",
    "source_context",
}
REQUIRED_TEXT = ("for", "task", "why", "trigger_when", "do_not_trigger_when", "requested_by")


def safe_text(value: object, *, limit: int = 800) -> bool:
    return isinstance(value, str) and 0 < len(value.strip()) <= limit and "\n" not in value and "\r" not in value


def validate_request(data: object) -> dict:
    if not isinstance(data, dict):
        raise ValueError("request must be a JSON object")
    unknown = sorted(set(data) - ALLOWED_KEYS)
    if unknown:
        raise ValueError(f"unsupported request keys: {', '.join(unknown)}")
    if data.get("schema_version") != "1.0":
        raise ValueError("schema_version must be 1.0")
    if data.get("enabled") is not True:
        raise ValueError("request must be explicitly enabled")
    request_id = data.get("request_id")
    if not isinstance(request_id, str) or not SAFE_ID.fullmatch(request_id):
        raise ValueError("invalid request_id")
    if data.get("owner") != "elementor" or data.get("project_id") != "project-elementor":
        raise ValueError("request owner/project mismatch")
    for key in REQUIRED_TEXT:
        if not safe_text(data.get(key)):
            raise ValueError(f"missing or unsafe {key}")
    if data.get("requested_by") != "webactueel-workflow":
        raise ValueError("requested_by must be webactueel-workflow")
    source = data.get("source_context")
    if not isinstance(source, dict) or set(source) != {"project_id", "source_set_version"}:
        raise ValueError("source_context must contain only project_id and source_set_version")
    if source.get("project_id") != "project-elementor" or not safe_text(source.get("source_set_version"), limit=160):
        raise ValueError("invalid source_context")
    return data


def write_github_output(path: Path, data: dict) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"request_id={data['request_id']}\n")
        handle.write(f"source_set_version={data['source_context']['source_set_version'].strip()}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("request", type=Path)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()
    data = validate_request(json.loads(args.request.read_text(encoding="utf-8")))
    if args.github_output:
        write_github_output(args.github_output, data)
    print(json.dumps({
        "status": "valid",
        "request_id": data["request_id"],
        "source_set_version": data["source_context"]["source_set_version"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
