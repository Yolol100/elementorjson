# Proof, visual polish and sidecar contracts

`elementorjson` does not choose art direction. Upstream Project Elementor + the `elementor` skill may supply two optional sidecars so this repository can lint declared design/content intent without hard-coding one client's rules.

## Files

- `contracts/design-intent.schema.json` — section roles/patterns, responsive transformation, proof metadata, baseline/version intent, density/component model, layout contract and unit strategy.
- `contracts/content-contract.schema.json` — global constraints plus optional `required_sections`, section-level required/forbidden content, CTA rules, H1 count and proof policy.
- `tools/audit_page_composition.py` — source-level lint for those contracts plus unit profiling and generic layout-risk heuristics.

```bash
python tools/audit_page_composition.py page.json \
  --design-intent page.design-intent.json \
  --content-contract page.content-contract.json \
  --json-output composition-report.json
```

## Briefing and baseline fields

A design-intent sidecar may declare `baseline_ref`/`baseline_version` and, per section, `density`, `component_model`, `cta_tier`, `equal_height_strategy` and a `layout_contract`. A content contract may declare `required_sections`, `required_h1_count`, `cta_once` and `section_rules`.

Section rules remain project data. They can say a hero requires a specific claim or CTA, but this repository must never hard-code one client's wording into generic logic.

When a section rule supplies a `section_id`, the composition linter can bind it to a top-level Elementor element with the same ID and check required/forbidden text in that region. A role-only rule is bound only when the design intent resolves it to exactly one section. Ambiguous/unbound rules warn rather than pretending section placement was proven.

## Generic layout warnings

The linter also reports generic source risks that repeatedly cause broken marketing pages:

- `flex_width_gap_overcommit` — explicit percentage child widths already consume ~100% while the parent also declares a non-zero gap;
- `artificial_stretch_whitespace` — a height-constrained sparse container uses centered/distributed justification and should be inspected before filler content is added;
- `semantic_h1_count` — optional contract-driven H1 count mismatch;
- `repeated_primary_cta` — a label marked in `cta_once` appears repeatedly;
- `required_claim_wrong_section` / `missing_section_cta` — a bound section violates its project-specific section rule.

These are source-level signals, not visual verdicts. A complex target can intentionally need a different structure; repair only confirmed defects and preserve proven target behavior.

## Boundaries

A green source report is not visual proof. Screenshot/browser review remains required for spacing, hierarchy, media crop, wrapping, empty space and aesthetics. Proof sidecars report provenance status; they never create testimonial text, customer permission or conversion evidence.

Relative-first unit lint is advisory because clean target exports may intentionally use PX and Elementor documents cases where fixed breakpoint gaps can be useful. Target preservation wins over mechanical unit conversion.
