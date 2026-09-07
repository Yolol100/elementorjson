# WordPress admin Elementor JSON import/export contract

`elementorjson` remains the controlled QA/validation lab. The live WordPress admin UI is implemented once, in `Yolol100/wordpressconnector`, so there is no second production bridge.

The canonical admin behavior is:

- Pages and Posts built with Elementor show a row action **Export Elementor JSON**.
- Saved Templates keep Elementor's native export action; WordPress Connector supplies a fallback only when the native action is absent.
- Pages, Posts and Saved Templates show **Import Elementor JSON** for users who can edit the target item.
- Import replaces only the target Elementor document structure/page settings and forces Elementor edit mode; it does not replace unrelated WordPress post fields.
- Import uses the WordPress Connector `ElementorAdapter` document-save/readback/rollback path rather than direct `_elementor_data` writes.
- Accepted portable document fields are `content`, `page_settings` (or legacy `settings`), `version`, `title`, and `type`.
- The uploaded JSON is limited to 5 MB and must contain a non-empty `content` array.

This repository may validate the JSON contract and disposable import/roundtrip behavior, but must not become a second live WordPress deployment bridge.
