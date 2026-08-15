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
7. Discover a real administrator in the disposable runtime, snapshot Library IDs, run Elementor's official `wp elementor library import` directly as that administrator, identify the one newly imported Library document, reopen/save it through Elementor, re-export it and compare semantically. Only Elementor element IDs are treated as volatile.
8. Render the roundtripped JSON into an isolated Canvas page.
9. Run Chromium, Firefox and WebKit across desktop/tablet/mobile plus active custom breakpoint widths; fail browser/console/network/overflow/serious automated WCAG issues and compare reviewed screenshots when an approved baseline exists.
10. Upload evidence artifacts and tear down the runtime.

## Pinned runtime

See `runtime-versions.json`. CI fails if the observed WordPress, PHP, Elementor Core or Hello versions drift from those pins. Node dependencies are exact and locked with `package-lock.json`; CI uses `npm ci` and `npm audit --audit-level=high`. The lockfile also forces the patched `adm-zip` 0.6.0 release so the known pre-0.6.0 ZIP memory-allocation vulnerability cannot re-enter through the pinned wp-env dependency tree.

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

Inside a disposable WordPress runtime the official import flow is:

```bash
wp ejl runtime_context --output=/tmp/context.json
wp ejl library_ids --output=/tmp/before.json
wp --user=<administrator-id-from-context> elementor library import /path/to/template.json --returnType=ids
wp ejl library_ids --output=/tmp/after.json
wp ejl roundtrip <new-library-id-from-before-after-diff> --output=/tmp/roundtrip.json
wp ejl render /tmp/roundtrip.json --slug=preview
```

CI discovers both IDs; nothing is hardcoded. `wp ejl render` remains a frontend harness and is not itself import proof.

## Repository security

See `SECURITY.md`. The repository source includes SHA-pinned Actions and Dependabot configuration. Branch/ruleset, secret-scanning and account-level security controls must also be enabled in GitHub repository settings; source code cannot substitute for those controls.
