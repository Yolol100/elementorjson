# Proof, visual polish and sidecar contracts

`elementorjson` does not choose art direction. Project Elementor + the `elementor` Skill may supply optional sidecars so this repository can lint declared intent without hard-coding client rules. The repository can also derive a deterministic whole-page Visual Target from the Elementor source.

## Files

- `contracts/design-intent.schema.json` — optional section roles/patterns, responsive transformation, proof metadata, baseline/version intent, density/component model, layout contract and unit strategy.
- `contracts/content-contract.schema.json` — optional global/section content constraints and proof policy.
- `contracts/visual-target.schema.json` — generated whole-page prediction contract and evidence boundary.
- `tools/audit_page_composition.py` — source-level composition/layout-risk lint.
- `tools/build_visual_target.py` — deterministic JSON → whole-page Visual Target builder.
- `.github/workflows/composition-contract.yml` — source-level CI for composition, contracts and Visual Targets.

## Visual Target contract

For each `templates/<stem>.json`, CI creates `artifacts/visual-targets/<stem>.json`. When `sidecars/<stem>.design-intent.json` exists, declared design intent is attached without converting it into observed fact.

The builder must preserve provenance:

- `explicit`: directly encoded in Elementor JSON;
- `declared`: supplied by a design-intent contract;
- `inferred`: bounded structural interpretation;
- `unknown`: unresolved by source evidence.

It assembles the whole page first: document role/type, section count/order, adjacency, widgets, dynamic markers and per-section desktop/tablet/mobile layout/style fields. It may infer only broad low/medium-confidence role hints such as hero-like or CTA-like. It must never invent exact spacing, geometry, typography, media output or runtime values that are absent from source.

`evidence_class=source_prediction` and `render_observed=false` are immutable boundaries. A green Visual Target means the prediction contract was built consistently; it does not mean the prediction matches a real browser.

## Sidecar convention

Runtime templates stay in `templates/`. Optional authored project contracts stay in `sidecars/`:

- `sidecars/<stem>.design-intent.json`
- `sidecars/<stem>.content-contract.json`

Generated Visual Targets belong only in workflow artifacts, not as hand-maintained source truth on the default branch.

## Closed-loop visual polish

After an actual controlled-runtime, staging or target render is available, compare the Visual Target with both screenshot and machine-readable DOM layout data. Use screenshot evidence for visual hierarchy/crop/rhythm and `layout_snapshot` for observable geometry such as bounding boxes, parent width ratio, flex/grid direction, wrap, gaps, padding, margins, overflow, text alignment and computed sizes.

A mismatch must be classified before repair. Change only the smallest confirmed cause, rerun the affected checks and rebuild the whole-page Visual Target after a material JSON change. Previously passed sections remain frozen unless the new change can affect them.

## Generic source warnings

The composition linter continues to report source risks such as:

- `flex_width_gap_overcommit`;
- `artificial_stretch_whitespace`;
- `semantic_h1_count`;
- `repeated_primary_cta`;
- `required_claim_wrong_section` / `missing_section_cta`.

These are source-level signals, not visual verdicts. Target preservation wins over mechanical cleanup when a real target proves intentional behavior.

## Boundaries

A Visual Target is not a screenshot. A DOM layout snapshot is not an aesthetic verdict. A controlled-runtime render is not customer staging. Screenshot/browser review remains required for claims about visible alignment, hierarchy, media crop, wrapping, empty space or aesthetics; Website QA remains required for target/release acceptance where applicable.
