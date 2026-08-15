# Security policy

## Supported scope

This repository is a public controlled-runtime and QA harness for Elementor JSON. It is not a production WordPress plugin and must not be used to store customer secrets, credentials, personal data, private screenshots, private download URLs, license files, or confidential Elementor exports.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting / Security Advisory flow for repository vulnerabilities when available. Do not publish credentials, license keys, private URLs, client data, or exploit details in a public issue.

## Runtime secrets

`ELEMENTOR_PRO_LICENSE_KEY` may exist only as a GitHub Actions secret. A deterministic Elementor Pro run also requires an explicit version value supplied to CI; the repository must never commit a Pro ZIP, Composer auth file, license key, or private package URL.

## Public fixtures

Only sanitized, non-confidential fixtures may be committed under `templates/`, `target/`, `tests/`, or screenshot baseline directories. Real target inventories and visuals must use a private runtime when they contain confidential site or client information.

## Evidence boundary

A green run proves only the controlled environment and checks executed by CI. It does not prove production security, target-site authorization, full accessibility, or staging/production compatibility.
