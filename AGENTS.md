# Elementor JSON Lab — agent instructions

These instructions apply to the entire repository.

## Role

This repository is a **controlled runtime capability** for Project Elementor. It is not the domain owner and it is not a production deployment system.

Before changing or running Elementor JSON work:

1. Read `runtime-contract.json`.
2. Read `docs/project-elementor-integration.md` when the task concerns routing, evidence, handoff, privacy or caller behavior.
3. Treat the Elementor Skill as domain owner for Elementor structure, dependencies, risk, visual-target interpretation and JSON decisions.
4. Treat `webactueel-workflow` as controller for canonical Project Elementor source writes, multi-owner work, rollback and formal scan-fix-retest workflows.

## Visual Target contract

- Build the whole-page Visual Target before section-level visual repair when the input is safe for this public repository.
- Keep prediction provenance explicit: `explicit`, `declared`, `inferred`, `unknown`.
- A generated Visual Target is always `source_prediction` with `render_observed=false`; never treat it as screenshot/browser/target proof.
- Do not invent exact layout, spacing, typography, media or dynamic values that are absent from source/declared intent.
- After a material JSON patch, rebuild the whole-page Visual Target before comparing the next render.
- Prefer screenshot + DOM `layout_snapshot` evidence over visual intuition alone for observable geometry, while preserving the evidence boundary that controlled runtime is not target staging.

## Trigger contract

Use this repository when Elementor JSON needs real disposable-runtime evidence, including widget/dependency scanning, Visual Target artifacts, rendering, responsive screenshots/layout snapshots, Pro availability checks, import-behavior checks, same-site media identity checks or exact-runtime native Website Template/Design System package checks.

For V4 Classes/Variables or mixed V3/V4 native package claims, use the runtime's own Elementor `import-export-customization` component through the generic EJL bridge. Keep the documented `wp elementor kit export` route as a separate legacy V3 CLI contract; do not promote it to V4 evidence when the runtime does not do so itself.

Do not turn a source-only task into a runtime run unless a runtime/visual/package claim is actually needed. Do not use this repository for production or live-site mutation.

## Privacy

This repository is public. Never commit:

- Elementor Pro license keys or Composer auth;
- passwords, API keys, credentials or private download URLs;
- personal data;
- confidential client JSON or private screenshots;
- site exports containing secrets or private customer data.

Use GitHub Actions secrets for credentials and sanitized fixtures for public-repo testing. Confidential artifacts require a private controlled runtime/repository.

## Elementor correctness

- Never invent site-object, media, menu, form, template, query, Loop, Dynamic Tag or product IDs.
- Preserve V3/V4/Atomic family unless migration is explicit and proven.
- Treat target inventory as availability evidence, not as proof of visual target equality.
- Third-party widgets require the matching add-on in the runtime before visual rendering can be called verified.
- Native package evidence is bound to the exact Elementor version and feature states captured by that controlled runtime.
- Portable imports may migrate media and allocate new attachment IDs; same-site existing-media reuse must preserve and live-validate the WordPress `id + url` pair.
- A green repository run is `controlled_runtime` evidence only. It is not `target_verified`, staging proof or production proof.

## Required checks

For changes that affect JSON auditing or Python logic:

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

For changes that affect Visual Target contracts/building, composition wiring, runtime contract, workflow, scanner plugin, rendering, Playwright tests or integration documentation, require the relevant GitHub Actions workflows to pass:

- `Page Composition Contract` — repository contracts, composition lint and Visual Target artifacts;
- `Elementor JSON QA` — `Static JSON audit` and `Elementor runtime preview`;
- `Native Elementor Kit Contract` — required when native Kit/Design-System behavior, the EJL native-kit bridge, V4 feature gating, media identity, native package workflow or its documented contract is changed.

The standard runtime job must start WordPress/Elementor, export widget inventory, audit/import/roundtrip templates, render them, capture desktop/tablet/mobile + active-breakpoint screenshots and layout metadata, and upload artifacts.

The native-kit job must use the pinned runtime, enable required V4 features before Elementor boot when V4 evidence is in scope, keep the documented V3 CLI package route separate, exercise Elementor's own `import-export-customization` component for V4/mixed export-import-reexport, verify Global Classes/Variables readback, verify same-site Image/Background/Basic Gallery media identity, and upload run-scoped artifacts.

## Change rules

- Keep `runtime-contract.json`, `toolkit-contract.json`, README, `docs/project-elementor-integration.md`, `AGENTS.md`, contracts and workflows aligned.
- Fail closed on unknown widgets, invalid JSON, failed render, failed native-package verification or failed browser tests.
- Repair only confirmed defects. Do not guess unknown Atomic, Pro, add-on or site-bound data.
- Keep Pro credentials outside the repository; `ELEMENTOR_PRO_LICENSE_KEY` may exist only as a GitHub Actions secret.
- Preserve evidence boundaries in every report or documentation change.
- After the final implementation change, require two stable green controlled-runtime final rounds before a release/staging handoff claim.
