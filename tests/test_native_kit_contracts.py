import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "validate_native_kit_contracts.py"
spec = importlib.util.spec_from_file_location("native_contracts", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class NativeKitContractTests(unittest.TestCase):
    def fixture_snapshot(self, profile):
        v3 = {"container_width": {"unit": "px", "size": 1180, "sizes": []}} if profile in ("v3", "mixed") else {}
        classes = {"g-test": {"id": "g-test", "type": "class", "label": "Test", "variants": []}} if profile in ("v4", "mixed") else {}
        variables = {}
        if profile in ("v4", "mixed"):
            variables = {
                "e-gv-color": {"type": "global-color-variable", "label": "color", "value": "#123456", "order": 1, "sync_to_v3": False},
                "e-gv-font": {"type": "global-font-variable", "label": "font", "value": "Arial", "order": 2, "sync_to_v3": False},
                "e-gv-size": {"type": "global-size-variable", "label": "size", "value": "1.5rem", "order": 3, "sync_to_v3": False},
            }
        return {"v3": v3, "v4": {"classes": classes, "variables": variables}}

    def write_zip(self, path, profile):
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("manifest.json", "{}")
            archive.writestr("site-settings.json", "{}")
            if profile in ("v4", "mixed"):
                archive.writestr("global-classes/g-test.json", "{}")
                archive.writestr("global-classes/order.json", "[]")
                archive.writestr("global-variables.json", "{}")

    def media_document(self, kind):
        media = {"id": 7, "url": "https://example.test/a.png"}
        if kind == "image":
            content = [{"widgetType": "image", "settings": {"image": media}, "elements": []}]
        elif kind == "background":
            content = [{"elType": "container", "settings": {"background_image": media}, "elements": []}]
        else:
            content = [{"widgetType": "image-gallery", "settings": {"wp_gallery": [media, media, media], "thumbnail_size": "full"}, "elements": []}]
        return {"content": content}

    def test_profiles_and_media_contracts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for profile in module.PROFILES:
                self.write_zip(root / f"{profile}.zip", profile)
                snapshot = self.fixture_snapshot(profile)
                (root / f"expected-{profile}.json").write_text(json.dumps(snapshot), encoding="utf-8")
                (root / f"roundtrip-{profile}.json").write_text(json.dumps(snapshot), encoding="utf-8")
                module.validate_zip(profile, root / f"{profile}.zip")
                module.assert_snapshot_roundtrip(profile, snapshot, snapshot)

            observed = root / "media-observed"
            observed.mkdir()
            (observed / "image-control.json").write_text(json.dumps(self.media_document("image")), encoding="utf-8")
            (observed / "background-control.json").write_text(json.dumps(self.media_document("background")), encoding="utf-8")
            (observed / "gallery-control.json").write_text(json.dumps(self.media_document("gallery")), encoding="utf-8")
            module.validate_media_contracts(root)

    def test_v3_rejects_v4_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "v3.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("manifest.json", "{}")
                archive.writestr("site-settings.json", "{}")
                archive.writestr("global-variables.json", "{}")
            with self.assertRaises(AssertionError):
                module.validate_zip("v3", path)


if __name__ == "__main__":
    unittest.main()
