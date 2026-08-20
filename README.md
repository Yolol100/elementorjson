# Elementor JSON Lab

Controlled-runtime QA for Elementor JSON. The repository validates source JSON, exercises Elementor's Template Library importer, compares importer storage semantically, renders the imported result in a pinned disposable WordPress/Elementor runtime, and runs responsive browser checks.

`runtime-contract.json` is the machine-readable evidence contract. Project Elementor remains the domain owner; this repository is only the controlled-runtime capability.

## When to use it

Use this repository when Elementor JSON needs evidence beyond source inspection, including new or screenshot-reconstructed JSON, structural/widget/responsive changes, importer or roundtrip checks, browser rendering, dependency checks, or Pro/runtime verification.

Do not use it for production writes or claim exact target compatibility without target/staging evidence. The repository is public: never commit credentials, license keys, personal data, confidential client JSON/screenshots, private URLs, or confidential target inventories.

## Current QA chain

1. Validate `runtime-contract.json` and run Python unit tests.
2. Run the classic/widget auditor plus deep Classic/Atomic structural checks, including typed Atomic props/styles and repeater-ID checks.
3. Install the exact npm dependency graph with `npm ci` and fail on high/critical npm audit findings.
4. Start pinned WordPress 7.0.4 / PHP 8.3 via wp-env.
5. Install pinned Elementor Core 4.2.2 and Hello Elementor 3.4.9.
6. Optionally install/activate Elementor Pro from Elementor's official Composer repository when `ELEMENTOR_PRO_LICENSE_KEY` exists as an Actions secret.
7. Export the registered widget/control inventory and verify runtime versions.
8. Audit source JSON against the runtime and optional sanitized target inventory.
9. Import every template through `wp --user=admin elementor library import`.
10. Export the importer-stored document and compare `content` + `page_settings` semantically. Element IDs are treated as importer-volatile; the proven importer omission of `isInner: false` is accepted only on importer output. Source JSON remains strict.
11. Re-audit importer output and render it to isolated Elementor Canvas pages.
12. Test Chromium, Firefox and WebKit at desktop/tablet/mobile plus active Elementor breakpoint boundaries, including reduced-motion, console/page errors, same-origin failed requests/4xx/5xx, broken images, horizontal overflow and basic keyboard focus.
13. Upload dependency, audit, importer/roundtrip, inventory, render, Pro-status, screenshot and Playwright evidence; then tear the runtime down.

## Repository layout

```text
.github/workflows/validate.yml          Main QA pipeline
.github/dependabot.yml                  Weekly npm and Actions dependency updates
.wp-env.json                            Pinned disposable WordPress/PHP environment
package.json / package-lock.json        Exact Node dependency contract
runtime-contract.json                   Machine-readable evidence boundary
docs/project-elementor-integration.md   Project routing/handoff contract
templates/                              Canonical sanitized Elementor JSON fixtures
target/inventory.json                   Optional sanitized target inventory
tools/audit_elementor_json.py           Classic/widget/dependency auditor
tools/validate_elementor_deep.py        Deep Classic/Atomic structural validator
tools/compare_elementor_roundtrip.py    Importer semantic comparison
wordpress-plugin/elementor-json-lab/    Runtime inventory/export/render CLI helper
tests/                                  Unit and Playwright browser tests
```

## Elementor Pro

Pro is never committed. Configure one repository Actions secret named exactly `ELEMENTOR_PRO_LICENSE_KEY`. When present, CI authenticates to Elementor's Composer repository, installs Pro, activates its license, verifies that a Pro version and Pro-owned widgets exist in the runtime inventory, runs the same audit/import/render/browser chain, and deactivates the temporary license during cleanup.

Without that secret the run is explicitly Free-only; `elementor-pro-status.json` records the mode. A green Free-only run is not Pro evidence.

## Target inventory

`wp ejl inventory --output=/tmp/inventory.json` can export a controlled installation's registered widget/control inventory. Only put it in `target/inventory.json` when it is safe for this public repository. A target inventory proves availability only; it does not prove target rendering, site IDs, globals, conditions, dynamic data, or staging behavior. Confidential targets require a private runtime/input route.

## Evidence boundary

A green run supports only `controlled_runtime` evidence for the exact pinned disposable environment and covered fixtures. It does not by itself prove customer staging compatibility, `target_verified`, production behavior, editor UI reopen/save/re-export, site-specific objects/globals/conditions/dynamic data, Pro when the secret was absent, pixel-perfect equality without an approved reference visual, or full accessibility/assistive-technology compliance.

For formal completion after implementation changes, require two stable green final controlled-runtime rounds, then use staging/`website-qa-checklist` when target or release claims are required.
