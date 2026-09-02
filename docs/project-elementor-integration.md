# Project Elementor integration

This repository is the Project Elementor controlled-runtime capability for source validation, whole-page visual-target prediction, official Elementor Template Library import, semantic importer roundtrip, runtime widget/dependency inspection, disposable rendering, cross-browser responsive evidence and exact-runtime native Website Template/Design System package evidence.

## Ownership

The Elementor Skill remains domain owner. `webactueel-workflow` controls multi-owner/source-write/formal scan-fix-retest work. Website QA owns staging/live/browser acceptance beyond this disposable runtime. This repository never becomes the design owner.

## Whole-page Visual Target

For safe/sanitized Elementor JSON, run `tools/build_visual_target.py` before section-level repair. The builder reads the entire document, records section order and adjacency, extracts explicit source layout/style data, attaches safe declared design-intent when supplied, applies only low/medium-confidence structural role hints, and leaves unresolved properties unknown.

Every prediction uses one of four provenance labels:

- `explicit` — directly present in the Elementor JSON;
- `declared` — supplied by the matching design-intent contract;
- `inferred` — a bounded structural interpretation such as hero-like/CTA-like;
- `unknown` — not established by source evidence.

The artifact is always `evidence_class=source_prediction` and `render_observed=false`. It is not browser proof and may not be promoted to pixel-perfect or target claims.

## Controlled-runtime chain

The core workflows must:

1. validate repository/runtime/tool contracts;
2. build and schema-check whole-page Visual Targets for committed sanitized templates;
3. validate Classic/widget structure plus deep Atomic typed props/styles/repeater structure;
4. audit optional design/content sidecars;
5. run all regression tests;
6. use the committed npm lockfile and block high/critical npm findings;
7. start the pinned WordPress 7.1 / PHP 8.3 runtime;
8. install Elementor Core 4.2.4 and Hello Elementor 3.5.1;
9. optionally install Pro from Elementor's official Composer repository;
10. export and verify actual runtime widget/control inventory;
11. audit source JSON against runtime and optional safe target inventory;
12. import through Elementor's Template Library CLI as administrator;
13. export importer storage and compare semantic document data while ignoring only proven volatile normalization;
14. re-audit importer output and render it;
15. run Chromium, Firefox and WebKit at desktop/tablet/mobile plus active breakpoint boundaries;
16. capture full-page screenshots plus DOM `layout_snapshot` metadata containing bounding boxes and computed layout/style values;
17. upload evidence and tear down the disposable runtime.

## Native Website Template / Design System chain

When the requested claim concerns a native V4 Design System, Global Classes/Variables or a mixed V3/V4 Website Template, use `.github/workflows/native-kit-contract.yml` in addition to the core QA chain.

- Keep the documented `wp elementor kit export` route as a separate V3 CLI contract. In Elementor Core 4.2.4 that command runs the legacy import/export process and must not by itself be promoted to V4 Classes/Variables evidence.
- For V4/mixed package evidence, activate the required exact-version feature flags before Elementor boot, then call the runtime's own `import-export-customization` component through the generic `ejl native_kit_export` / `ejl native_kit_import` bridge. The bridge does not invent package internals; it lets Elementor register and execute its own native runners.
- Fail closed when the exact runtime does not expose the customization component or when required V4 features are inactive.
- Prove the package by inspecting the generated ZIP, confirming Global Classes/Variables files and values, resetting the disposable design-system state, importing through the same native customization process, checking repository readback, and re-exporting once more.
- Keep media identity as a separate contract. Same-site existing WordPress media must preserve a valid `id + url` pair for the tested Image, Background and Basic Gallery controls. Portable package/template import may migrate media and assign new attachment IDs; that migration must not be confused with same-site reuse.

This chain is still `controlled_runtime` evidence. It proves only the exact pinned Elementor version and feature states used by the run.

## Closed-loop comparison

Use the complete Visual Target as the predicted page model, then compare rendered screenshots/layout snapshots section by section and in whole-page context. Check alignment, widths/heights, parent ratios, direction/wrap, grid tracks, gaps, padding/margins, overflow, typography, visibility and breakpoint changes. A mismatch authorizes only the smallest confirmed repair. After a material patch, rebuild the whole-page Visual Target and rerun the affected evidence. Keep previous PASS scope frozen unless the patch can affect it.

Do not compare on visual intuition alone when exact DOM geometry exists. Do not treat DOM geometry as aesthetics or target-site proof; screenshots and human/AI visual review still matter.

## Privacy and target boundaries

The repository is public. Never commit confidential client JSON/screenshots, credentials, personal data, secret URLs or confidential inventories. Sensitive artifacts require a private runtime or exact site route. A green run remains controlled-runtime evidence only; it does not prove customer staging, target IDs/globals/conditions/dynamic values, production behavior, full accessibility or pixel-perfect equality without an approved reference. Native V4 package success also does not prove a different target where Elementor version, feature states or registered runners differ.

## Final gate

After the last implementation change, require two stable green final controlled-runtime rounds before staging/release handoff. For target or release claims, continue through `website-qa-checklist` rather than upgrading controlled-runtime evidence by wording.
