# Elementor JSON Lab

A controlled-runtime QA pipeline for Elementor JSON. It combines source-level validation with a pinned disposable WordPress/Elementor runtime, official Template Library import/readback, semantic roundtrip comparison, direct preview rendering and cross-browser responsive visual regression.

`runtime-contract.json` is the machine-readable evidence contract. `docs/project-elementor-integration.md` describes how Project Elementor calls this repository.

## Use this repository when

Use it when Elementor JSON must move beyond source inspection into reproducible runtime evidence: new or screenshot-reconstructed JSON, structural/widget/responsive changes, import checks, Pro dependency checks, preview rendering or visual verification.

Do not use it for production writes or as proof of an exact customer target. This repository is public: never commit confidential client JSON, private screenshots, real credentials, license keys, private URLs or unsanitized target inventories.

## Hardened pipeline

The final GitHub Actions workflow:

1. Validates `runtime-contract.json` and pinned versions.
2. Runs auditor + semantic-roundtrip unit tests and PHP syntax checks.
3. Source-audits every template for wrapper/tree/IDs, classic/Atomic/mixed family, Atomic required fields/typed props, duplicate style variants, repeater IDs, responsive controls, globals, dynamic references and potential site-bound references.
4. Installs the committed npm dependency tree with `npm ci` and runs `npm audit`.
5. Starts pinned WordPress 7.0.4 on PHP 8.3 and installs pinned Elementor Core 4.2.2 + Hello Elementor 3.4.9.
6. Optionally installs an explicitly version-pinned Elementor Pro package through Elementor's Composer repository.
7. Exports actual widget/control/breakpoint inventory and audits every JSON file against it.
8. Imports every template through Elementor's official `wp elementor library import` command.
9. Re-reads the imported `elementor_library` data and compares source vs imported content/page settings semantically; generated element IDs are ignored, semantic drift is not.
10. Renders a separate isolated Elementor Canvas preview.
11. Runs Chromium, Firefox and WebKit at desktop/tablet/mobile plus discovered extra Elementor breakpoints.
12. Fails on browser/console/request/resource errors, horizontal overflow, invalid nested interactive controls, failed keyboard-focus sanity, visual baseline regression or other configured checks; reduced-motion rendering is exercised.
13. Uploads audit/import/runtime/browser evidence and always tears down the environment.

## Repository layout

```text
.github/workflows/validate.yml          Final read-only QA pipeline
.github/dependabot.yml                  Dependency update policy
.github/CODEOWNERS                      Code ownership
.wp-env.json                            Pinned disposable WordPress/PHP environment
SECURITY.md                             Secret/reporting/evidence policy
runtime-contract.json                   Machine-readable runtime/evidence contract
docs/project-elementor-integration.md   Project Elementor caller/handoff contract
package.json + package-lock.json         Locked wp-env/Playwright tooling
playwright.config.js                    Chromium/Firefox/WebKit configuration
templates/                              Sanitized Elementor JSON fixtures
target/inventory.json                   Optional sanitized target inventory
tools/audit_elementor_json.py           Source/runtime JSON auditor
tools/compare_elementor_roundtrip.py    Import semantic comparator
wordpress-plugin/elementor-json-lab/    Inventory/preview/import-readback WP-CLI helper
tests/                                  Unit tests, browser QA and visual baselines
```

## Normal workflow

Place one or more non-confidential Elementor export JSON files in `templates/`, for example `templates/homepage.json`, then open/update a pull request. The `Elementor JSON QA` workflow must pass:

- `Static JSON audit`
- `Elementor runtime preview`

A formal clean/10-out-of-10 `controlled_runtime` claim requires two complete green rounds after the last repository change.

## Runtime versions

Current controlled baseline is declared in `runtime-contract.json` and enforced by CI:

- WordPress 7.0.4
- PHP 8.3
- Elementor Core 4.2.2
- Hello Elementor 3.4.9
- `@wordpress/env` 11.11.0
- `@playwright/test` 1.61.1

Changing a pin is a deliberate runtime-contract change, not an automatic latest-version update.

## Elementor Pro

Pro is never committed. To enable deterministic Pro coverage configure both:

- GitHub Actions secret: `ELEMENTOR_PRO_LICENSE_KEY`
- GitHub repository variable: `ELEMENTOR_PRO_VERSION`

If only one is configured, CI fails closed. When both are present, the workflow authenticates to Elementor's official Composer repository, installs exactly the requested Pro version, activates the plugin/license, runs the same import/runtime/browser gates and deactivates the temporary license during teardown.

Without both values the pipeline explicitly runs Free/Core mode.

## Target inventory

A controlled installation can export widget/control availability with:

```bash
wp ejl inventory --output=/tmp/inventory.json
```

Only a deliberately sanitized inventory may be placed at `target/inventory.json` in this public repository. A real confidential target requires a private controlled runtime. Inventory proves observed availability only; add-on rendering requires the actual matching add-on and staging remains a separate gate.

## Commands

Source audit:

```bash
python tools/audit_elementor_json.py templates/homepage.json
```

Audit against a sanitized target inventory:

```bash
python tools/audit_elementor_json.py templates/homepage.json \
  --inventory target/inventory.json \
  --output artifacts/homepage-target.json
```

Direct isolated preview inside an active runtime:

```bash
wp ejl render /path/to/homepage.json --slug=homepage
```

Read back an item already imported by Elementor's Template Library importer:

```bash
wp ejl export-template <elementor_library-post-id> --output=/tmp/reexport.json
```

Compare semantic import readback:

```bash
python tools/compare_elementor_roundtrip.py source.json reexport.json
```

## Evidence boundary

A clean source audit is not a runtime claim. A clean runtime is not a customer-target claim. This repository returns at most `controlled_runtime` evidence for its pinned disposable environment. Exact customer IDs/dynamic data, staging behavior, production behavior, real form delivery/uploads, WooCommerce transactions and full accessibility compliance require their own target/staging evidence.
