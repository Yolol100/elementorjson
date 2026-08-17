#!/usr/bin/env python3
import json
import sys
from pathlib import Path

REQUIRED = {
    "runtime-contract.json": ["schema_version"],
    "toolkit-contract.json": ["schema_version"],
}

def validate(path: Path, required_keys):
    errors = []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{path}: invalid JSON: {exc}"]
    if not isinstance(value, dict):
        return [f"{path}: root must be an object"]
    for key in required_keys:
        if key not in value:
            errors.append(f"{path}: required key missing: {key}")
    return errors

def main():
    errors=[]
    for filename, keys in REQUIRED.items():
        path=Path(filename)
        if not path.exists(): errors.append(f"{filename}: file missing")
        else: errors.extend(validate(path,keys))
    if errors:
        print("Repository contract validation failed:", file=sys.stderr)
        for error in errors: print(f"- {error}", file=sys.stderr)
        return 1
    print("Elementor repository contracts: OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
