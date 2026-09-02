#!/usr/bin/env python3
import argparse
import json
import sys
import zipfile
from pathlib import Path

PROFILES = ("v3", "v4", "mixed")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def nonempty_v3(snapshot):
    values = snapshot.get("v3", {})
    return {k: v for k, v in values.items() if v not in (None, "", [], {})}


def normalize_classes(snapshot):
    out = []
    classes = snapshot.get("v4", {}).get("classes", {})
    for item in classes.values():
        if not isinstance(item, dict):
            continue
        out.append({"label": item.get("label"), "type": item.get("type"), "variants": item.get("variants", [])})
    return sorted(out, key=lambda item: (str(item.get("label")), str(item.get("type"))))


def normalize_variables(snapshot):
    out = []
    variables = snapshot.get("v4", {}).get("variables", {})
    for item in variables.values():
        if not isinstance(item, dict):
            continue
        out.append({
            "label": item.get("label"),
            "type": item.get("type"),
            "value": item.get("value"),
            "order": item.get("order"),
            "sync_to_v3": bool(item.get("sync_to_v3", False)),
        })
    return sorted(out, key=lambda item: (str(item.get("label")), str(item.get("type"))))


def assert_snapshot_roundtrip(profile: str, expected: dict, actual: dict):
    expected_v3 = nonempty_v3(expected)
    actual_v3 = nonempty_v3(actual)
    for key, value in expected_v3.items():
        if actual_v3.get(key) != value:
            raise AssertionError(f"{profile}: V3 setting {key!r} changed on native import roundtrip")

    expected_classes = normalize_classes(expected)
    actual_classes = normalize_classes(actual)
    expected_variables = normalize_variables(expected)
    actual_variables = normalize_variables(actual)
    if expected_classes != actual_classes:
        raise AssertionError(f"{profile}: V4 classes changed on native import roundtrip")
    if expected_variables != actual_variables:
        raise AssertionError(f"{profile}: V4 variables changed on native import roundtrip")

    if profile == "v3" and (expected_classes or expected_variables):
        raise AssertionError("v3 fixture unexpectedly contains V4 design-system data")
    if profile == "v4" and (not expected_classes or not expected_variables):
        raise AssertionError("v4 fixture does not contain both classes and variables")
    if profile == "mixed" and (not expected_v3 or not expected_classes or not expected_variables):
        raise AssertionError("mixed fixture does not contain V3 + classes + variables")


def validate_zip(profile: str, path: Path):
    if not path.is_file() or path.stat().st_size <= 0:
        raise AssertionError(f"missing or empty native kit archive: {path}")
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        if bad:
            raise AssertionError(f"{profile}: corrupt ZIP member: {bad}")
        names = sorted(name.replace("\\", "/") for name in archive.namelist())
        for name in names:
            if name.startswith("/") or "../" in name or name == "..":
                raise AssertionError(f"{profile}: unsafe ZIP member path: {name}")
        if not any(Path(name).name == "manifest.json" for name in names):
            raise AssertionError(f"{profile}: native Elementor manifest.json is missing")
        if not any("site-settings" in name for name in names):
            raise AssertionError(f"{profile}: native site-settings payload is missing")
        has_classes = any(name.startswith("global-classes/") for name in names)
        has_variables = any(name.startswith("global-variables") for name in names)
        if profile == "v3" and (has_classes or has_variables):
            raise AssertionError("v3 native export unexpectedly contains V4 classes/variables files")
        if profile in ("v4", "mixed") and not (has_classes and has_variables):
            raise AssertionError(f"{profile}: native export is missing V4 classes or variables files")
    return names


def walk_elements(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_elements(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_elements(child)


def assert_media_value(value, label):
    if not isinstance(value, dict):
        raise AssertionError(f"{label}: media value is not an object")
    media_id = value.get("id")
    if isinstance(media_id, str) and media_id.isdigit():
        media_id = int(media_id)
    if not isinstance(media_id, int) or media_id <= 0:
        raise AssertionError(f"{label}: media id is not a positive attachment ID")
    url = value.get("url")
    if not isinstance(url, str) or not url.startswith(("http://", "https://")):
        raise AssertionError(f"{label}: media url is missing or invalid")


def validate_media_contracts(root: Path):
    observed = root / "media-observed"
    image = load_json(observed / "image-control.json")
    background = load_json(observed / "background-control.json")
    gallery = load_json(observed / "gallery-control.json")
    image_nodes = [node for node in walk_elements(image.get("content", [])) if node.get("widgetType") == "image"]
    if len(image_nodes) != 1:
        raise AssertionError("image-control: expected exactly one Image widget")
    assert_media_value(image_nodes[0].get("settings", {}).get("image"), "image-control")
    backgrounds = []
    for node in walk_elements(background.get("content", [])):
        settings = node.get("settings")
        if isinstance(settings, dict) and settings.get("background_image"):
            backgrounds.append(settings["background_image"])
    if len(backgrounds) != 1:
        raise AssertionError("background-control: expected exactly one populated background_image")
    assert_media_value(backgrounds[0], "background-control")
    gallery_nodes = [node for node in walk_elements(gallery.get("content", [])) if node.get("widgetType") == "image-gallery"]
    if len(gallery_nodes) != 1:
        raise AssertionError("gallery-control: expected exactly one Basic Gallery widget")
    items = gallery_nodes[0].get("settings", {}).get("gallery")
    if not isinstance(items, list) or len(items) != 3:
        raise AssertionError("gallery-control: expected exactly three gallery media items")
    for index, item in enumerate(items):
        assert_media_value(item, f"gallery-control[{index}]")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = {"schema_version": "1.0", "profiles": {}, "media": "pending", "status": "fail"}
    for profile in PROFILES:
        names = validate_zip(profile, args.root / f"{profile}.zip")
        expected = load_json(args.root / f"expected-{profile}.json")
        actual = load_json(args.root / f"roundtrip-{profile}.json")
        assert_snapshot_roundtrip(profile, expected, actual)
        report["profiles"][profile] = {"zip_members": names, "roundtrip": "pass"}
    validate_media_contracts(args.root)
    report["media"] = "pass"
    report["status"] = "pass"
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, OSError, ValueError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        print(f"native contract validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
