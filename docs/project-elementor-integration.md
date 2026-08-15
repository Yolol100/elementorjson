# Project Elementor integration

This repository is the Project Elementor `controlled_runtime` for source validation, official Elementor Template Library import, semantic importer roundtrip, runtime widget/dependency inspection, disposable rendering and cross-browser responsive evidence.

## Trigger

Use it when new or screenshot-reconstructed Elementor JSON needs importer/runtime/visual evidence; existing JSON changes structure, widgets, Atomic data, responsive behavior or dependencies; the user asks to test, scan, import, roundtrip, render, preview, screenshot, verify widgets or verify Pro; or a source-only result is about to receive a stronger runtime/importer/browser claim.

Skip it only for source-only explanation/planning without such a claim.

## Ownership and preflight

The Elementor skill remains domain owner. `webactueel-workflow` controls multi-owner/source-write/formal scan-fix-retest work. This repository is a capability, not an owner.

Before execution:

1. Classify artifact, editor family, dependency mode, target objects and risk.
2. Keep unknown IDs, Dynamic Tags, Forms, Loops, queries, conditions, globals and add-on data unknown.
3. Sanitize all inputs because the repository is public; confidential data requires a private runtime.
4. Use `target/inventory.json` only when it is controlled and safe for public storage.
5. Use `ELEMENTOR_PRO_LICENSE_KEY` only as an Actions secret when Pro coverage is required.

## Controlled-runtime chain

The main workflow must:

1. validate the runtime contract and unit tests;
2. validate Classic/widget structure plus deep Atomic typed props/styles/repeater structure;
3. use the committed npm lockfile via `npm ci` and block high/critical npm audit findings;
4. start the pinned WordPress/PHP runtime and pinned Elementor Core/Hello versions;
5. optionally install Pro from Elementor's official Composer repository;
6. export and verify the actual runtime widget/control inventory;
7. audit source JSON against runtime and optional sanitized target inventory;
8. import as the wp-env administrator through Elementor's Template Library CLI;
9. export importer storage and compare `content`/`page_settings` semantically, ignoring only proven importer-volatility/defaults;
10. re-audit importer output and render the importer-produced JSON;
11. run Chromium, Firefox and WebKit at desktop/tablet/mobile plus active breakpoint boundaries with reduced-motion/error/request/image/overflow/basic keyboard checks;
12. upload all evidence and tear down the disposable runtime.

Source JSON remains stricter than importer storage. In particular, Atomic source elements require boolean `isInner`; the comparator/imported-output validator may accept only the proven importer omission equivalent to `isInner: false`. Explicit `true`, invalid types and site-bound references remain significant.

## Readback and iteration

Require both `Static JSON audit` and `Elementor runtime preview` to succeed. Inspect dependency audit, runtime inventory, source/runtime/deep audits, importer roundtrip output, imported JSON, render manifests, Pro mode and browser artifacts. Repair only confirmed defects and rerun the same chain.

After the last implementation change, require two stable green final controlled-runtime rounds before a staging/release handoff.

## Evidence boundary

A green run may support only the covered `controlled_runtime` claims. It does not prove exact customer staging compatibility, `target_verified`, production behavior, editor UI reopen/save/re-export, site-specific IDs/globals/conditions/dynamic data, Pro when no Pro secret was present, pixel-perfect equality without an approved reference, or full accessibility/assistive-technology compliance.

Target/staging/live proof remains a separate `website-qa-checklist` gate. Custom WordPress code/integrations remain `wordpressqualityarchitect` scope.

## Failure behavior

Fail closed on invalid runtime contract, dependency audit failure, malformed Classic/Atomic source, unavailable widget, importer permission/import failure, semantic roundtrip drift outside the proven normalization set, importer-output audit failure, render failure or browser failure. Do not weaken source validation merely to accommodate importer storage normalization.

## Privacy and secrets

Never commit Elementor Pro keys, Composer auth, credentials, personal data, confidential client JSON/screenshots, private download URLs or confidential target inventories. Use Actions secrets for Pro credentials and a private runtime/repository for sensitive artifacts.

`runtime-contract.json` is the canonical machine-readable form of this policy. If this document, README and that contract drift, repair the drift before making controlled-runtime claims.
