# Elementor JSON Lab — agent instructions

These instructions apply to the entire repository.

## Role

This private repository is a controlled runtime capability for Project Elementor. It is not the domain owner, workflow controller, live WordPress bridge or production deployment system.

Before changing or running Elementor JSON work:

1. Read `runtime-contract.json` and `toolkit-contract.json`.
2. Read `docs/project-elementor-integration.md` for routing, evidence, handoff or privacy work.
3. Treat the `elementor` Skill as owner of structure, dependencies, risk, Visual Target interpretation and JSON decisions.
4. Treat `webactueel-workflow` as controller for cross-skill work, project-source writes, rollback and closure.
5. Use this repository only when its controlled-runtime evidence is actually needed.

## Visual Target

- Build one whole-page Visual Target before section-level visual repair.
- Preserve provenance: `explicit`, `declared`, `inferred`, `unknown`.
- Keep `evidence_class=source_prediction` and `render_observed=false` until a real render exists.
- Never invent layout, typography, media, dynamic values or site identities absent from trusted input.
- Rebuild the whole-page target after every material JSON patch.
- Prefer screenshot plus DOM `layout_snapshot` evidence for observable geometry.

## Runtime boundary

Use this runtime for widget/dependency checks, importer roundtrips, rendering, responsive screenshots, layout snapshots, Pro availability, same-site media identity, and native V3/V4/mixed Kit contracts.

For V4 Classes/Variables, use Elementors own `import-export-customization` component through the EJL bridge. Keep the documented V3 CLI export path separate and do not promote it to V4 evidence.

Do not turn a source-only task into a runtime run. Do not use this repository for live-site mutation; use the canonical, preflight-ready `wordpressconnector` route when a live WordPress action is required.

## Privacy and repository hygiene

Private storage does not authorize unrestricted client data.

- Never commit secrets, credentials, private download URLs, license keys or personal data.
- Keep task-specific JSON, screenshots and inventories temporary and run-scoped unless project policy explicitly permits otherwise.
- Keep project truth and target-specific request state off `main`.
- Use GitHub Actions Secrets for permitted credentials.
- Remove unexplained target/run residue before closure.

## Elementor correctness

- Never invent site-object, media, menu, form, template, query, Loop, Dynamic Tag or product IDs.
- Preserve V3/V4/Atomic family unless migration is explicit and proven.
- Treat inventory as availability evidence, not visual-equality evidence.
- Require matching add-ons before third-party widgets can be rendered as verified.
- Bind native package claims to the exact runtime version and feature states.
- Treat a green run as `controlled_runtime`, never as `target_verified`, staging or production proof.

## Required checks

For Python/JSON logic:

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

For affected runtime behavior require the relevant workflows:

- `Page Composition Contract`
- `Elementor JSON QA`
- `Native Elementor Kit Contract` when native Kit, V4, media identity or package behavior changes

The standard runtime must validate/import/roundtrip, render, test desktop/tablet/mobile plus active breakpoints, and upload run-scoped evidence. The native-kit job must use the pinned runtime and verify the exact V3/V4/mixed behavior in scope.

## Change rules

- Keep `runtime-contract.json`, `toolkit-contract.json`, README, integration docs, contracts, tests and workflows aligned.
- Fail closed on invalid/unknown JSON, missing dependencies, failed import/render/browser/package validation or contract drift.
- Repair only confirmed defects.
- Preserve evidence boundaries in every output.
- Require two stable green controlled-runtime final rounds after the last implementation change before a staging/release handoff claim.
