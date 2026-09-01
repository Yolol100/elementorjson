import importlib.util
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "tools" / "audit_page_composition.py"
spec = importlib.util.spec_from_file_location("composition", MODULE)
composition = importlib.util.module_from_spec(spec)
spec.loader.exec_module(composition)


def template(text="Good content", unit="rem"):
    return {"content": [{"id":"a","elType":"container","settings":{"padding":{"unit":unit,"top":"2","right":"2","bottom":"2","left":"2"}},"elements":[{"id":"b","elType":"widget","widgetType":"heading","settings":{"title":text},"elements":[]}]}]}


class PageCompositionTests(unittest.TestCase):
    def test_content_contract_blocks_forbidden_word(self):
        result = composition.audit(template("Old carwash copy"), None, {"must_not_include":["carwash"]})
        self.assertEqual(result["status"], "fail")
        self.assertTrue(any(x["code"] == "forbidden_content" for x in result["findings"]))

    def test_unverified_quote_can_block(self):
        intent = {"sections":[{"section_id":"proof","section_role":"proof","selected_pattern":"quote","responsive_plan":{"desktop":"split","tablet":"stack","mobile":"stack"},"proof_items":[{"type":"direct_testimonial","status":"placeholder"}]}]}
        content = {"proof_policy":{"unverified_quotes":"block"}}
        result = composition.audit(template(), intent, content)
        self.assertEqual(result["status"], "fail")
        self.assertTrue(any(x["code"] == "unverified_testimonial" for x in result["findings"]))

    def test_repeated_pattern_warns_not_fails(self):
        sections=[]
        for i in range(3):
            sections.append({"section_id":str(i),"section_role":"benefits","selected_pattern":"2x2-grid","background_mode":"light","alignment":"center","visual_anchor":"icon","responsive_plan":{"desktop":"grid","tablet":"grid","mobile":"stack"}})
        result = composition.audit(template(), {"sections":sections}, None)
        self.assertEqual(result["status"], "warn")
        self.assertTrue(any(x["code"] == "pattern_overuse" for x in result["findings"]))


if __name__ == "__main__":
    unittest.main()
