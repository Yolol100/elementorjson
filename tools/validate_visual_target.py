#!/usr/bin/env python3
"""Validate generated Elementor Visual Target artifacts without extra dependencies."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ALLOWED_PROVENANCE = {"explicit", "declared", "inferred", "unknown"}
EXPECTED_LABELS = ["explicit", "declared", "inferred", "unknown"]
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


def _check_annotated(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{path}: annotated value must be an object")
        return
    provenance = value.get("provenance")
    if provenance not in ALLOWED_PROVENANCE:
        errors.append(f"{path}: invalid provenance {provenance!r}")
    if "value" not in value:
        errors.append(f"{path}: annotated value is missing value")


def validate_visual_target(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["root: visual target must be an object"]
    if data.get("schema_version") != "1.0":
        errors.append("schema_version: expected 1.0")
    if data.get("status") not in {"pass", "warn", "fail"}:
        errors.append("status: expected pass/warn/fail")
    if data.get("evidence_class") != "source_prediction":
        errors.append("evidence_class: must remain source_prediction")
    if data.get("render_observed") is not False:
        errors.append("render_observed: must remain false for a source prediction")
    if data.get("provenance_labels") != EXPECTED_LABELS:
        errors.append("provenance_labels: expected explicit/declared/inferred/unknown in canonical order")

    source = data.get("source")
    if source is not None:
        if not isinstance(source, dict):
            errors.append("source: must be an object when present")
        else:
            sha = source.get("sha256")
            if sha is not None and (not isinstance(sha, str) or not SHA256_RE.fullmatch(sha)):
                errors.append("source.sha256: invalid SHA-256")

    sections = data.get("sections")
    if not isinstance(sections, list):
        errors.append("sections: must be an array")
        return errors

    seen_ids: set[str] = set()
    for index, section in enumerate(sections):
        path = f"sections[{index}]"
        if not isinstance(section, dict):
            errors.append(f"{path}: section must be an object")
            continue
        sid = section.get("section_id")
        if not isinstance(sid, str) or not sid:
            errors.append(f"{path}.section_id: non-empty string required")
        elif sid in seen_ids:
            errors.append(f"{path}.section_id: duplicate {sid!r}")
        else:
            seen_ids.add(sid)

        role = section.get("role_hint")
        _check_annotated(role, f"{path}.role_hint", errors)
        if isinstance(role, dict) and role.get("confidence") not in {"low", "medium", "high"}:
            errors.append(f"{path}.role_hint.confidence: invalid")

        responsive = section.get("responsive")
        if not isinstance(responsive, dict):
            errors.append(f"{path}.responsive: object required")
        else:
            for viewport in ("desktop", "tablet", "mobile"):
                viewport_data = responsive.get(viewport)
                vp = f"{path}.responsive.{viewport}"
                if not isinstance(viewport_data, dict):
                    errors.append(f"{vp}: object required")
                    continue
                for group_name in ("layout", "style"):
                    group = viewport_data.get(group_name)
                    if not isinstance(group, dict):
                        errors.append(f"{vp}.{group_name}: object required")
                        continue
                    for key, annotated in group.items():
                        _check_annotated(annotated, f"{vp}.{group_name}.{key}", errors)

        atomic = section.get("atomic_style_rules")
        if not isinstance(atomic, list):
            errors.append(f"{path}.atomic_style_rules: array required")
        else:
            for rule_index, rule in enumerate(atomic):
                rp = f"{path}.atomic_style_rules[{rule_index}]"
                if not isinstance(rule, dict):
                    errors.append(f"{rp}: object required")
                    continue
                props = rule.get("properties")
                if not isinstance(props, dict):
                    errors.append(f"{rp}.properties: object required")
                    continue
                for key, annotated in props.items():
                    _check_annotated(annotated, f"{rp}.properties.{key}", errors)

        declared = section.get("declared_intent")
        if not isinstance(declared, dict):
            errors.append(f"{path}.declared_intent: object required")
        else:
            for key, annotated in declared.items():
                _check_annotated(annotated, f"{path}.declared_intent.{key}", errors)
                if isinstance(annotated, dict) and annotated.get("provenance") != "declared":
                    errors.append(f"{path}.declared_intent.{key}: provenance must be declared")

        unknowns = section.get("unknowns")
        if not isinstance(unknowns, list) or not all(isinstance(item, str) for item in unknowns):
            errors.append(f"{path}.unknowns: string array required")
        if section.get("prediction_confidence") not in {"low", "medium", "high"}:
            errors.append(f"{path}.prediction_confidence: invalid")

    whole = data.get("whole_page")
    if isinstance(whole, dict):
        order = whole.get("section_order")
        if isinstance(order, list) and sections:
            actual = [section.get("section_id") for section in sections if isinstance(section, dict)]
            if order != actual:
                errors.append("whole_page.section_order: must match generated section order")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("visual_target")
    args = parser.parse_args()
    path = Path(args.visual_target)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Visual Target validation failed: {exc}")
        return 1
    errors = validate_visual_target(data)
    if errors:
        print("Visual Target validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Visual Target: valid source_prediction contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
