import importlib.util
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "tools" / "audit_page_composition.py"
spec = importlib.util.spec_from_file_location("composition", MODULE)
composition = importlib.util.module_from_spec(spec)
spec.loader.exec_module(composition)


def widget(i, text, tag=None):
    settings = {"title": text}
    if tag:
        settings["header_size"] = tag
    return {"id": i, "elType": "widget", "widgetType": "heading", "settings": settings, "elements": []}


def template(text="Good content", unit="rem"):
    return {"content": [{"id":"a","elType":"container","settings":{"padding":{"unit":unit,"top":"2","right":"2","bottom":"2","left":"2"}},"elements":[widget("b", text)]}]}


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

    def test_required_section_and_h1_contract(self):
        t = {"content":[{"id":"hero","elType":"container","settings":{},"elements":[widget("h","Hero","h2")]}]}
        intent = {"sections":[{"section_id":"hero","section_role":"hero","selected_pattern":"split","responsive_plan":{"desktop":"split","tablet":"stack","mobile":"stack"}}]}
        result = composition.audit(t, intent, {"required_sections":["hero","services"],"required_h1_count":1})
        self.assertEqual(result["status"], "fail")
        codes={x["code"] for x in result["findings"]}
        self.assertIn("missing_required_section", codes)
        self.assertIn("semantic_h1_count", codes)

    def test_section_rule_detects_claim_in_wrong_section(self):
        t={"content":[
            {"id":"hero","elType":"container","settings":{},"elements":[widget("h1","Hero","h1")]},
            {"id":"capacity","elType":"container","settings":{},"elements":[widget("c","50-70 vehicles per day")]}
        ]}
        intent={"sections":[
            {"section_id":"hero","section_role":"hero","selected_pattern":"split","responsive_plan":{"desktop":"split","tablet":"stack","mobile":"stack"}},
            {"section_id":"capacity","section_role":"capacity","selected_pattern":"metric","responsive_plan":{"desktop":"split","tablet":"stack","mobile":"stack"}}
        ]}
        content={"section_rules":[{"section_id":"hero","required_claims":["50-70 vehicles per day"]}]}
        result=composition.audit(t,intent,content)
        self.assertEqual(result["status"],"fail")
        self.assertTrue(any(x["code"]=="required_claim_wrong_section" for x in result["findings"]))

    def test_flex_percent_width_plus_gap_warns(self):
        child=lambda i:{"id":i,"elType":"container","settings":{"width":{"unit":"%","size":25}},"elements":[widget(i+"w","x")]}
        t={"content":[{"id":"services","elType":"container","settings":{"flex_direction":"row","gap":{"unit":"rem","size":1}},"elements":[child(str(i)) for i in range(4)]}]}
        result=composition.audit(t,None,None)
        self.assertEqual(result["status"],"warn")
        self.assertTrue(any(x["code"]=="flex_width_gap_overcommit" for x in result["findings"]))

    def test_height_constraint_plus_space_between_warns(self):
        t={"content":[{"id":"card","elType":"container","settings":{"min_height":{"unit":"px","size":500},"flex_justify_content":"space-between"},"elements":[widget("w","Short")]}]}
        result=composition.audit(t,None,None)
        self.assertEqual(result["status"],"warn")
        self.assertTrue(any(x["code"]=="artificial_stretch_whitespace" for x in result["findings"]))

    def test_cta_once_warns_on_repetition(self):
        t={"content":[{"id":"a","elType":"container","settings":{},"elements":[
            {"id":"b1","elType":"widget","widgetType":"button","settings":{"button_text":"Contact us"},"elements":[]},
            {"id":"b2","elType":"widget","widgetType":"button","settings":{"button_text":"Contact us"},"elements":[]}
        ]}]}
        result=composition.audit(t,None,{"cta_once":["Contact us"]})
        self.assertEqual(result["status"],"warn")
        self.assertTrue(any(x["code"]=="repeated_primary_cta" for x in result["findings"]))


if __name__ == "__main__":
    unittest.main()
