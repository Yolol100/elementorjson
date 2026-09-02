# Section widget capability and safe repair

This controlled runtime does not use one static Elementor/Elementor Pro widget list as execution truth. It exports the capabilities actually registered by the exact runtime and uses that inventory as availability evidence.

## Version-bound inventory

For each run, bind the Elementor Core version, Elementor Pro version when loaded, active plugins, active devices/breakpoints, registered widgets, registered layout/Atomic elements, registered document/template types and registered Dynamic Tags. For widgets/elements/tags record ownership/plugin slug, categories and exposed controls when safely available. The classic Form widget may expose registered `submit_actions` choice keys; treat them as availability evidence only and still test delivery/integrations on staging.

Release history and documentation can explain drift, but they do not prove that a widget, element, document type, tag or control exists in the current runtime. Classic widgets expose controls that can be checked against the generated inventory. Atomic/V4 typed props/styles remain on their dedicated typed validation path rather than being treated as Classic controls.

When a previous trusted target/runtime inventory exists, compare it with the new inventory using `tools/compare_runtime_capabilities.py`. Treat removed capabilities, changed capability records/controls or removed plugins as `review_required`; additions and version changes are drift evidence that must be re-evaluated before reuse. This is the automatic change detector for installed Elementor, Pro and add-on capability surfaces; it complements, rather than replaces, current vendor/release research.

## Object-context routing

Classify the Elementor object before selecting widgets/elements. Prefer an exact registered document type from `document_types`; the table below is a planning fallback when a target-specific type is not yet known.

| Object/context | Required planning roles | Typical native candidates when registered | Extra gates |
| --- | --- | --- | --- |
| Archive | archive context, title/description, dynamic listing, query/pagination, optional filters | Archive Title, Archive Posts, Loop Grid, taxonomy/dynamic widgets | Pro/Theme Builder, query source, display conditions |
| Single / Post / Page | content hierarchy, post/page title/content/media/meta as needed | Post Title, Post Content, Featured Image, Post Info, Author/Navigation, section widgets | exact post/document context; dynamic data proof |
| Single Product | product identity, gallery, title, price, stock, variations, add-to-cart, meta/upsells as needed | Woo product widgets/dynamic tags | WooCommerce, product context, cart/action tests |
| Product Archive / Shop | product archive context, listing, sorting/filtering/pagination | Archive/Loop/Product widgets, Woo filters when available | Woo query/archive context, filters and pagination |
| Cart / Checkout / My Account | transactional/account flow and presentation only | registered Woo cart/checkout/account widgets/elements | high risk; Woo owns data/transactions; staging/sandbox required |
| Section / Column / Inner Section | legacy V3 structural hierarchy, widths, alignment, gaps/spacing and responsive order | registered Section/Column/Inner Section plus minimal children | preserve legacy family during repair; no silent container migration |
| Container | layout parent, direction, width, alignment, gap, responsive behavior | Container and child widgets/elements | do not add content widgets unless intent requires them |
| Div block | Atomic structural wrapper | registered Atomic Div/Block plus typed children | V4/Atomic target evidence |
| Flexbox | Atomic/Flex structural layout | registered Flexbox plus typed children | V4 props, wrap/direction/breakpoints |
| Grid / Raster | grid structure, tracks, gaps, item placement, responsive transformation | registered Grid/Atomic Grid or supported container grid | V4 target evidence where Atomic; layout-math check |
| Classic Form | fields, labels, validation, submit and registered actions | Form widget plus its registered controls/actions | Pro, spam/privacy, delivery/integration tests |
| Atomic Form | form wrapper, fields, validation, submit, actions | registered Atomic Form elements | V4/Pro, actions, privacy, spam, delivery/integration tests |
| Atomic Loop | query, loop layout, repeated item/component | registered Atomic Loop/Loop Layout/Loop Item capabilities | Pro, query/data source, V4 proof, component dependency |
| Loop Item | dynamic item identity, image, title, metadata/excerpt/price/action | Featured Image, Post/Product Title, Excerpt, Post Info, Dynamic Tags, Button, Woo widgets | correct loop/query; no invented IDs |
| Component / Global Widget | reusable master plus instances/usage | registered Component/Global Widget capabilities | usage scan; master edits propagate; detach/unlink semantics |
| Error 404 | recovery message, navigation, search, optional relevant content | Heading, Text, Search, Button, Posts/Loop | 404 condition and real missing-URL test |
| Floating Element | concise message/action, optional icon/image/form, position/visibility/interaction | registered text/button/media/form capabilities | triggers/conditions, reduced motion, mobile obstruction |
| Footer | branding, navigation, legal/contact/social, optional search/newsletter | Site Logo, Menu, Text, Social Icons, Form/Search | Theme Builder conditions; global consistency |
| Header | branding, navigation, search, primary action, optional account/cart/social | Site Logo, Menu/Nav, Search, Button, Social, Woo cart/account | Theme Builder conditions; responsive menu behavior |
| Popup | focused message/CTA, optional form/countdown/media/navigation | Heading/Text/Button/Form/Countdown/Image/Video/Menu | triggers, close behavior, focus/keyboard, conditions |
| Search Results | search context, result listing, query/pagination, empty state/refinement | Search, Archive Title, Archive Posts/Loop Grid | Search Results condition; no-results test |
| Section intent inside any document | semantic section wrapper and only required content roles | smallest registered structural/content composition | preserve V3/V4 family and page rhythm |

The names above are role examples, not a static availability list. A candidate that is not registered in the exact runtime is unavailable.

## Per-section selection contract

The calling Elementor Skill translates object context plus section intent into a small candidate set. For each document, template, section or reusable component it must:

1. classify the exact registered document/object context first;
2. determine content, semantic role, functionality, dynamic data, layout, visual treatment, responsive behavior and accessibility needs;
3. prefer the smallest native Elementor Core/Pro composition that can satisfy those needs;
4. when native capability is insufficient or an installed site already depends on an add-on, include matching third-party widgets as secondary candidates;
5. intersect every widget/element/tag candidate with the exact runtime inventory;
6. reject any unregistered capability and verify required controls before writing settings;
7. record Pro/add-on/site-object dependencies and unresolved target assumptions;
8. keep unknown site-bound data unknown instead of inventing IDs or mappings.

The runtime inventory proves availability only. It does not prove that the choice is visually correct on a customer target.

## Popular add-on discovery policy

Do not maintain a permanent hardcoded list of popular add-on widgets as execution truth. Popularity and catalogs change.

When add-on awareness is relevant:

1. Use current WordPress.org adoption signals and the vendor's current widget catalog only as discovery/ranking evidence.
2. Prefer established Elementor add-on families with meaningful current adoption, but never infer that a target has them installed.
3. Read the exact target/runtime inventory and identify third-party widgets/elements/tags by owner/plugin slug.
4. Build secondary candidates from recurring capability families such as Mega/Nav Menu, Post Grid/List/Carousel, WooCommerce grids/carousels/filters, Search/AJAX Search, advanced filters, Accordion/Tabs, Pricing Table, Testimonial/Review, Team Member, Gallery/Media Grid, Info/Icon Box, Content Toggle, Modal/Offcanvas, Lottie/animation, tables/charts and form stylers.
5. Prefer Core/Pro when it satisfies the requirement with equal or lower dependency/risk. Prefer an installed add-on when it is already an established site dependency or supplies a required capability not available natively.
6. Never install or introduce an add-on solely because it is popular without an explicit dependency decision.
7. Verify exact controls/responsive/dynamic behavior from runtime/target evidence before use.

Current web research may name candidate add-on families, but those names belong to execution evidence for that run rather than this durable contract.

## Safe automatic correction

`tools/repair_elementor_json.py` applies only allowlisted, reversible source repairs and always writes to a separate output file. It never mutates the source artifact in place.

Current allowlist:

- `EJL-SAFE-001`: remove an empty/no-op Classic setting only when the exact runtime inventory proves that the control is unrecognized for that registered widget and the key is not private/special.

The repair tool deliberately blocks instead of guessing when a widget/element/tag is unavailable, an unknown setting is non-empty, Atomic/V4 typed evidence is missing, or a repair would change content, layout, typography, interactions, Dynamic Tags, Forms/actions, Loops, WooCommerce, Theme Builder placement, Components, globals/classes/variables, site-object IDs or add-on behavior without target proof.

Each applied repair records rule ID, affected path, before/after values and runtime version evidence. The report also records the source SHA-256 so rollback means restoring the exact source artifact.

## Verification loop

Use:

`object context -> runtime capabilities -> inventory drift check -> section intent -> candidates -> capability intersection -> minimal plan -> audit -> safe repair -> readback -> re-audit -> importer/roundtrip/render evidence when applicable -> PASS|rollback`

After a repair, re-run the same audit. If validation worsens, a new error appears, importer/roundtrip/render evidence fails or uncertainty remains, discard the patched artifact and restore the source SHA baseline. Already-green sections remain frozen unless a later change can demonstrably affect them.
