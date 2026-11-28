#!/usr/bin/env python3
"""Conservative, local Elementor V3 -> Gutenberg content candidate. No site writes."""
import argparse
from collections import Counter
import hashlib
import html
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 4 * 1024 * 1024
MAX_NODES = 2000
MAX_DEPTH = 30
ROOT_KEYS = {"title", "type", "version", "content", "page_settings"}
NODE_KEYS = {"id", "elType", "widgetType", "settings", "elements", "isInner"}
LAYOUT = {"section", "column", "container"}
ID = re.compile(r"[A-Fa-f0-9]{7,16}\Z")
HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}

class Blocked(Exception):
    pass

def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Blocked("DUPLICATE_JSON_KEY")
        result[key] = value
    return result

def load_source(raw):
    if len(raw) > MAX_BYTES:
        raise Blocked("SOURCE_TOO_LARGE")
    try:
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object,
                          parse_constant=lambda _: (_ for _ in ()).throw(Blocked("NONFINITE_JSON")))
    except (UnicodeError, ValueError, RecursionError):
        raise Blocked("INVALID_JSON") from None
    if not isinstance(data, dict):
        raise Blocked("EXPECTED_DOCUMENT_OBJECT")
    return data

def plain_text(value):
    # No raw HTML, dynamic tokens, shortcode or markup interpretation.
    return (isinstance(value, str) and 0 < len(value) <= 10000
            and value == value.strip()
            and all(c not in value for c in "<>[]{}\r\n\t\x00")
            and not any(ord(c) < 32 or ord(c) == 127 for c in value))

def plan(data):
    reasons = Counter()
    kinds = Counter()
    ids = set()
    mapping = []
    count = 0
    if set(data) - ROOT_KEYS or data.get("version") != "0.4" or data.get("type") != "page":
        reasons["DOCUMENT_TYPE_VERSION_OR_UNKNOWN_FIELDS"] += 1
    if data.get("page_settings", {}) not in ({}, []):
        reasons["PAGE_SETTINGS_REQUIRE_REVIEW"] += 1
    if not isinstance(data.get("content"), list) or not data["content"]:
        raise Blocked("MISSING_PAGE_CONTENT")

    def visit(node, depth):
        nonlocal count
        count += 1
        if count > MAX_NODES or depth > MAX_DEPTH:
            raise Blocked("STRUCTURE_LIMIT")
        if not isinstance(node, dict):
            raise Blocked("INVALID_ELEMENT")
        identity = node.get("id")
        if not isinstance(identity, str) or not ID.fullmatch(identity) or identity in ids:
            raise Blocked("INVALID_OR_DUPLICATE_ELEMENT_ID")
        ids.add(identity)
        kind = node.get("elType")
        if set(node) - NODE_KEYS or type(node.get("isInner", False)) is not bool:
            reasons["UNKNOWN_ELEMENT_FIELDS"] += 1
        children = node.get("elements")
        if not isinstance(children, list):
            raise Blocked("INVALID_CHILDREN")
        settings = node.get("settings")
        if not isinstance(settings, (dict, list)) or (isinstance(settings, list) and settings):
            raise Blocked("INVALID_SETTINGS")
        settings = settings or {}
        inner = [visit(child, depth + 1) for child in children]
        if isinstance(kind, str) and kind in LAYOUT:
            kinds["layout"] += 1
            if settings or "widgetType" in node or not children:
                reasons["LAYOUT_SETTINGS_REQUIRE_REVIEW"] += 1
            mapping.append({"source_id": identity, "candidate_block": "core/group"})
            return ('<!-- wp:group -->\n<div class="wp-block-group">\n'
                    + "\n".join(inner) + "\n</div>\n<!-- /wp:group -->")
        if kind != "widget" or children:
            reasons["UNSUPPORTED_STRUCTURE"] += 1
            kinds["unsupported"] += 1
            return ""
        widget = node.get("widgetType")
        if widget == "heading" and set(settings) == {"title", "header_size"}:
            heading = settings["header_size"]
            value = settings["title"]
            if isinstance(heading, str) and heading in HEADINGS and plain_text(value):
                level = int(heading[1])
                kinds["heading"] += 1
                mapping.append({"source_id": identity, "candidate_block": "core/heading",
                                "text_sha256": hashlib.sha256(value.encode()).hexdigest()})
                attrs = "" if level == 2 else " " + json.dumps({"level": level}, separators=(",", ":"))
                return ('<!-- wp:heading' + attrs + ' -->\n<' + heading +
                        ' class="wp-block-heading">' + html.escape(value, quote=False) +
                        '</' + heading + '>\n<!-- /wp:heading -->')
        if widget == "text-editor" and set(settings) == {"editor"} and plain_text(settings["editor"]):
            value = settings["editor"]
            kinds["paragraph"] += 1
            mapping.append({"source_id": identity, "candidate_block": "core/paragraph",
                            "text_sha256": hashlib.sha256(value.encode()).hexdigest()})
            return "<!-- wp:paragraph -->\n<p>" + html.escape(value, quote=False) + "</p>\n<!-- /wp:paragraph -->"
        kinds["unsupported"] += 1
        reasons["WIDGET_OR_SETTINGS_REQUIRE_REVIEW"] += 1
        return ""

    fragments = [visit(node, 1) for node in data["content"]]
    supported = not reasons
    # Do not emit partially converted pages. Group mapping is content-only,
    # not evidence that a default Elementor layout equals a core Group.
    report = {"schema_version": 1, "evidence_class": "source_prediction",
              "status": "CONTENT_CANDIDATE_ONLY" if supported else "MANUAL_MIGRATION_REQUIRED",
              "source_node_count": count, "kind_counts": dict(kinds),
              "reason_counts": dict(reasons), "render_observed": False,
              "editor_roundtrip": "NOT_RUN", "visual_equivalence": "NOT_RUN",
              "target_verified": False, "production_go": False,
              "required_next_gates": ["private_inventory_and_backup", "native_block_parse_and_editor_roundtrip",
                                     "all_urls_metadata_media_and_dynamic_dependencies", "before_after_dom_and_screenshots",
                                     "responsive_accessibility_functional_and_rollback", "independent_qa"]}
    return report, "\n\n".join(fragments) + "\n" if supported else None, mapping if supported else []

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, help="New private JSON candidate; no output on blocked source")
    parser.add_argument("--confirm-private-output", action="store_true")
    args = parser.parse_args(argv)
    try:
        if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
            raise Blocked("CLI_LOCAL_ONLY")
        with args.source.open("rb") as handle:
            raw = handle.read(MAX_BYTES+1)
        report, markup, mapping = plan(load_source(raw))
        if args.output and markup is not None:
            out = args.output.resolve()
            if (not args.confirm_private_output or out == ROOT or ROOT in out.parents
                    or not out.parent.is_dir() or out.exists()):
                raise Blocked("PRIVATE_NEW_OUTPUT_REQUIRED")
            if os.name == "posix" and out.parent.stat().st_mode & 0o077:
                raise Blocked("PRIVATE_DIRECTORY_0700_REQUIRED")
            # Windows ACL must be verified by the local owner before use.
            payload = {"report": report, "source_sha256": hashlib.sha256(raw).hexdigest(),
                       "candidate_post_content": markup, "element_mapping": mapping}
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
            with os.fdopen(os.open(out, flags, 0o600), "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
        print(json.dumps(report))
        return 0 if markup is not None else 2
    except (Blocked, OSError, UnicodeError, RecursionError):
        # No source strings, private path or raw exception in logs.
        print(json.dumps({"status":"BLOCKED","render_observed":False,"production_go":False}), file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())
