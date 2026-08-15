# Elementor JSON Lab

A reusable QA pipeline for Elementor JSON templates. It combines source-level JSON checks with a disposable WordPress + Elementor runtime and browser screenshots.

## What it does

1. Reads Elementor export JSON from `templates/`.
2. Audits the document structure, element IDs, editor family, `widgetType` values and widget settings.
3. Starts a disposable WordPress environment with Hello Elementor and Elementor Free.
4. Uses the included WordPress plugin to export the widgets and controls actually registered by Elementor in that runtime.
5. Fails when a JSON template requests a widget that the runtime does not provide.
6. Renders valid templates into isolated Elementor Canvas pages.
7. Captures desktop, tablet and mobile screenshots with Playwright.
8. Uploads audit reports, runtime metadata, render manifests and screenshots as GitHub Actions artifacts.

## Repository layout

```text
.github/workflows/validate.yml        GitHub Actions QA pipeline
.wp-env.json                          Disposable WordPress/Elementor environment
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

Push or update the file. The `Elementor JSON QA` workflow runs automatically.

The workflow produces:

- `static-audit`: source-only JSON reports.
- `elementor-runtime-qa`: registered widget inventory, runtime audit, render manifests, Playwright report and desktop/tablet/mobile screenshots.

Template filenames become preview slugs. `homepage.json` is rendered at `/homepage/` inside the temporary test site.

## Elementor Pro and add-ons

The public CI baseline intentionally installs Elementor Free only. Do not commit licensed Elementor Pro packages, credentials or private download URLs to this public repository.

For accurate ownership/dependency checks against a real installation, install `wordpress-plugin/elementor-json-lab` on a controlled WordPress/Elementor environment and export its inventory:

```bash
wp ejl inventory --output=/tmp/inventory.json
```

Save the resulting JSON as `target/inventory.json`. The auditor can then distinguish widgets registered by Elementor Core, Elementor Pro and third-party add-ons on that target.

A target inventory proves availability in the scanned installation; it does not make Pro/add-on widgets render in the public Free-only CI runtime. A visual preview of those widgets requires a legally available matching plugin runtime.

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

A clean source audit is not the same as a verified target import. The strongest portable result from this repository is a reproducible runtime preview. Exact compatibility with a customer installation still depends on its Elementor/Pro/add-on versions, editor family, globals, dynamic objects and site-specific IDs.
