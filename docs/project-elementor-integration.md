# Project Elementor integration

This repository is the Project Elementor `controlled_runtime` for Elementor JSON validation, widget/dependency inspection, real disposable WordPress/Elementor rendering and responsive screenshots.

## Trigger

Call this repository when any of the following is true:

- new Elementor JSON, including JSON reconstructed from a screenshot, needs a runtime or visual claim;
- existing Elementor JSON changes structure, widgets, widget settings, responsive behavior or dependencies;
- the user asks to test, scan, render, preview, screenshot, verify widgets, verify Elementor Pro or check import behavior;
- source-valid JSON is about to be described as runtime-valid or visually correct.

Do not call it for explanation or source-only planning when no runtime claim is needed.

## Why

Use the repository to separate source inspection from real runtime evidence. It must detect unavailable widgets, identify Core/Pro/third-party ownership where the runtime can prove it, inspect registered controls, render the template in a disposable Elementor installation and return desktop/tablet/mobile screenshots.

## Caller contract

The Elementor skill remains the domain owner. `webactueel-workflow` remains the controller for project-source writes, multi-owner work, rollback and formal scan-fix-retest flows. The repository is a capability, never a second domain owner.

Before calling:

1. Classify the artifact, editor family/structure, dependency mode, target objects and risk.
2. Keep unknown site IDs, Dynamic Tags, Forms, Loops, queries, conditions and add-on data unknown; never invent them.
3. Use a sanitized fixture when the real input is confidential because this repository is public.
4. If exact target compatibility is required, provide a controlled `target/inventory.json` and still treat staging as a separate later gate.

## Invocation

1. Put the canonical test JSON under `templates/`.
2. Optionally provide `target/inventory.json` exported by `wp ejl inventory` from a controlled target installation.
3. Configure `ELEMENTOR_PRO_LICENSE_KEY` only as a GitHub Actions secret when Pro runtime coverage is required.
4. Let `.github/workflows/validate.yml` execute the source audit and controlled runtime.
5. Read the `static-audit` and `elementor-runtime-qa` artifacts.
6. Inspect runtime inventory, runtime audit, render manifests, Pro status and all three screenshot classes.
7. On a confirmed defect or visual mismatch, edit the canonical JSON and rerun the same pipeline.

## Evidence boundary

A green run supports `controlled_runtime` evidence for the disposable environment. It does not prove:

- exact customer staging compatibility;
- `target_verified` status;
- production behavior;
- site-specific object IDs or live dynamic data;
- full accessibility compliance.

Target/staging/browser acceptance remains a separate gate and belongs to the appropriate staging/QA route.

## Failure behavior

Fail closed when `runtime-contract.json` is invalid, a requested widget is missing from the runtime, the JSON audit fails, Elementor cannot render the template or the browser test fails. Repair only confirmed defects and rerun; do not guess unknown Atomic, Pro, add-on or site-bound data.

## Privacy and secrets

Never commit Elementor Pro keys, Composer auth, credentials, private download URLs, personal data, confidential client JSON or private screenshots. Use GitHub Actions secrets for Pro credentials and a private runtime/repository for confidential artifacts.

## Canonical machine contract

`runtime-contract.json` is the machine-readable form of this policy. CI validates it before the normal JSON tests. If this document and `runtime-contract.json` conflict, fix the drift before relying on the repository.
