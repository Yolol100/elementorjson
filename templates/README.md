# Templates

Place only importable Elementor export JSON files directly in this directory.

Examples:

- `homepage.json`
- `landing-page.json`
- `contact.json`

Do not place design-intent or content-contract sidecars in `templates/`; the runtime workflow treats template JSON as importable Elementor documents. Put optional sidecars in `sidecars/` with the same template stem, for example `sidecars/homepage.design-intent.json` and `sidecars/homepage.content-contract.json`.

Each template is audited and, when compatible with the CI runtime, rendered into a temporary WordPress page for desktop, tablet and mobile screenshots. The separate `Page Composition Contract` workflow runs source-level composition/layout/proof/content lint and automatically attaches matching sidecars.
