# Security policy

## Supported scope

This private repository is a controlled-runtime and QA harness for Elementor JSON. It is not a production deployment system or live WordPress bridge.

## Reporting a vulnerability

Use GitHub private vulnerability reporting / Security Advisory flow when available. Do not place credentials, license keys, private URLs, client data, exploit details or other secrets in an issue or pull request.

## Runtime secrets

`ELEMENTOR_PRO_LICENSE_KEY` may exist only as a GitHub Actions secret. Never commit a Pro ZIP, Composer authentication file, license key, private package URL or other credential.

## Fixtures and evidence

Only sanitized, task-appropriate fixtures belong on `main`. Customer JSON, screenshots, inventories and run-scoped evidence must follow the repository hygiene policy and must not become permanent default-branch project truth.

## Evidence boundary

A green repository run proves only the controlled environment and checks that actually executed. It does not prove target authorization, staging/production compatibility, full accessibility, production security or live-site correctness.
