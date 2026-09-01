import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('vt', ROOT / 'tools' / 'build_visual_target.py')
vt = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(vt)


def classic_section(sid='s1', settings=None, elements=None):
    return {'id': sid, 'elType': 'container', 'isInner': False, 'settings': settings or {}, 'elements': elements or []}


def widget(wid, wtype, settings=None):
    return {'id': wid, 'elType': 'widget', 'widgetType': wtype, 'isInner': False, 'settings': settings or {}, 'elements': []}


class VisualTargetTests(unittest.TestCase):
    def build(self, content, intent=None):
        return vt.build_visual_target({'title': 'T', 'type': 'page', 'version': '0.4', 'content': content}, intent)

    def test_empty_page_warns_without_inventing_sections(self):
        r = self.build([])
        self.assertEqual(r['sections'], [])
        self.assertFalse(r['summary']['prediction_complete'])

    def test_basic_heading_button_is_hero_like_only_as_inference(self):
        r = self.build([classic_section(elements=[widget('h','heading',{'title':'Hello'}), widget('b','button',{'text':'Go'})])])
        role = r['sections'][0]['role_hint']
        self.assertEqual(role['value'], 'hero-like')
        self.assertEqual(role['provenance'], 'inferred')
        self.assertFalse(r['render_observed'])

    def test_explicit_flex_layout_is_preserved(self):
        s = classic_section(settings={
            'flex_direction': 'row', 'flex_justify_content': 'space-between',
            'flex_align_items': 'center', 'gap': {'unit':'px','size':24},
            'padding': {'unit':'px','top':40,'right':20,'bottom':40,'left':20},
        })
        r = self.build([s])
        d = r['sections'][0]['responsive']['desktop']
        self.assertEqual(d['layout']['direction']['value'], 'row')
        self.assertEqual(d['layout']['gap']['value'], '24px')
        self.assertEqual(d['style']['padding']['value']['top'], 40)
        self.assertEqual(d['layout']['direction']['provenance'], 'explicit')

    def test_responsive_overrides_are_separate(self):
        s = classic_section(settings={'flex_direction':'row','flex_direction_tablet':'column','flex_direction_mobile':'column-reverse'})
        r = self.build([s])
        resp = r['sections'][0]['responsive']
        self.assertEqual(resp['desktop']['layout']['direction']['value'], 'row')
        self.assertEqual(resp['tablet']['layout']['direction']['value'], 'column')
        self.assertEqual(resp['mobile']['layout']['direction']['value'], 'column-reverse')
        self.assertTrue(resp['mobile']['has_explicit_overrides'])

    def test_grid_is_explicit(self):
        r = self.build([classic_section(settings={'display':'grid','grid_columns':3,'gap':{'unit':'rem','size':2}})])
        d = r['sections'][0]['responsive']['desktop']['layout']
        self.assertEqual(d['display']['value'], 'grid')
        self.assertEqual(d['grid_columns']['value'], 3)
        self.assertEqual(d['gap']['value'], '2rem')

    def test_nested_structure_depth_and_widgets(self):
        inner = classic_section('inner', elements=[widget('i','image',{'image': {'id': 9}})])
        outer = classic_section('outer', elements=[inner, widget('h','heading',{'title':'X'})])
        r = self.build([outer])
        c = r['sections'][0]['content']
        self.assertGreaterEqual(c['max_depth'], 2)
        self.assertIn('image', c['widget_types'])
        self.assertIn('media-id-without-rendered-url', r['sections'][0]['unknowns'])

    def test_dynamic_data_is_not_resolved(self):
        r = self.build([classic_section(elements=[widget('h','heading',{'title':'{{post_title}}','dynamic_tags':{'title':'x'}})])])
        self.assertIn('dynamic-content-runtime-value', r['sections'][0]['unknowns'])

    def test_atomic_html_v3_text_is_unwrapped(self):
        atomic = {
            'id':'a1','elType':'e-div-block','isInner':False,'settings':{},'elements':[{
                'id':'a2','elType':'widget','widgetType':'e-heading','isInner':False,
                'settings':{'title':{'$$type':'html-v3','value':{'content':{'$$type':'string','value':'Atomic title'},'children':[]}}},
                'elements':[]
            }]
        }
        r = self.build([atomic])
        self.assertIn('Atomic title', r['sections'][0]['content']['text_snippets'])

    def test_design_intent_is_declared_not_explicit(self):
        intent = {'schema_version':'1.0','sections':[{'section_id':'s1','section_role':'hero','selected_pattern':'split','alignment':'left','responsive_plan':{'desktop':'split','tablet':'split','mobile':'stack'}}]}
        r = self.build([classic_section('s1')], intent)
        d = r['sections'][0]['declared_intent']
        self.assertEqual(d['section_role'], {'value':'hero','provenance':'declared'})
        self.assertEqual(d['selected_pattern']['value'], 'split')

    def test_adjacency_is_whole_page_aware(self):
        r = self.build([classic_section('a'), classic_section('b'), classic_section('c')])
        self.assertEqual(r['sections'][1]['adjacency']['previous_section_id'], 'a')
        self.assertEqual(r['sections'][1]['adjacency']['next_section_id'], 'c')
        self.assertEqual(r['whole_page']['section_order'], ['a','b','c'])

    def test_duplicate_top_ids_warn(self):
        r = self.build([classic_section('dup'), classic_section('dup')])
        self.assertTrue(any(x['code']=='duplicate_top_level_ids' for x in r['warnings']))
        self.assertEqual(r['status'], 'warn')

    def test_invalid_content_fails_closed(self):
        r = vt.build_visual_target({'content': {}})
        self.assertEqual(r['status'], 'fail')
        self.assertEqual(r['sections'], [])

    def test_invalid_root_fails_closed(self):
        r = vt.build_visual_target([])
        self.assertEqual(r['status'], 'fail')

    def test_last_heading_button_can_be_cta_like(self):
        r = self.build([classic_section('x'), classic_section('last', elements=[widget('h','heading',{'title':'Ready'}), widget('b','button',{'text':'Start'})])])
        self.assertEqual(r['sections'][-1]['role_hint']['value'], 'cta-like')

    def test_confidence_rises_with_explicit_geometry(self):
        settings = {'flex_direction':'row','flex_justify_content':'center','flex_align_items':'center','gap':10,'width':100,'padding':20,'background_color':'#fff'}
        r = self.build([classic_section(settings=settings)])
        self.assertEqual(r['sections'][0]['prediction_confidence'], 'high')

    def test_source_prediction_never_becomes_render_proof(self):
        r = self.build([classic_section()])
        self.assertEqual(r['evidence_class'], 'source_prediction')
        self.assertFalse(r['render_observed'])
        self.assertIn('not screenshot', r['claim_boundary'].lower())


if __name__ == '__main__':
    unittest.main()
