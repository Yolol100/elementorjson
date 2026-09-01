# Proof, visual polish and sidecar contracts

`elementorjson` does not choose art direction. Upstream Project Elementor + the `elementor` skill may supply two optional sidecars so this repository can lint declared design/content intent without hard-coding one client's rules.

## Files

- `contracts/design-intent.schema.json` — section roles/patterns, responsive transformation, proof metadata and unit strategy.
- `contracts/content-contract.schema.json` — `must_include`, `must_not_include`, `claim_once`, CTA/audience guidance and proof policy.
- `tools/audit_page_composition.py` — lightweight source-level lint for those contracts plus unit profiling.

```bash
python tools/audit_page_composition.py page.json \
  --design-intent page.design-intent.json \
  --content-contract page.content-contract.json \
  --json-output composition-report.json
```

## Boundaries

A green source report is not visual proof. Screenshot/browser review remains required for spacing, hierarchy, media crop, wrapping, empty space and aesthetics. Proof sidecars report provenance status; they never create testimonial text, customer permission or conversion evidence.

Relative-first unit lint is advisory because clean target exports may intentionally use PX and Elementor documents cases where fixed breakpoint gaps can be useful. Target preservation wins over mechanical unit conversion.
