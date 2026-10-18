# Elementor JSON Lab — agentcontract

## Rol en bron
- `elementor` beslist over JSON, V3/V4/Atomic/mixed, dependencies en Visual Target; `webactueel-workflow` regelt multi-ownerwerk, bronwrites en closure.
- Deze repo is uitsluitend een controlled-runtime harness, **geen** live WordPress-bridge, projectbron, controller of deployroute.
- Lees `runtime-contract.json` en `toolkit-contract.json`; bij handoffs, bewijs of privacy ook `docs/project-elementor-integration.md`. Gebruik de repo alleen voor noodzakelijk runtimebewijs.

## Veilig wijzigen
- Start met target, versies, widget-/add-on-inventaris en terugvalroute. Bewaar V3/V4-familie; migratie vereist expliciete opdracht én tests.
- Maak vóór visuele reparatie één whole-page Visual Target met provenance (`explicit|declared|inferred|unknown`); `source_prediction` is nooit renderbewijs. Actualiseer na materiële JSON-wijziging. Vergelijk met echte screenshot en DOM `layout_snapshot`.
- Verzin geen IDs, media, menu's, forms, dynamic tags, queries, loops of add-ons. Houd secrets, klantdata, screenshots en runinputs buiten `main` en alleen tijdelijk/run-scoped.
- Voor live WordPress-mutaties: alleen geautoriseerde `wordpressconnector`-route met preflight, backup/rollback en site-readback.

## Runtime en bewijs
- Test importer/roundtrip, render, desktop/tablet/mobile en actieve breakpoints; controleer Pro, add-ons, media-identiteit en native Kit-gedrag alleen in exact passende runtime.
- V4 Classes/Variables gebruiken de native `import-export-customization`-component via deze bridge; V3 CLI-export is geen V4-bewijs.
- Test: `python -m unittest discover -s tests -p 'test_*.py' -v`. Run ook `Page Composition Contract`, `Elementor JSON QA` en bij Kit/V4 `Native Elementor Kit Contract`.
- Houd contracts, code, tests, docs en workflows synchroon. Unknown JSON, ontbrekende dependency of mislukte import/render/roundtrip => blokkeren.
- Groene Actions bewijzen alleen controlled runtime, nooit staging of productie. Voor staging/releasehandoff: na de laatste wijziging twee stabiele groene controlled-runtime-eindrondes en passende live QA.
