# Native migration preflight (candidate)

Phase 1 inventory and phase 2 conservative candidate generation only. This is a source-prediction tool, not a site migration engine, import API, visual proof, theme generator or controller. It does not modify Elementor or WordPress. The existing Elementor controlled runtime and WordPress theme/staging acceptance stay authoritative.

Local CLI: python tools/plan_native_migration.py <private-export.json>
Optional: --output <new file in private directory outside checkout> --confirm-private-output

Use a real export privately, never upload to this public repository. On Windows the owner must verify the directory ACL before confirming. The CLI refuses CI usage. Only the synthetic unit fixtures execute in public CI. Source content, element IDs and mapping are never printed. Output is a private JSON containing native block candidate markup and source-to-block mapping.

Initial allowlist: classic 0.4 page envelope, plain explicit h1-h6 headings, plain text-editor paragraphs, and empty-settings layout nodes mapped to core Group. This intentionally does not infer layout defaults, classes, responsive styles, fonts, globals, media, ACF, links, dynamic tags, loops, forms, WooCommerce, shortcode, raw rich text or V4/Atomic. Unknown fields/settings or unsupported widgets block the entire candidate rather than dropping content. Supported content is not a promise that default Group layout matches Elementor.

Five-phase safe handoff:
1. Inventory all posts/pages/projects, URL/slug/ID, templates/conditions, content, media, ACF/SEO, dynamic dependencies, editor/version, complete private backup and current screenshots/DOM.
2. Produce per-item candidate or explicit manual mapping and separately approved improvement plan. Never auto-rewrite unknown content or IDs.
3. Before staging import verify core block parse/serialization, native editor save/reopen, theme/dependency baseline and rollback. Preserve URLs, content, media, custom fields, forms and redirects. Do not publish a partial candidate.
4. Authorized isolated staging only, with reversible import and exact target readback. Keep original Elementor until validated; use existing WordPress/hosting owners.
5. Compare same viewport/device/font/load state baseline and candidate screenshots/DOM, approved tolerances and exact content/metadata/behavior. No unapproved visual/content differences; check keyboard, forms, links, SEO and relevant Woo flows. Website QA verifies independently. Two stable green controlled-runtime rounds for affected Elementor scope and real target/host rollback before release.

Candidate generation is never staging or production acceptance. Use existing theme/scripts/validate_staging_acceptance.py for that repository's theme receipt, not a second release authority.

Reference: https://developer.wordpress.org/block-editor/getting-started/fundamentals/markup-representation-block/
