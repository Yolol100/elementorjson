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

Dependabot monitors npm and GitHub Actions updates. [CVE-2026-97058](https://github.com/advisories/ghsa-hp3w-g68c-fv3c) has no upstream patched `sprintf-js` release. The pinned development-only dependency tree now overrides `argparse` to `2.0.1`, which removes `sprintf-js` instead of falsely claiming a patched version. Verify `npm ci`, `npm audit --audit-level=low`, `js-yaml` parsing and the WordPress/Elementor runtime after each change to the override. Reassess this workaround when `@wordpress/env` no longer depends on `js-yaml@3`; never ignore newly detected advisories.

## Evidence boundary

A green repository run proves only the controlled environment and checks that actually executed. It does not prove target authorization, staging/production compatibility, full accessibility, production security or live-site correctness.
