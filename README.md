# Elementor JSON Lab

A controlled QA runtime for Elementor JSON. It validates source structure and dependencies, imports templates through Elementor's official Template Library CLI, reopens/saves/re-exports them for semantic roundtrip comparison, renders the roundtripped data in disposable WordPress, and runs cross-browser responsive/browser/accessibility/visual checks.

`runtime-contract.json` defines when Project Elementor may use this repository and the maximum evidence claim. `runtime-versions.json` pins the reproducible runtime.

## Evidence boundary

A green run is **controlled_runtime** evidence. It can prove the pinned disposable runtime, official Library import, Elementor reopen/save/re-export roundtrip, registered widget/design-system availability, and configured browser checks. It does not prove customer staging/production, unknown site IDs/dynamic data, manual accessibility compliance, or pixel equality to a reference that was never supplied.

## Pipeline

1. Validate contract/version pins, `package-lock.json`, npm audit and Python unit tests.
2. Audit every `templates/*.json` for wrapper/tree/IDs/editor family/widgets/controls/responsive settings/repeaters/Atomic shapes/globals/classes.
3. Start pinned WordPress/PHP through wp-env.
4. Install pinned Elementor Core + Hello; optionally install an explicitly pinned Pro version.
5. Export registered widgets, controls, active breakpoints, classic Kit globals and Atomic global classes.
6. Audit against runtime and optional sanitized `target/inventory.json`.
7. Run Elementor's official `library import`, reopen/save the imported Library document, re-export it and compare semantically. Only Elementor element IDs are treated as volatile.
8. Render the roundtripped JSON into an isolated Canvas page.
9. Run Chromium, Firefox and WebKit across desktop/tablet/mobile plus active custom breakpoint widths; fail browser/console/network/overflow/serious automated WCAG issues and compare reviewed screenshots.
10. Upload evidence artifacts and tear down the runtime.

## Pinned runtime

See `runtime-versions.json`. CI fails if the observed WordPress, PHP, Elementor Core or Hello versions drift from those pins. Node dependencies are exact and locked with `package-lock.json`; CI uses `npm ci` and `npm audit --audit-level=high`.

## Elementor Pro

Pro is never committed. Configure both:

- GitHub Actions secret `ELEMENTOR_PRO_LICENSE_KEY`;
- repository variable `ELEMENTOR_PRO_VERSION` containing the exact allowed Pro package version.

If a license secret exists without a version pin, CI fails closed. Without the secret, CI runs in Free mode and records that state in `elementor-pro-status.json`.

## Public-repository privacy

Never commit credentials, license keys, personal data, client-confidential JSON, private screenshots, private URLs, Composer auth files, or an unsanitized target inventory. Use a private runtime/repository for confidential client artifacts.

## Target inventory

On a controlled target/runtime with the helper plugin active:

```bash
wp ejl inventory --output=/tmp/inventory.json
```

Only a sanitized inventory may be committed as `target/inventory.json` here. Inventory proves availability/configuration evidence for the scanned installation; it does not prove staging render equality.

## Local commands

```bash
npm ci
npm audit --audit-level=high
python -m unittest discover -s tests -p 'test_*.py' -v
python tools/audit_elementor_json.py templates/example.json
python tools/audit_elementor_json.py templates/example.json --inventory target/inventory.json
python tools/compare_elementor_roundtrip.py templates/example.json artifacts/roundtrip-json/example.json
npm run test:visual
```

Inside the WordPress runtime:

```bash
wp ejl inventory --output=/tmp/inventory.json
wp ejl import-roundtrip /path/to/template.json --output=/tmp/roundtrip.json
wp ejl render /tmp/roundtrip.json --slug=preview
```

`wp ejl render` remains a frontend harness and is not itself import proof; `import-roundtrip` invokes Elementor's official Library Import command first.

## Repository security

See `SECURITY.md`. The repository source includes SHA-pinned Actions and Dependabot configuration. Branch/ruleset, secret-scanning and account-level security controls must also be enabled in GitHub repository settings; source code cannot substitute for those controls.
