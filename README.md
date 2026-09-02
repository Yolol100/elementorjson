# Elementor JSON Lab

> **Portfoliostatus:** Actief ondersteunend · publieke gecontroleerde Elementor QA-runtime

**Rol in het platform:** Elementor JSON Lab valideert en test niet-gevoelige Elementor JSON in een publieke gecontroleerde runtime. Project Elementor + de `elementor` Skill blijven eigenaar van ontwerp- en JSON-beslissingen; deze repository levert reproduceerbare source-prediction/import/runtime/browser-evidence. Commit hier nooit vertrouwelijke klant-JSON, privé-screenshots, credentials of persoonsgegevens.

## Wat de runtime nu doet

De QA-keten bestaat uit drie gekoppelde bewijsstromen:

1. **Whole-page Visual Target** — `tools/build_visual_target.py` leest de volledige Elementor JSON en maakt `artifacts/visual-targets/<template>.json`. Elke voorspelde eigenschap blijft gelabeld als `explicit`, `declared`, `inferred` of `unknown`. `evidence_class=source_prediction` en `render_observed=false` zijn harde grenzen: het model is een voorspelling, geen screenshot.
2. **Echte controlled-runtime render** — Elementor importeert de template via de officiële Template Library CLI in een wegwerp-WordPressomgeving. Playwright rendert Chromium, Firefox en WebKit op desktop/tablet/mobile plus actieve breakpointgrenzen, maakt full-page screenshots en bewaart per screenshot een `layout_snapshot` met bounding boxes en computed layout/style data.
3. **Native Website Template/Design System contract** — `.github/workflows/native-kit-contract.yml` gebruikt de gepinde Elementor-runtime om V3, V4 en mixed packagegedrag te bewijzen. De repo behoudt de gedocumenteerde `wp elementor kit export`-route als V3-contract en heeft daarnaast een generieke `ejl native_kit_export` / `ejl native_kit_import` bridge naar Elementors eigen `import-export-customization` component. Daarmee kunnen de in die exacte runtime geregistreerde native runners voor onder andere Global Classes en Variables worden getest zonder een eigen ZIP-formaat te verzinnen. Dezelfde workflow bewijst same-site WordPress media `id + url` readback voor Image, Background en Basic Gallery.

De assistant vergelijkt daarna het whole-page model met renderbewijs, herstelt alleen bevestigde afwijkingen en bouwt het model na een materiële patch opnieuw.

## Huidige QA-keten

1. Valideer `runtime-contract.json`, `toolkit-contract.json` en contracts.
2. Bouw het whole-page Visual Target en valideer Classic/Atomic JSON.
3. Audit optionele `*.design-intent.json` en `*.content-contract.json` sidecars.
4. Run alle Python regressietests.
5. Installeer de locked npm-tooling en blokkeer high/critical `npm audit` findings.
6. Start WordPress **7.1** / PHP **8.3** via wp-env.
7. Installeer Elementor Core **4.2.4** en Hello Elementor **3.5.1**.
8. Installeer Elementor Pro alleen wanneer de bestaande `ELEMENTOR_PRO_LICENSE_KEY` Actions-secret beschikbaar is; de exacte geïnstalleerde Pro-versie is run-specifiek bewijs.
9. Exporteer runtime widget/control inventory en verifieer de versies.
10. Importeer iedere template via `wp --user=admin elementor library import`.
11. Vergelijk importer storage semantisch met de source en heraudit imported JSON.
12. Render naar geïsoleerde Elementor Canvas-pagina's.
13. Test browsers/breakpoints op HTTP-, console-, request-, image-, overflow- en focusfouten.
14. Schrijf screenshot + DOM-layoutmetadata weg en upload evidence artifacts.
15. Wanneer native Kit/Design-Systembewijs nodig is: activeer de benodigde Elementor-features vóór boot, exporteer/importeer via de runtime-eigen customization component, controleer V4 Classes/Variables en package readback, en houd portable media-migratie apart van same-site ID-behoud.
16. Vereis na de laatste implementatiewijziging twee stabiele groene controlled-runtime rondes vóór staging/release-handoff.

## Repository layout

```text
.github/workflows/validate.yml               Pinned runtime/import/render QA
.github/workflows/composition-contract.yml   Composition + Visual Target QA
.github/workflows/native-kit-contract.yml    Native V3/V4/mixed Kit + media contract
.wp-env.json                                 Pinned disposable WordPress/PHP
runtime-contract.json                        Machine-readable evidence boundary
toolkit-contract.json                        Tool/capability contract
contracts/visual-target.schema.json          Visual Target prediction schema
contracts/design-intent.schema.json          Optional design intent
contracts/content-contract.schema.json       Optional content constraints
tools/build_visual_target.py                 JSON -> whole-page Visual Target
tools/audit_page_composition.py              Composition/layout-risk lint
tools/audit_elementor_json.py                Classic/widget/dependency audit
tools/validate_elementor_deep.py             Deep Classic/Atomic validation
tools/compare_elementor_roundtrip.py         Import semantic comparison
tests/e2e/preview.spec.js                    Screenshots + DOM layout snapshots
wordpress-plugin/elementor-json-lab/         Runtime inventory/export/render/native-kit CLI helper
```

## Gebruik en grenzen

Gebruik deze repo wanneer JSON meer nodig heeft dan broninspectie: visual modelling, importer/roundtrip, widget/dependency, render, responsive, browserbewijs of een reproduceerbaar native Website Template/Design System-contract. Een source-only taak mag zonder runtime sluiten wanneer geen sterkere claim nodig is.

Een green Visual Target bewijst alleen een consistente bronvoorspelling. Een green runtime bewijst alleen de gepinde controlled runtime. Native Kit-success bewijst alleen het gedrag van de exact gepinde Elementor-versie en de tijdens die run actieve features; het maakt geen targetsite automatisch compatibel. Geen van deze routes bewijst op zichzelf customer staging, `target_verified`, productie, site-specifieke IDs/globals/dynamic data, pixel-perfect gelijkheid zonder goedgekeurde referentie of volledige accessibility/assistive-technology compliance. Daarvoor blijft staging/Website QA nodig.

Portable Elementor-import kan media migreren en nieuwe attachment-ID's maken. Same-site hergebruik van bestaande media moet daarentegen het bestaande WordPress `id + url` paar behouden en live valideren.

## Privacy

De repository is publiek. Gebruik alleen gesaniteerde fixtures. Vertrouwelijke JSON, screenshots, inventories, tokens, licenties en klantdata horen in een private runtime of exacte site-route. `ELEMENTOR_PRO_LICENSE_KEY` mag uitsluitend als GitHub Actions secret bestaan.

## Licentie

Deze repository bevat momenteel geen open-sourcelicentie. Hergebruik, distributie of afgeleide werken zijn niet toegestaan zonder expliciete toestemming van de rechthebbende.
