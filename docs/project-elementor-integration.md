# Project Elementor integration

This repository is the Project Elementor `controlled_runtime` for Elementor JSON source validation, dependency inspection, official Template Library import readback, disposable WordPress/Elementor preview rendering and cross-browser responsive visual regression.

## Trigger

Call this repository when any of the following is true:

- new Elementor JSON, including JSON reconstructed from a screenshot, needs a runtime or visual claim;
- existing Elementor JSON changes structure, widgets, widget settings, responsive behavior or dependencies;
- the user asks to test, scan, render, preview, screenshot, verify widgets, verify Elementor Pro or check import behavior;
- source-valid JSON is about to be described as runtime-valid, importer-valid or visually correct.

Do not call it for explanation or source-only planning when no runtime claim is needed.

## Caller contract

The Elementor skill remains the domain owner. `webactueel-workflow` remains the controller for project-source writes, multi-owner work, rollback and formal scan-fix-retest flows. The repository is a capability, never a second domain owner.

Before calling:

1. Classify artifact, editor family, dependency mode, target objects and risk.
2. Keep unknown site IDs, Dynamic Tags, Forms, Loops, queries, conditions, globals/classes/variables and add-on data unknown; never invent them.
3. Use only sanitized fixtures in this public repository.
4. Treat `target/inventory.json` as optional sanitized availability evidence, never as staging or visual target proof.
5. Use a private runtime/repository for confidential target inventories, JSON or reference screenshots.

## Controlled runtime sequence

The final `.github/workflows/validate.yml` must execute these independent gates:

1. Validate `runtime-contract.json` and pinned runtime versions.
2. Run Python auditor/roundtrip unit tests and PHP syntax checks.
3. Source-audit every template, including classic/Atomic/mixed structure, IDs, repeaters, responsive controls and target-bound reference warnings.
4. Install dependencies from committed `package-lock.json` with `npm ci` and run `npm audit`.
5. Start the pinned WordPress/PHP runtime and install pinned Elementor Core + Hello Elementor.
6. Enable Elementor Pro only when both a secret license key and an explicit Pro version are configured.
7. Export the actual runtime widget/control/breakpoint inventory.
8. Audit JSON against that inventory and optional sanitized target inventory.
9. Import each template through Elementor's official `wp elementor library import` CLI route.
10. Read the imported `elementor_library` post and semantically compare stored content/page settings with source JSON; generated element IDs may differ, semantic settings may not.
11. Render a separate isolated Canvas preview.
12. Run Chromium, Firefox and WebKit at desktop/tablet/mobile plus discovered extra Elementor breakpoints, with browser/resource/error, overflow, nested-interactive, keyboard-focus and reduced-motion checks.
13. Compare screenshots with committed sanitized visual baselines.
14. Upload evidence and always tear down the runtime/deactivate a temporary Pro license.

## Evidence boundary

A green run supports `controlled_runtime` evidence for exactly the pinned disposable environment and checks executed. It does not prove exact customer staging compatibility, `target_verified`, production behavior, site-specific object/dynamic correctness, real form delivery/uploads, WooCommerce transactions, confidential target equality or full accessibility compliance.

Target/staging acceptance remains a separate gate and belongs to `website-qa-checklist` where required.

## Pro mode

`ELEMENTOR_PRO_LICENSE_KEY` must be a GitHub Actions secret. `ELEMENTOR_PRO_VERSION` must be an explicit repository variable. If only one is configured, the workflow fails closed. The Pro package, license key, Composer auth and private URLs must never be committed.

## Failure behavior

Fail closed when the runtime contract drifts, dependency audit fails, a requested widget is missing, source JSON is invalid, official import fails, semantic import readback differs, preview rendering fails, browser/resource checks fail or visual regression exceeds the configured tolerance. Repair only confirmed defects and rerun the unchanged final pipeline.

## Final gate

After the last repository change, require two complete green rounds before describing the repository as formally clean or 10/10 at `controlled_runtime` level. This still does not elevate the result to staging or production proof.

## Canonical machine contract

`runtime-contract.json` is the machine-readable form of this policy. If this document, `AGENTS.md`, README or workflow conflict with it, fix the drift before relying on repository output.
