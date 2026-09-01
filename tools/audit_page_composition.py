#!/usr/bin/env python3
"""Lint Elementor JSON against optional design-intent and project content contracts.

This tool does not choose art direction. It checks declared section intent,
client-specific content constraints, proof evidence metadata and unit usage.
"""
import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

TEXT_KEYS = {"title", "editor", "text", "description", "button_text", "ekit_funfact_title_text"}


def load(path: str | None) -> Any:
    if not path:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def walk(node: Any):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)


def visible_text(document: Any) -> str:
    parts = []
    for obj in walk(document):
        for key, value in obj.items():
            if key in TEXT_KEYS and isinstance(value, str):
                parts.append(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value)).strip())
        if isinstance(obj.get("icon_list"), list):
            for item in obj["icon_list"]:
                if isinstance(item, dict) and isinstance(item.get("text"), str):
                    parts.append(item["text"])
    return "\n".join(x for x in parts if x)


def unit_profile(document: Any) -> Counter:
    counts = Counter()
    for obj in walk(document):
        unit = obj.get("unit")
        if isinstance(unit, str) and unit:
            counts[unit.lower()] += 1
    return counts


def finding(items, severity, code, message, **extra):
    row = {"severity": severity, "code": code, "message": message}
    row.update(extra)
    items.append(row)


def audit(template: Any, intent: Any = None, content: Any = None) -> dict:
    findings = []
    text = visible_text(template)
    folded = text.casefold()
    units = unit_profile(template)

    if content:
        for phrase in content.get("must_include", []):
            if phrase.casefold() not in folded:
                finding(findings, "error", "missing_required_content", f"Required content not found: {phrase}")
        for phrase in content.get("must_not_include", []):
            if phrase.casefold() in folded:
                finding(findings, "error", "forbidden_content", f"Forbidden/outdated content found: {phrase}")
        for phrase in content.get("claim_once", []):
            count = folded.count(phrase.casefold())
            if count > 1:
                finding(findings, "warning", "repeated_dominant_claim", f"Claim appears {count} times: {phrase}", count=count)

    if intent:
        sections = intent.get("sections", []) if isinstance(intent, dict) else []
        patterns = Counter()
        previous = None
        proof_policy = (content or {}).get("proof_policy", {}) if isinstance(content, dict) else {}
        for index, section in enumerate(sections):
            if not isinstance(section, dict):
                finding(findings, "error", "invalid_intent_section", f"Section intent at index {index} is not an object")
                continue
            sid = section.get("section_id", f"index-{index}")
            pattern = section.get("selected_pattern")
            if not pattern:
                finding(findings, "error", "missing_selected_pattern", f"No selected_pattern for {sid}")
            else:
                patterns[str(pattern)] += 1
            responsive = section.get("responsive_plan")
            if not isinstance(responsive, dict) or not all(responsive.get(k) for k in ("desktop", "tablet", "mobile")):
                finding(findings, "warning", "incomplete_responsive_plan", f"Incomplete desktop/tablet/mobile plan for {sid}")
            if previous:
                same = sum(1 for key in ("selected_pattern", "background_mode", "alignment", "visual_anchor") if section.get(key) and section.get(key) == previous.get(key))
                if same >= 3 and section.get("adjacent_contrast") is not True:
                    finding(findings, "warning", "adjacent_section_monotony", f"{previous.get('section_id')} and {sid} share at least three visual dimensions")
            previous = section

            for proof in section.get("proof_items", []) or []:
                if not isinstance(proof, dict):
                    continue
                ptype, status = proof.get("type"), proof.get("status")
                if ptype == "direct_testimonial" and status != "verified":
                    mode = proof_policy.get("unverified_quotes", "warn")
                    finding(findings, "error" if mode == "block" else "warning", "unverified_testimonial", f"Direct testimonial in {sid} is {status or 'unclassified'}")
                if ptype == "customer_logo" and proof.get("permission_confirmed") is not True:
                    mode = proof_policy.get("unapproved_logos", "warn")
                    finding(findings, "error" if mode == "block" else "warning", "unapproved_customer_logo", f"Customer logo in {sid} lacks confirmed permission")

        for pattern, count in patterns.items():
            if count >= 3:
                finding(findings, "warning", "pattern_overuse", f"Pattern used {count} times: {pattern}", count=count)

    scalable = units["rem"] + units["em"] + units["%"]
    fixed = units["px"]
    total = scalable + fixed
    if total >= 20 and fixed / total > 0.8:
        finding(findings, "warning", "px_dominant_units", f"PX accounts for {fixed}/{total} common size units; verify intentional target preservation rather than habit")

    status = "fail" if any(x["severity"] == "error" for x in findings) else ("warn" if findings else "pass")
    return {"schema_version": "1.0", "status": status, "findings": findings, "unit_profile": dict(units), "text_length": len(text)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("template")
    parser.add_argument("--design-intent")
    parser.add_argument("--content-contract")
    parser.add_argument("--json-output")
    args = parser.parse_args()
    try:
        result = audit(load(args.template), load(args.design_intent), load(args.content_contract))
    except (OSError, json.JSONDecodeError) as exc:
        result = {"schema_version": "1.0", "status": "fail", "findings": [{"severity": "error", "code": "unreadable_input", "message": str(exc)}]}
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.json_output:
        Path(args.json_output).write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 1 if result["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
