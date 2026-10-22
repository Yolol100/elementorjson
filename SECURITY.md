# Security policy

## Supported scope

This public repository is a controlled-runtime and QA harness for Elementor JSON. It is not a production deployment system or live WordPress bridge.

## Reporting a vulnerability

Use GitHub private vulnerability reporting / Security Advisory flow when available. Do not place credentials, license keys, private URLs, client data, exploit details or other secrets in an issue or pull request.

## Runtime secrets

`ELEMENTOR_PRO_LICENSE_KEY` may exist only as a GitHub Actions secret. Never commit a Pro ZIP, Composer authentication file, license key, private package URL or other credential.

## Fixtures and evidence

This public repository and its Git history are visible to anyone. Only sanitized, task-appropriate fixtures belong on `main`. Customer JSON, screenshots, inventories and run-scoped evidence must follow the repository hygiene policy and must not become permanent default-branch project truth.

## Automated security checks and residual dependency risk

GitHub CodeQL scans supported JavaScript/TypeScript, Python and GitHub Actions sources on changes and weekly. CodeQL does not scan this project's PHP source; WordPress runtime and other PHP/security acceptance require separate checks.

Dependabot monitors npm and GitHub Actions updates. [CVE-2026-97058](https://github.com/advisories/ghsa-hp3w-g68c-fv3c) has no upstream `sprintf-js` patch. This repository removes the vulnerable development-only dependency chain `@wordpress/env -> js-yaml@3 -> argparse@1 -> sprintf-js` by pinning `argparse@2.0.1` in npm `overrides`. Keep `npm ci`, `npm audit`, the lockfile regression and the pinned WordPress CLI smoke tests green. Reevaluate the override when `@wordpress/env` drops `js-yaml@3` naturally; do not claim a patched `sprintf-js` version.

## Public pull request isolation

Automatic pull request and main-push QA must run in Free/Core mode. Even if
`ELEMENTOR_PRO_LICENSE_KEY` is configured later, it is available only when the
runtime QA workflow is **manually dispatched on `main`**. This prevents an
automated pull request from receiving the license credential via WordPress
plugin code or shell steps. GitHub workflow `validate.yml` includes a negative
regression test to reject unguarded Pro secret references.

## Evidence boundary

A green repository run proves only the controlled environment and checks that actually executed. It does not prove target authorization, staging/production compatibility, full accessibility, production security or live-site correctness.
