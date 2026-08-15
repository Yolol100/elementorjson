# Templates

Place only sanitized Elementor export JSON files directly in this directory.

Examples:

- `homepage.json`
- `landing-page.json`
- `contact.json`

Each `.json` file is source-audited, checked against the pinned runtime widget inventory, imported through Elementor's official Template Library CLI, semantically compared after import readback, rendered into a separate temporary Elementor Canvas page and tested in Chromium, Firefox and WebKit at desktop/tablet/mobile plus discovered extra Elementor breakpoints.

Visual screenshots are compared with committed baselines under `tests/e2e/preview.spec.js-snapshots/`.

Template filenames must map to unique non-empty slugs. Never place confidential client JSON, credentials, private URLs or unsanitized site-bound data in this public repository.
