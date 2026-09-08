# Elementor JSON Lab

> **Status:** actief ondersteunend · private controlled Elementor QA-runtime

Elementor JSON Lab levert reproduceerbaar bewijs voor Elementor JSON. De `elementor` Skill blijft eigenaar van structuur, ontwerpbeslissingen en compatibiliteitsinterpretatie; `webactueel-workflow` blijft de controller. Deze repository is geen productie-deployer en geen live WordPress-bridge.

## Eén taak

```text
veilige Elementor JSON
→ optionele snelle WordPress Playground-baseline
→ bronvalidatie en Visual Target
→ disposable wp-env WordPress/Elementor import
→ roundtrip, render en browserchecks
→ run-scoped evidence
```

## Wat de runtime bewijst

- Een aparte WordPress Playground-smoke kan snel bewijzen dat de gepinde, al in `package-lock.json` aanwezige CLI een schone WordPress 7.1/PHP 8.3-baseline start en dat homepage + REST reageren. Dit is **geen** Elementor-import- of renderbewijs.
- Classic/V3, V4/Atomic en mixed JSON-validatie binnen het actuele runtimecontract.
- Whole-page Visual Target met provenance: `explicit`, `declared`, `inferred` of `unknown`.
- Import en semantische roundtrip in de diepere gepinde wp-env WordPress/Elementor-omgeving.
- Desktop-, tablet-, mobile- en breakpoint-renders met screenshots en DOM-layoutmetadata.
- Widget/control inventory, dependencychecks en optionele Elementor Pro-detectie.
- Native V3/V4/mixed Website Template/Design System-contracten via Elementors eigen runtimecomponenten.
- Same-site media `id + url` readback voor ondersteunde controls.

De exacte versies, features, workflows en bewijsgrenzen staan in `runtime-contract.json` en `toolkit-contract.json`. Die contracten zijn leidend; README-versies zijn niet normatief.

## Gebruik deze repository wanneer

- broninspectie niet genoeg is;
- een snelle accountloze schone WordPress/PHP-baseline nuttig is vóór diepere Elementor-validatie;
- importer/roundtrip-, render-, responsive- of browserbewijs nodig is;
- een reproduceerbaar native Kit/Design-System-contract nodig is;
- een lokale Codex-runtime niet aantoonbaar dezelfde evidence-class levert.

Gebruik hem niet voor:

- productie- of live-site-mutaties;
- het verzinnen van site-, media-, form-, Loop-, query- of Dynamic Tag-ID's;
- vertrouwelijke klantdata zonder taakgebonden private runtimebeleid;
- een source-only taak waarvoor geen runtimeclaim nodig is.

## Bewijsgrenzen

- Een groene Playground-smoke bewijst alleen de vastgelegde schone WordPress/PHP-baseline; wp-env/MySQL blijft nodig voor Elementor-import, widgets, roundtrip en renderclaims.
- Een Visual Target is `source_prediction`, geen screenshotbewijs.
- Een groene gecontroleerde run is geen target-, staging- of productiebewijs.
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

Voor de snelle baseline moet `WordPress Playground Smoke` groen zijn. Voor Elementor runtime-, render-, Visual Target- of native Kit-wijzigingen moeten daarnaast de relevante diepere GitHub Actions-workflows slagen. Zie `AGENTS.md` voor de exacte change- en releasegates.

## Licentie

Deze repository bevat momenteel geen open-sourcelicentie. Hergebruik, distributie of afgeleide werken zijn niet toegestaan zonder expliciete toestemming van de rechthebbende.
