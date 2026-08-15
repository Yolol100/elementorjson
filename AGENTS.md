# Elementor JSON Lab — agent instructions

These instructions apply to the entire repository.

## Role

This repository is a **controlled runtime capability** for Project Elementor. It is not the domain owner and it is not a production deployment system.

Before changing or running Elementor JSON work:

1. Read `runtime-contract.json`.
2. Read `docs/project-elementor-integration.md` when the task concerns routing, evidence, handoff, privacy or caller behavior.
3. Treat the Elementor skill as domain owner for Elementor structure, dependencies, risk and JSON decisions.
4. Treat `webactueel-workflow` as controller for canonical Project Elementor source writes, multi-owner work, rollback and formal scan-fix-retest workflows.

## Trigger contract

Use this repository when Elementor JSON needs real disposable-runtime evidence, including source validation, widget/dependency scanning, official Template Library import behavior, semantic roundtrip, preview rendering, responsive screenshots, visual regression or Pro availability checks.

Do not turn a source-only task into a runtime run unless a runtime/visual claim is needed. Do not use this repository for production or live-site mutation.

## Privacy

This repository is public. Never commit Elementor Pro license keys or Composer auth, credentials or private download URLs, personal data, confidential client JSON or private screenshots, or unsanitized real target inventories.

Use GitHub Actions secrets for credentials and sanitized fixtures for public-repo testing. Confidential artifacts require a private controlled runtime/repository.

## Elementor correctness

- Never invent site-object, media, menu, form, template, query, Loop, Dynamic Tag or product IDs.
- Preserve V3/V4/Atomic family unless migration is explicit and proven.
- Atomic values and structures must follow a proven Elementor export/runtime shape; unknown Atomic data is not normalized by guesswork.
- Treat target inventory as availability evidence, not as proof of visual target equality.
- Third-party widgets require the matching add-on in the runtime before visual rendering can be called verified.
- A green repository run is `controlled_runtime` evidence only. It is not `target_verified`, staging proof or production proof.

## Required checks

For changes that affect JSON auditing or Python logic:

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

For workflow/runtime changes, the GitHub Actions workflow `Elementor JSON QA` must pass both jobs:

- `Static JSON audit`
- `Elementor runtime preview`

The final runtime job must use the committed npm lockfile, audit dependencies, start the pinned WordPress/PHP/Elementor runtime, export widget inventory, run the JSON auditor, import templates through Elementor's official Template Library CLI, compare semantic import readback, render isolated previews, and pass Chromium/Firefox/WebKit responsive + visual regression checks.

A formal cleanup or 10/10 controlled-runtime claim requires two complete green rounds after the last repository change.

## Change rules

- Keep `runtime-contract.json`, `README.md`, `docs/project-elementor-integration.md`, `AGENTS.md` and `.github/workflows/validate.yml` aligned.
- Pin third-party GitHub Actions to immutable full commit SHAs.
- Keep `package-lock.json` committed and use `npm ci` in the final workflow.
- Fail closed on invalid JSON, missing widgets, failed official import, semantic roundtrip drift, failed preview, dependency-audit failure, browser/runtime errors or visual regression.
- Repair only confirmed defects. Do not guess unknown Atomic, Pro, add-on or site-bound data.
- Pro mode requires both `ELEMENTOR_PRO_LICENSE_KEY` as a GitHub Actions secret and an explicit `ELEMENTOR_PRO_VERSION` repository variable. Never infer the latest Pro version.
- Preserve evidence boundaries in every report or documentation change.
