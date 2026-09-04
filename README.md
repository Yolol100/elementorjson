# Elementor JSON Lab

> **Status:** actief ondersteunend · private controlled Elementor QA-runtime

Elementor JSON Lab levert reproduceerbaar bewijs voor Elementor JSON. De `elementor` Skill blijft eigenaar van structuur, ontwerpbeslissingen en compatibiliteitsinterpretatie; `webactueel-workflow` blijft de controller. Deze repository is geen productie-deployer en geen live WordPress-bridge.

## Eén taak

```text
veilige Elementor JSON
→ bronvalidatie en Visual Target
→ disposable WordPress/Elementor import
→ roundtrip, render en browserchecks
→ run-scoped evidence
```

## Wat de runtime bewijst

- Classic/V3, V4/Atomic en mixed JSON-validatie binnen het actuele runtimecontract.
- Whole-page Visual Target met provenance: `explicit`, `declared`, `inferred` of `unknown`.
- Import en semantische roundtrip in een gepinde wegwerp-WordPressomgeving.
- Desktop-, tablet-, mobile- en breakpoint-renders met screenshots en DOM-layoutmetadata.
- Widget/control inventory, dependencychecks en optionele Elementor Pro-detectie.
- Native V3/V4/mixed Website Template/Design System-contracten via Elementors eigen runtimecomponenten.
- Same-site media `id + url` readback voor ondersteunde controls.

De exacte versies, features en bewijsgrenzen staan in `runtime-contract.json` en `toolkit-contract.json`. Die contracten zijn leidend; README-versies zijn niet normatief.

## Gebruik deze repository wanneer

- broninspectie niet genoeg is;
- importer/roundtrip-, render-, responsive- of browserbewijs nodig is;
- een reproduceerbaar native Kit/Design-System-contract nodig is;
- een lokale Codex-runtime niet aantoonbaar dezelfde evidence-class levert.

Gebruik hem niet voor:

- productie- of live-site-mutaties;
- het verzinnen van site-, media-, form-, Loop-, query- of Dynamic Tag-ID's;
- vertrouwelijke klantdata zonder taakgebonden private runtimebeleid;
- een source-only taak waarvoor geen runtimeclaim nodig is.

## Bewijsgrenzen

- Een Visual Target is `source_prediction`, geen screenshotbewijs.
- Een groene run is `controlled_runtime`, geen target-, staging- of productiebewijs.
- Native Kit-success geldt alleen voor de exact vastgelegde Elementor-versie en featurestates.
- Targetcompatibiliteit, pixel-fidelity, echte content/dynamic data en volledige accessibility blijven aparte staging-/Website-QA-poorten.
- Portable imports kunnen nieuwe media-ID's maken; same-site hergebruik moet het bestaande `id + url`-paar live behouden en valideren.

## Privacy en veiligheid

De repository is private, maar private opslag verlaagt de veiligheidsgrenzen niet.

- Commit nooit wachtwoorden, tokens, licentiesleutels, Composer-auth of persoonsgegevens.
- Gebruik GitHub Actions Secrets voor `ELEMENTOR_PRO_LICENSE_KEY` en andere toegestane credentials.
- Bewaar klant-JSON, screenshots en inventories alleen wanneer ze noodzakelijk, taakgebonden en volgens het projectbeleid toegestaan zijn.
- Plaats projectwaarheid niet permanent op `main`; gebruik tijdelijke runtime-input en run-scoped artifacts.

## Verificatie

Voor Python-/JSON-logica:

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

Voor runtime-, render-, Visual Target- of native Kit-wijzigingen moeten de relevante GitHub Actions-workflows slagen. Zie `AGENTS.md` voor de exacte change- en releasegates.

## Licentie

Deze repository bevat momenteel geen open-sourcelicentie. Hergebruik, distributie of afgeleide werken zijn niet toegestaan zonder expliciete toestemming van de rechthebbende.
