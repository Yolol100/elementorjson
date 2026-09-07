# WordPress admin Elementor JSON import/export contract

`elementorjson` remains the controlled QA/validation lab. The live WordPress admin UI is implemented once, in `Yolol100/wordpressconnector`, so there is no second production bridge.

The canonical admin behavior is:

- Pages and Posts built with Elementor show **Export Elementor JSON** as a per-item row action.
- Pages, Posts and Saved Templates show **Import Elementor JSON** as a per-item row action; Pages, Posts and Saved Templates also expose an import screen for create-new or replace-existing flows.
- The WordPress bulk-action dropdown exposes **Export Elementor JSON (ZIP)** for Pages, Posts and Saved Templates. Selected exportable Elementor items are written as separate `.json` files in one ZIP. Non-Elementor or unauthorized selections are skipped and recorded in `manifest.json`.
- Bulk export is bounded to 100 selected items per request.
- When Elementor Pro Theme Builder is available, Pages and Posts also expose **Export Elementor + Site Parts**. The connector bundle can contain the source document plus the matching header/footer and source metadata.
- Saved Templates keep Elementor's native export action; WordPress Connector supplies a fallback only when the native action is absent.
- Import can replace the Elementor structure/page settings of an explicitly selected existing item or create a new draft from the uploaded JSON.
- Import does not replace unrelated WordPress post fields and uses the WordPress Connector `ElementorAdapter` create/save/readback/rollback paths rather than direct `_elementor_data` writes.
- Accepted portable document fields include `content`, `page_settings` (or legacy `settings`), `version`, `title`, `type`, `global_classes` and `global_variables`.
- The connector site-parts bundle uses `wordpressconnector/elementor-site-parts-bundle`; Page/Post import consumes its `document` payload and does not silently overwrite Theme Builder assignments.
- Uploaded JSON is limited to 5 MB and must contain a non-empty `content` array.

`wordpressconnector` also supports deterministic `expected_fingerprint` and site-scoped HMAC `expected_state_token` guards for REST mutations. Those transport/runtime guards belong to WordPress Connector, not to this QA repository.

This repository may validate the JSON contract and disposable import/roundtrip/render behavior, but must not become a second live WordPress deployment bridge.
