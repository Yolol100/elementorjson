# V4 runtime capability inventory

The controlled runtime exports V3/Classic and V4/Atomic capability evidence as separate runtime surfaces. Do not infer Atomic settings from Classic `controls`: Elementor 4.2 Atomic elements intentionally use Atomic controls, prop schemas and style schemas instead.

The runtime inventory now records, when the exact runtime exposes them:

- `widgets` and `elements`, including `atomic` classification;
- `atomic_config` per registered Atomic widget/element: Atomic controls, props schema, states/pseudo states, dependency mapping, base settings/styles, child-type rules and element metadata;
- `experiments`, including current active state for registered Elementor/Pro feature flags;
- `atomic_style_schema` and `atomic_dynamic_tags`;
- target/runtime `global_classes`, `variables` and `components`;
- `interactions` configuration when the module is active;
- Classic document types, Dynamic Tags and controls;
- installed plugin/Elementor/Pro versions and active responsive devices/breakpoints.

These surfaces are availability evidence for the disposable controlled runtime only. A customer site's Classes, Variables, Components, Pro/add-on capabilities and site objects must come from that target's private Bridge inventory. Never copy IDs or design-system values from this public runtime into a target.

`tools/compare_runtime_capabilities.py` treats removed or changed V3/V4 capability records as review-required drift and treats additions/version changes as drift that must be re-evaluated before reuse. This includes changes to Atomic props/controls, experiments, style schema, Atomic Dynamic Tags, Classes, Variables, Components and Interactions.
