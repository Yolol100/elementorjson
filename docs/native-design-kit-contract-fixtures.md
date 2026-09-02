# Native Elementor Design Kit contract fixtures

This document describes a **controlled-runtime evidence workflow**. It does not turn this repository into the product Design Kit generator and it does not authorize target-site mutation.

## Purpose

`Native Elementor Contract Fixtures` uses the pinned disposable WordPress/Elementor runtime to observe current native import/export structures instead of guessing private Elementor JSON or ZIP formats.

Baseline for this contract set:

- WordPress 7.1
- PHP 8.3.x
- Elementor Core 4.2.4
- Hello Elementor 3.5.1
- Elementor Website Template format emitted by `import-export-customization`

The workflow is version-bound. A later Elementor version requires a fresh run before its structures are treated as compiler evidence.

## Generated Website Template contracts

The workflow creates three sanitized native ZIPs by calling Elementor's current `import-export-customization` component itself:

1. `v3.zip` — V3 Site Settings/Globals/Theme Style/Layout evidence without V4 Classes or Variables.
2. `v4.zip` — V4 Design System evidence containing a valid Global Class plus current color, font and size Variables.
3. `mixed.zip` — the same portable V3 design-system settings together with the V4 Class and Variables.

Each profile is imported again into an isolated blank Kit. The validator compares the resulting semantic state with the pre-export state. It allows only explicitly documented native canonicalization, such as Elementor expanding `space_between_widgets` from a compact size value to its equivalent `column`/`row`/`isLinked` representation.

For V4/mixed, the ZIP must contain both `global-classes/` and `global-variables.json`, and the post-import state must still contain the expected Class and all three current Variable families used by this canary.

## Native media-control contracts

The workflow creates three disposable WordPress image attachments on the same runtime and then saves/exports minimal templates through Elementor's **local Template Library**. This preserves the real same-site attachment identity long enough to observe the native control structures:

- `media-observed/image-control.json` — classic Image widget with a positive attachment `id` and matching `url`.
- `media-observed/background-control.json` — Container `background_image` with a positive attachment `id` and matching `url`.
- `media-observed/gallery-control.json` — Basic Gallery (`image-gallery`) using `wp_gallery` with three positive attachment IDs/URLs and native `thumbnail_size`.

These IDs are disposable runtime facts, not portable IDs for another WordPress installation.

## Why media is not tested through portable re-import

A portable Template Library import may intentionally remap, download or clear site-bound media identity. Therefore a portable import/re-export cannot prove the exact target attachment ID contract. The media fixture is intentionally **same-site save -> native local-template export**. Target-site use still requires the Elementor JSON Bridge to revalidate every chosen WordPress attachment ID + URL before apply.

## Artifact

A successful run uploads `native-elementor-contracts` containing at least:

- `v3.zip`, `v4.zip`, `mixed.zip`;
- `expected-v3.json`, `expected-v4.json`, `expected-mixed.json`;
- `roundtrip-v3.json`, `roundtrip-v4.json`, `roundtrip-mixed.json`;
- the three `media-observed/*.json` contracts;
- `validation-report.json` with `status=pass`.

The ZIPs are native Elementor evidence produced by the pinned runtime. They are **compiler fixtures**, not a reusable client Design Kit and not target-site content.

## Consumer rule

A Design Kit compiler may use these structures only when all of the following are true:

1. the target/export family and Elementor version are compatible with the observed contract;
2. the relevant `Native Elementor Contract Fixtures` run is green;
3. the compiler maps only fields with an observed native contract;
4. unsupported, plan-bound, Pro-only, add-on or target-bound data remains blocked or requires target evidence;
5. generated packages still pass native import and semantic roundtrip before any stronger claim.

`elementorjson` remains the controlled-runtime/test harness. Product generation belongs to the registered generator owner when that repository exists.

## Evidence boundary

This workflow can prove native Elementor 4.2.4 contract shapes and semantic roundtrip inside the disposable controlled runtime. It does not prove target-site compatibility, Elementor Pro behavior when Pro is absent, customer media identity, production import safety, visual quality or live behavior.
