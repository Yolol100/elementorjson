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

Use this repository when Elementor JSON needs real disposable-runtime evidence, including widget/dependency scanning, rendering, responsive screenshots, Pro availability checks or import-behavior checks.

Do not turn a source-only task into a runtime run unless a runtime/visual claim is actually needed. Do not use this repository for production or live-site mutation.

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
- A green repository run is `controlled_runtime` evidence only. It is not `target_verified`, staging proof or production proof.

## Required checks

For changes that affect JSON auditing or Python logic:

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

For changes that affect the runtime contract, workflow, scanner plugin, rendering, Playwright tests or integration documentation, require the GitHub Actions workflow `Elementor JSON QA` to pass both jobs:

- `Static JSON audit`
- `Elementor runtime preview`

The static job must validate `runtime-contract.json`. The runtime job must start WordPress/Elementor, export widget inventory, audit templates, render them, capture desktop/tablet/mobile screenshots and upload artifacts.

## Change rules

- Keep `runtime-contract.json`, `README.md`, `docs/project-elementor-integration.md` and `.github/workflows/validate.yml` aligned.
- Fail closed on unknown widgets, invalid JSON, failed render or failed browser tests.
- Repair only confirmed defects. Do not guess unknown Atomic, Pro, add-on or site-bound data.
- Keep Pro credentials outside the repository; `ELEMENTOR_PRO_LICENSE_KEY` may exist only as a GitHub Actions secret.
- Preserve evidence boundaries in every report or documentation change.
