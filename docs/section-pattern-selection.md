# Upstream section-pattern selection contract

`elementorjson` remains a controlled-runtime QA repository. It does not choose art direction itself. Project Elementor and the `elementor` skill remain the owners of section-pattern selection before JSON reaches this repository.

## Required upstream behavior

Before generating or validating a substantial new page/post/template JSON, the upstream Elementor workflow should:

1. classify every section by role, content shape, CTA/proof needs and density;
2. research relevant current reference patterns when visual form is not already fixed by an approved baseline;
3. choose a layout family per section rather than defaulting every section to the same card grid;
4. audit the full page for adjacent-section repetition, duplicate facts/CTAs and visual monotony;
5. define desktop/tablet/mobile behavior and the intended Elementor Flexbox/Grid mapping;
6. only then generate JSON for this repository's importer/runtime/browser validation.

Recommended inspiration discovery sources are SaaSFrame, Lapa Ninja and Land-book. These are reference inputs, not evidence of Elementor compatibility or conversion performance. Elementor Help remains the primary source for native Flexbox/Grid implementation behavior.

## Cohesion handoff

A page-level handoff should be able to state, at minimum, the chosen pattern for each major section and why adjacent sections form one coherent visual system. The controlled-runtime QA in this repository can validate JSON structure, dependencies, importer behavior, responsive rendering and browser failures, but it does not prove subjective design quality or automatically detect that two different sections are aesthetically too similar.

When a visual baseline exists, staging/browser comparison remains the appropriate proof route after controlled-runtime checks.

## Proof, units and machine-readable intent

For substantial pages the upstream workflow may provide `*.design-intent.json` and `*.content-contract.json` sidecars using the schemas under `contracts/`. `tools/audit_page_composition.py` can then lint declared section repetition, client-specific required/forbidden content, proof provenance status and unit usage without choosing art direction itself.

Direct testimonials are distinct from factual customer stories, third-party ratings and logo permissions. An unverified relationship must never be converted into a quote. Relative-first unit guidance is advisory: clean target units and tested breakpoint-specific PX exceptions are preserved when appropriate. See `docs/proof-polish-and-sidecars.md`.
