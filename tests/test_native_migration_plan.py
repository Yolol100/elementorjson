import contextlib
import copy
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import plan_native_migration as m

def fixture():
    return {"version":"0.4","type":"page","title":"Synthetic","page_settings":[],
            "content":[{"id":"aaa0001","elType":"container","settings":{},"elements":[
                {"id":"aaa0002","elType":"widget","widgetType":"heading",
                 "settings":{"title":"Example & test","header_size":"h3"},"elements":[]},
                {"id":"aaa0003","elType":"widget","widgetType":"text-editor",
                 "settings":{"editor":"Plain paragraph"},"elements":[]}]}]}

class NativeMigration(unittest.TestCase):
    def test_content_candidate(self):
        report, markup, mapping = m.plan(fixture())
        self.assertEqual(report["status"],"CONTENT_CANDIDATE_ONLY")
        self.assertIn('<!-- wp:heading {"level":3} -->',markup)
        self.assertIn('Example &amp; test',markup)
        self.assertIn('<!-- wp:paragraph -->',markup)
        self.assertEqual(len(mapping),3)
        self.assertFalse(report["render_observed"])
        self.assertFalse(report["production_go"])
        self.assertEqual(report["editor_roundtrip"],"NOT_RUN")
        self.assertNotIn("Example",json.dumps(report))
    def test_block_on_loss(self):
        for change in (
            lambda d: d["content"][0]["settings"].update({"gap":20}),
            lambda d: d["content"][0]["elements"][0]["settings"].update({"align":"center"}),
            lambda d: d["content"][0]["elements"][1]["settings"].update({"editor":"<p>Rich</p>"}),
            lambda d: d["content"][0]["elements"][1]["settings"].update({"editor":"[shortcode]"}),
            lambda d: d["content"][0]["elements"][1]["settings"].update({"__dynamic__":{"editor":"unknown"}}),
            lambda d: d["content"][0]["elements"][1].update({"widgetType":"form"}),
            lambda d: d["content"][0].update({"styles":{}}),
            lambda d: d.update({"page_settings":{"hide_title":"yes"}}),
            lambda d: d.update({"version":"4.0"}),
            lambda d: d.update({"custom_fields":{"acf":1}}),
        ):
            d=fixture(); change(d)
            with self.subTest(d=d):
                report, markup, mapping=m.plan(d)
                self.assertEqual(report["status"],"MANUAL_MIGRATION_REQUIRED")
                self.assertIsNone(markup)
                self.assertEqual(mapping,[])
    def test_duplicate_and_shape(self):
        with self.assertRaises(m.Blocked):m.load_source(b'{"x":1,"x":2}')
        with self.assertRaises(m.Blocked):m.load_source(b'{"x":NaN}')
        d=fixture();d["content"][0]["elements"][1]["id"]="aaa0002"
        with self.assertRaises(m.Blocked):m.plan(d)
        d=fixture();d["content"][0]["elements"]=None
        with self.assertRaises(m.Blocked):m.plan(d)
    def test_heading_default(self):
        d=fixture();d["content"][0]["elements"][0]["settings"]["header_size"]="h2"
        self.assertIn("<!-- wp:heading -->",m.plan(d)[1])
    def test_output_and_ci(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/"source.json";source.write_text(json.dumps(fixture()))
            out=Path(tmp)/"candidate.json"
            with patch.dict(os.environ,{"CI":"true"}),contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(m.main([str(source)]),2)
            with patch.dict(os.environ,{},clear=True),contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(m.main([str(source),"--output",str(out)]),2)
                self.assertFalse(out.exists())
                self.assertEqual(m.main([str(source),"--output",str(out),"--confirm-private-output"]),0)
                self.assertTrue(out.exists())
                self.assertEqual(m.main([str(source),"--output",str(out),"--confirm-private-output"]),2)
