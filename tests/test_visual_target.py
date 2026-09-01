import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('vt', ROOT / 'tools' / 'build_visual_target.py')
vt = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(vt)


def classic_section(sid='s1', settings=None, elements=None, styles=None):
    return {
        'id': sid, 'elType': 'container', 'isInner': False,
        'settings': settings or {}, 'elements': elements or [], 'styles': styles or []
    }


def widget(wid, wtype, settings=None):
    return {'id': wid, 'elType': 'widget', 'widgetType': wtype, 'isInner': False, 'settings': settings or {}, 'elements': []}


class VisualTargetTests(unittest.TestCase):
    def build(self, content, intent=None, page_settings=None):
        return vt.build_visual_target({
            'title': 'T', 'type': 'page', 'version': '0.4',
            'page_settings': page_settings or [], 'content': content
        }, intent)

    def test_empty_page_warns_without_inventing_sections(self):
        r = self.build([])
        self.assertEqual(r['sections'], [])
        self.assertFalse(r['summary']['prediction_complete'])
        self.assertEqual(r['status'], 'warn')

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

    def test_custom_classic_breakpoint_is_preserved_without_guessing_target_width(self):
        r = self.build([classic_section(settings={'flex_direction':'row','flex_direction_laptop':'column'})])
        custom = r['sections'][0]['custom_responsive_controls']
        self.assertEqual(custom[0]['breakpoint_suffix'], 'laptop')
        self.assertEqual(custom[0]['value'], 'column')
        self.assertEqual(custom[0]['provenance'], 'explicit')

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

    def test_globals_are_detected_as_runtime_references(self):
        r = self.build([classic_section(elements=[widget('h','heading',{'title':'Hello','__globals__':{'title_color':'globals/colors?id=1'}})])])
        self.assertIn('__globals__', r['sections'][0]['content']['external_reference_keys'])
        self.assertIn('global-or-design-system-runtime-reference', r['sections'][0]['unknowns'])

    def test_atomic_html_v3_text_is_unwrapped(self):
        atomic = {
            'id':'a1','elType':'e-div-block','isInner':False,'settings':{},'styles':[],'elements':[{
                'id':'a2','elType':'widget','widgetType':'e-heading','isInner':False,
                'settings':{'title':{'$$type':'html-v3','value':{'content':{'$$type':'string','value':'Atomic title'},'children':[]}}},
                'elements':[]
            }]
        }
        r = self.build([atomic])
        self.assertIn('Atomic title', r['sections'][0]['content']['text_snippets'])

    def test_atomic_style_variants_preserve_typed_prop_identity(self):
        atomic = {
            'id':'a1','elType':'e-flexbox','isInner':False,'settings':{},
            'styles':[{'id':'style1','type':'local','variants':[
                {'meta':{'breakpoint':'desktop','state':'normal'},'props':{
                    'display':{'$$type':'string','value':'flex'},
                    'gap':{'$$type':'size','value':{'size':24,'unit':'px'}}
                }},
                {'meta':{'breakpoint':'mobile','state':'normal'},'props':{
                    'flex-direction':{'$$type':'string','value':'column'}
                }}
            ]}],
            'elements':[]
        }
        r = self.build([atomic])
        rules = r['sections'][0]['atomic_style_rules']
        self.assertEqual(len(rules), 2)
        self.assertEqual(rules[0]['properties']['display']['value'], 'flex')
        self.assertEqual(rules[0]['properties']['display']['typed_type'], 'string')
        self.assertEqual(rules[0]['properties']['gap']['value'], '24px')
        self.assertEqual(rules[0]['properties']['gap']['typed_type'], 'size')
        self.assertEqual(rules[1]['breakpoint'], 'mobile')
        self.assertEqual(rules[1]['properties']['flex-direction']['value'], 'column')
        self.assertNotIn('desktop.layout.gap', r['sections'][0]['unknowns'])

    def test_atomic_style_object_container_is_preserved(self):
        atomic = {
            'id':'a1','elType':'e-flexbox','isInner':False,'settings':{},
            'styles':{
                'local-style':{
                    'type':'local',
                    'variants':{
                        'mobile-normal':{
                            'meta':{'breakpoint':'mobile','state':'normal'},
                            'props':{'flex-direction':{'$$type':'string','value':'column'}}
                        }
                    }
                }
            },
            'elements':[]
        }
        r = self.build([atomic])
        rules = r['sections'][0]['atomic_style_rules']
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0]['style_id'], 'local-style')
        self.assertEqual(rules[0]['breakpoint'], 'mobile')
        self.assertEqual(rules[0]['properties']['flex-direction']['typed_type'], 'string')

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

    def test_page_settings_are_part_of_whole_page_model(self):
        r = self.build([classic_section()], page_settings={'hide_title':'yes'})
        self.assertEqual(r['whole_page']['page_settings']['hide_title'], 'yes')

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
