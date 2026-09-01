import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BUILDER_SPEC = importlib.util.spec_from_file_location('visual_builder', ROOT / 'tools' / 'build_visual_target.py')
builder = importlib.util.module_from_spec(BUILDER_SPEC)
BUILDER_SPEC.loader.exec_module(builder)

VALIDATOR_SPEC = importlib.util.spec_from_file_location('visual_validator', ROOT / 'tools' / 'validate_visual_target.py')
validator = importlib.util.module_from_spec(VALIDATOR_SPEC)
VALIDATOR_SPEC.loader.exec_module(validator)


def sample_target():
    template = {
        'title': 'Sample', 'type': 'page', 'version': '0.4',
        'content': [{
            'id': 's1', 'elType': 'container', 'isInner': False,
            'settings': {'flex_direction': 'row', 'gap': {'unit': 'px', 'size': 24}},
            'elements': []
        }]
    }
    return builder.build_visual_target(template)


class VisualTargetContractTests(unittest.TestCase):
    def test_builder_output_passes_contract_validator(self):
        self.assertEqual(validator.validate_visual_target(sample_target()), [])

    def test_rejects_promotion_to_render_observation(self):
        target = sample_target()
        target['render_observed'] = True
        errors = validator.validate_visual_target(target)
        self.assertTrue(any('render_observed' in item for item in errors), errors)

    def test_rejects_evidence_class_upgrade(self):
        target = sample_target()
        target['evidence_class'] = 'browser_at'
        errors = validator.validate_visual_target(target)
        self.assertTrue(any('evidence_class' in item for item in errors), errors)

    def test_rejects_unknown_provenance_label(self):
        target = sample_target()
        mutated = copy.deepcopy(target)
        mutated['sections'][0]['responsive']['desktop']['layout']['direction']['provenance'] = 'observed'
        errors = validator.validate_visual_target(mutated)
        self.assertTrue(any('invalid provenance' in item for item in errors), errors)

    def test_rejects_declared_intent_that_loses_declared_provenance(self):
        target = builder.build_visual_target(
            {'content': [{'id': 's1', 'elType': 'container', 'isInner': False, 'settings': {}, 'elements': []}]},
            {'schema_version': '1.0', 'sections': [{'section_id': 's1', 'section_role': 'hero', 'selected_pattern': 'split'}]},
        )
        target['sections'][0]['declared_intent']['section_role']['provenance'] = 'explicit'
        errors = validator.validate_visual_target(target)
        self.assertTrue(any('provenance must be declared' in item for item in errors), errors)

    def test_rejects_section_order_drift(self):
        target = sample_target()
        target['whole_page']['section_order'] = ['other']
        errors = validator.validate_visual_target(target)
        self.assertTrue(any('section_order' in item for item in errors), errors)


if __name__ == '__main__':
    unittest.main()
