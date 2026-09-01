#!/usr/bin/env python3
"""Lint Elementor JSON against optional design-intent and project content contracts.

This tool does not choose art direction. It checks declared section intent,
client-specific content constraints, proof evidence metadata, unit usage and a
small set of generic layout-risk heuristics.
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


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value)).strip()


def visible_text(document: Any) -> str:
    parts = []
    for obj in walk(document):
        for key, value in obj.items():
            if key in TEXT_KEYS and isinstance(value, str):
                parts.append(clean_text(value))
        if isinstance(obj.get("icon_list"), list):
            for item in obj["icon_list"]:
                if isinstance(item, dict) and isinstance(item.get("text"), str):
                    parts.append(item["text"])
    return "\n".join(x for x in parts if x)


def node_visible_text(node: Any) -> str:
    return visible_text(node) if isinstance(node, (dict, list)) else ""


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


def _size_value(value: Any, expected_unit: str | None = None) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    if isinstance(value, dict):
        unit = str(value.get("unit", "")).lower()
        if expected_unit is not None and unit != expected_unit.lower():
            return None
        raw = value.get("size")
        if isinstance(raw, (int, float)):
            return float(raw)
        if isinstance(raw, str):
            try:
                return float(raw.strip())
            except ValueError:
                return None
    return None


def _percent_width(settings: dict) -> float | None:
    for key in ("width", "_element_width", "flex_basis"):
        value = settings.get(key)
        pct = _size_value(value, "%")
        if pct is not None:
            return pct
    return None


def _positive_gap(settings: dict) -> bool:
    for key in ("gap", "flex_gap", "grid_gap", "column_gap"):
        value = settings.get(key)
        if isinstance(value, dict):
            for sub in ("size", "column", "row"):
                raw = value.get(sub)
                if isinstance(raw, dict):
                    raw = raw.get("size")
                try:
                    if raw is not None and float(raw) > 0:
                        return True
                except (TypeError, ValueError):
                    pass
        else:
            try:
                if value is not None and float(value) > 0:
                    return True
            except (TypeError, ValueError):
                pass
    return False


def _has_height_constraint(settings: dict) -> bool:
    for key in ("min_height", "height", "min_height_mobile", "min_height_tablet"):
        value = settings.get(key)
        if isinstance(value, dict):
            size = _size_value(value)
            if size is not None and size > 0:
                return True
        elif isinstance(value, str) and value not in ("", "default", "auto"):
            return True
        elif isinstance(value, (int, float)) and value > 0:
            return True
    return False


def _justify_mode(settings: dict) -> str:
    for key in ("flex_justify_content", "justify_content", "content_position"):
        value = settings.get(key)
        if isinstance(value, str) and value:
            return value.lower().replace("_", "-")
    return ""


def _is_grid(settings: dict) -> bool:
    return any(str(settings.get(key, "")).lower() == "grid" for key in ("display", "container_type", "layout_type"))


def _is_row(settings: dict) -> bool:
    direction = str(settings.get("flex_direction", settings.get("direction", "row"))).lower()
    return direction not in {"column", "column-reverse"}


def _layout_findings(template: Any, findings: list[dict]) -> None:
    for obj in walk(template):
        if not isinstance(obj, dict):
            continue
        settings = obj.get("settings") if isinstance(obj.get("settings"), dict) else {}
        children = obj.get("elements") if isinstance(obj.get("elements"), list) else []
        if len(children) >= 2 and _is_row(settings) and not _is_grid(settings) and _positive_gap(settings):
            widths = []
            all_explicit = True
            for child in children:
                csettings = child.get("settings") if isinstance(child, dict) and isinstance(child.get("settings"), dict) else {}
                pct = _percent_width(csettings)
                if pct is None:
                    all_explicit = False
                    break
                widths.append(pct)
            if all_explicit and widths and sum(widths) >= 99.9:
                finding(
                    findings,
                    "warning",
                    "flex_width_gap_overcommit",
                    f"Row declares {sum(widths):g}% child width plus a non-zero gap; verify Grid/Flex Grow/calc math instead of relying on shrink or wrapping.",
                    element_id=obj.get("id"),
                    width_total=sum(widths),
                )

        if _has_height_constraint(settings) and _justify_mode(settings) in {"center", "space-between", "space-around", "space-evenly"}:
            substantive = [child for child in children if node_visible_text(child).strip()]
            if len(substantive) <= 3:
                finding(
                    findings,
                    "warning",
                    "artificial_stretch_whitespace",
                    "Height-constrained sparse container uses centered/distributed vertical justification; inspect stretch/min-height before adding filler content.",
                    element_id=obj.get("id"),
                    justify=_justify_mode(settings),
                )


def _h1_count(template: Any) -> int:
    count = 0
    for obj in walk(template):
        if not isinstance(obj, dict) or obj.get("elType") != "widget":
            continue
        settings = obj.get("settings") if isinstance(obj.get("settings"), dict) else {}
        if str(settings.get("header_size", settings.get("html_tag", ""))).lower() == "h1":
            count += 1
    return count


def _top_level_map(template: Any) -> dict[str, dict]:
    content = template.get("content", []) if isinstance(template, dict) else []
    return {str(x.get("id")): x for x in content if isinstance(x, dict) and x.get("id")}


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
        for label in content.get("cta_once", []):
            count = folded.count(label.casefold())
            if count > 1:
                finding(findings, "warning", "repeated_primary_cta", f"CTA label appears {count} times despite cta_once: {label}", count=count)
        if "required_h1_count" in content:
            expected = int(content["required_h1_count"])
            actual = _h1_count(template)
            if actual != expected:
                finding(findings, "error", "semantic_h1_count", f"Expected {expected} H1 widget(s), found {actual}.", expected=expected, actual=actual)

    intent_sections = intent.get("sections", []) if isinstance(intent, dict) else []
    intent_by_id = {str(s.get("section_id")): s for s in intent_sections if isinstance(s, dict) and s.get("section_id")}
    roles = {str(s.get("section_role")) for s in intent_sections if isinstance(s, dict) and s.get("section_role")}

    if content:
        for required in content.get("required_sections", []):
            if str(required) not in roles and str(required) not in intent_by_id:
                finding(findings, "error", "missing_required_section", f"Required section not declared in design intent: {required}")

        top = _top_level_map(template)
        for index, rule in enumerate(content.get("section_rules", []) or []):
            if not isinstance(rule, dict):
                finding(findings, "error", "invalid_section_rule", f"Section rule at index {index} is not an object")
                continue
            candidate_ids = []
            if rule.get("section_id"):
                candidate_ids.append(str(rule["section_id"]))
            elif rule.get("section_role"):
                candidate_ids.extend(str(s.get("section_id")) for s in intent_sections if isinstance(s, dict) and s.get("section_role") == rule.get("section_role") and s.get("section_id"))
            if len(candidate_ids) != 1 or candidate_ids[0] not in top:
                finding(findings, "warning", "section_rule_unbound", f"Section rule could not bind uniquely to a top-level Elementor section: {rule.get('section_id') or rule.get('section_role') or index}")
                continue
            sid = candidate_ids[0]
            section_folded = node_visible_text(top[sid]).casefold()
            for phrase in rule.get("required_claims", []) or []:
                if phrase.casefold() not in section_folded:
                    code = "required_claim_wrong_section" if phrase.casefold() in folded else "missing_section_required_claim"
                    finding(findings, "error", code, f"Required claim for section {sid} is not present in that section: {phrase}", section_id=sid)
            for phrase in rule.get("forbidden_content", []) or []:
                if phrase.casefold() in section_folded:
                    finding(findings, "error", "forbidden_section_content", f"Forbidden content found in section {sid}: {phrase}", section_id=sid)
            for label in rule.get("required_ctas", []) or []:
                if label.casefold() not in section_folded:
                    finding(findings, "error", "missing_section_cta", f"Required CTA not found in section {sid}: {label}", section_id=sid)

    if intent:
        sections = intent_sections
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
            contract = section.get("layout_contract")
            if isinstance(contract, dict):
                counts = [contract.get(k) for k in ("desktop_columns", "tablet_columns", "mobile_columns")]
                if any(v is not None and (not isinstance(v, int) or v < 1) for v in counts):
                    finding(findings, "error", "invalid_layout_contract", f"Invalid column count in layout_contract for {sid}")
            if previous:
                keys = ("selected_pattern", "background_mode", "alignment", "visual_anchor", "density", "component_model")
                same = sum(1 for key in keys if section.get(key) and section.get(key) == previous.get(key))
                if same >= 4 and section.get("adjacent_contrast") is not True:
                    finding(findings, "warning", "adjacent_section_monotony", f"{previous.get('section_id')} and {sid} share at least four visual dimensions")
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

    _layout_findings(template, findings)

    scalable = units["rem"] + units["em"] + units["%"]
    fixed = units["px"]
    total = scalable + fixed
    if total >= 20 and fixed / total > 0.8:
        finding(findings, "warning", "px_dominant_units", f"PX accounts for {fixed}/{total} common size units; verify intentional target preservation rather than habit")

    status = "fail" if any(x["severity"] == "error" for x in findings) else ("warn" if findings else "pass")
    return {"schema_version": "1.1", "status": status, "findings": findings, "unit_profile": dict(units), "text_length": len(text)}


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
        result = {"schema_version": "1.1", "status": "fail", "findings": [{"severity": "error", "code": "unreadable_input", "message": str(exc)}]}
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.json_output:
        Path(args.json_output).write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 1 if result["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
