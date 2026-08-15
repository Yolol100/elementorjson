# Elementor JSON Lab

A reusable QA pipeline for Elementor JSON templates. It combines source-level JSON checks with a disposable WordPress + Elementor runtime and browser screenshots.

`runtime-contract.json` is the machine-readable contract that tells Project Elementor and the Elementor skill when this repository is the correct controlled runtime, why it is used, which inputs it accepts, what it must execute and which evidence it may return. The detailed caller/handoff contract is documented in `docs/project-elementor-integration.md`.

## When Project Elementor should use this repository

Use this repository when Elementor JSON must move beyond source-only inspection into reproducible runtime evidence, including:

- new or screenshot-reconstructed Elementor JSON that must be rendered or visually checked;
- existing JSON changes to structure, widgets, widget settings, responsive behavior or dependencies;
- requests to test, scan, render, preview, screenshot, verify widgets, verify Pro or check import behavior;
- any claim that source-valid JSON also works in a real disposable WordPress/Elementor runtime.

Do not use it for explanation/planning only, production writes, or exact target compatibility without target evidence. Because this repository is public, never commit confidential client JSON, private screenshots, credentials, personal data, license keys or secret URLs. Use sanitized fixtures or a private controlled runtime for sensitive work.

## What it does

1. Reads Elementor export JSON from `templates/`.
2. Audits the document structure, element IDs, editor family, `widgetType` values and widget settings.
3. Starts a disposable WordPress environment with Hello Elementor and Elementor Free.
4. Optionally installs and activates Elementor Pro when the repository secret `ELEMENTOR_PRO_LICENSE_KEY` is configured.
5. Uses the included WordPress plugin to export the widgets and controls actually registered by Elementor in that runtime.
6. Fails when a JSON template requests a widget that the runtime does not provide.
7. Renders valid templates into isolated Elementor Canvas pages.
8. Captures desktop, tablet and mobile screenshots with Playwright.
9. Uploads audit reports, runtime metadata, render manifests and screenshots as GitHub Actions artifacts.

## Repository layout

```text
.github/workflows/validate.yml        GitHub Actions QA pipeline
.wp-env.json                          Disposable WordPress/Elementor environment
runtime-contract.json                 Machine-readable trigger/runtime/evidence contract
docs/project-elementor-integration.md Detailed Project Elementor caller/handoff contract
package.json                          wp-env and Playwright versions
playwright.config.js                  Browser test configuration
templates/                            Put Elementor JSON templates here
target/inventory.json                 Optional target-site widget inventory
tools/audit_elementor_json.py         JSON/widget/settings auditor
wordpress-plugin/elementor-json-lab/  Runtime scanner + preview WP-CLI commands
tests/                                Auditor and browser tests
```

## Normal workflow

Put one or more Elementor JSON exports directly in `templates/`, for example:

```text
templates/homepage.json
```

Push or update the file. The `Elementor JSON QA` workflow runs automatically. CI first validates `runtime-contract.json`, so the repository fails closed if its routing/evidence contract drifts.

The workflow produces:

- `static-audit`: source-only JSON reports.
- `elementor-runtime-qa`: registered widget inventory, runtime audit, render manifests, Elementor Pro status, Playwright report and desktop/tablet/mobile screenshots.

Template filenames become preview slugs. `homepage.json` is rendered at `/homepage/` inside the temporary test site.

## Elementor Pro

Elementor Pro is never committed to this repository. The CI workflow uses Elementor's official Composer repository when a license key is available.

One-time GitHub setup:

1. Open the repository settings.
2. Go to `Secrets and variables` > `Actions`.
3. Create a repository secret named exactly `ELEMENTOR_PRO_LICENSE_KEY`.
4. Paste your valid Elementor Pro license key as the secret value.

On the next workflow run the pipeline will automatically:

1. Install Elementor Core.
2. Authenticate Composer against `composer.elementor.com` using the secret.
3. Install `elementor/elementor-pro` through Composer.
4. Activate the Elementor Pro plugin.
5. Activate the Pro license through Elementor CLI.
6. Export the actual Core + Pro widget/control inventory.
7. Audit and render the supplied JSON using that runtime.
8. Create desktop, tablet and mobile screenshots.
9. Deactivate the temporary Pro license before destroying the WordPress environment.

If the secret is not configured, the same workflow continues in Elementor Free mode. The artifact contains `elementor-pro-status.json` so it is explicit which runtime was used.

Do not commit the license key, an Elementor Pro ZIP, Composer auth files, private download URLs or other credentials to this public repository.

## Target-site and add-on inventory

For accurate ownership/dependency checks against a real installation, install `wordpress-plugin/elementor-json-lab` on a controlled WordPress/Elementor environment and export its inventory:

```bash
wp ejl inventory --output=/tmp/inventory.json
```

Save the resulting JSON as `target/inventory.json`. The auditor can then distinguish widgets registered by Elementor Core, Elementor Pro and third-party add-ons on that target.

A target inventory proves availability in the scanned installation. Add-on widgets still require the matching add-on plugin in the preview runtime before their visual rendering can be considered verified.

## Commands

Audit a template without WordPress:

```bash
python tools/audit_elementor_json.py templates/homepage.json
```

Audit against an exported target inventory:

```bash
python tools/audit_elementor_json.py templates/homepage.json \
  --inventory target/inventory.json \
  --output artifacts/homepage-target.json
```

Create/update a preview page inside a WordPress runtime where the plugin is active:

```bash
wp ejl render /path/to/homepage.json --slug=homepage
```

## Evidence boundary

A clean source audit is not the same as a verified target import. This repository returns `controlled_runtime` evidence: it can prove its disposable runtime, widget availability and configured viewport renders, but it cannot by itself prove exact customer staging compatibility, target-specific IDs, production behavior or full accessibility compliance.
