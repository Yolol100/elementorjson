# Section widget capability and safe repair

This controlled runtime does not use one static Elementor/Elementor Pro widget list as execution truth. It exports the widgets and controls actually registered by the exact runtime and uses that inventory as availability evidence.

## Version-bound inventory

For each run, bind the Elementor Core version, Elementor Pro version when loaded, active plugins, active devices/breakpoints, registered widgets, widget ownership, plugin slug, categories and exposed controls. Release history and documentation can explain drift, but they do not prove that a widget/control exists in the current runtime.

Classic widgets expose controls that can be checked against the generated inventory. Atomic/V4 typed props/styles must stay on their dedicated typed validation path rather than being treated as Classic controls.

## Object-context routing

Classify the Elementor object before selecting widgets. The object type determines the required roles; the exact widget is chosen only after intersecting those roles with the runtime inventory.

| Object/context | Required planning roles | Typical native candidates when registered | Extra gates |
| --- | --- | --- | --- |
| Archive | archive context, title/description when needed, dynamic listing, query/pagination, optional filters | Archive Title, Archive Posts, Loop Grid, taxonomy/dynamic widgets | Pro/Theme Builder, query source, display conditions |
| Container | layout parent, direction, width, alignment, gap, responsive behavior | Container and child widgets/elements | Do not add content widgets unless section intent requires them |
| Div block | Atomic structural wrapper | Atomic Div/Block plus typed child elements | V4/Atomic target evidence |
| Flexbox | Atomic/Flex structural layout | Flexbox plus typed child elements | V4/Atomic props, wrap/direction/breakpoints |
| Atomic Form | form wrapper, labels, fields, validation, submit, actions | Atomic Form with Label, Input, Text Area, Checkbox, Radio, Date, Time, Select, File Upload, Submit | V4, actions, privacy, spam, delivery/integration tests |
| Grid / Raster | grid structure, tracks, gaps, item placement, responsive transformation | Grid/Atomic Grid or supported container grid | V4/target evidence where Atomic; layout-math check |
| Error 404 | recovery message, useful navigation, search, optional recent/relevant content | Heading, Text, Search/Search Form, Button, Posts/Loop Grid | 404 display condition and real missing-URL test |
| Floating Element | concise message/action, optional icon/image/form, position/visibility/interaction | Heading/Text/Button/Image/Icon/Form depending intent | trigger/condition/position, reduced motion, mobile obstruction |
| Footer | branding, navigation, legal/contact/social, optional search/newsletter | Site Logo, Menu/Nav Menu, Heading/Text, Social Icons, Form/Search | Theme Builder/display conditions; global consistency |
| Header | branding, primary navigation, search, primary action, optional account/cart/social | Site Logo, Menu/Nav Menu, Search, Button, Social Icons, Woo cart/account when needed | Theme Builder/display conditions; responsive menu behavior |
| Loop Item | dynamic item identity, image, title, metadata/excerpt/price/action as required | Featured Image, Post/Product Title, Excerpt, Post Info, Dynamic Tags, Button, Woo product widgets | correct loop type/query; no invented IDs; dynamic data proof |
| Page / Pagina | semantic sections and page-level hierarchy | smallest Core/Pro composition per section intent | whole-page visual target and section/context QA |
| Popup | focused message/CTA, optional form/countdown/media/navigation | Heading/Text/Button/Form/Countdown/Image/Video/Menu as needed | popup layout, conditions, triggers, close behavior, focus/keyboard |
| Search Results | search context, result listing, query/pagination, empty state, optional refinement | Search, Archive Title, Archive Posts or Loop Grid | Search Results condition; query source; no-results test |
| Section | semantic section wrapper and only the content roles required by that section | Section/Container plus minimal content widgets | preserve V3/V4 family and page rhythm |

The names above are role examples, not a static availability list. A candidate that is not registered in the exact runtime is unavailable.

## Per-section selection contract

The calling Elementor Skill remains responsible for translating object context plus section intent into a small candidate set. For each section or reusable component it must:

1. classify the object/context first;
2. determine content, semantic role, functionality, dynamic data, layout, visual treatment, responsive behavior and accessibility needs;
3. prefer the smallest native Elementor Core/Pro composition that can satisfy those needs;
4. when a native composition is insufficient or an installed site already depends on an add-on, include matching third-party widgets as secondary candidates;
5. intersect every candidate with the exact runtime inventory;
6. reject any widget that is not registered in the runtime;
7. verify required controls/capabilities before writing settings;
8. record Pro/add-on/site-object dependencies and unresolved target assumptions;
9. keep unknown site-bound data unknown instead of inventing IDs or mappings.

The runtime inventory proves availability only. It does not prove that the choice is visually correct on a customer target.

## Popular add-on discovery policy

Do not maintain a permanent hardcoded list of "popular" add-on widgets as execution truth. Popularity and widget catalogs change.

When add-on awareness is relevant:

1. Use current WordPress.org installation signals and the vendor's current widget catalog only as discovery/ranking evidence.
2. Prefer established Elementor add-on families with meaningful current adoption, but never infer that a target has them installed.
3. Read the exact target/runtime inventory and identify third-party widgets by `owner=third-party` plus `plugin_slug`.
4. Build secondary candidates from recurring capability families such as Mega/Nav Menu, Post Grid/List/Carousel, WooCommerce product grids/carousels/filters, Search/AJAX Search, advanced filters, Accordion/Tabs, Pricing Table, Testimonial/Review, Team Member, Gallery/Media Grid, Info/Icon Box, Content Toggle, Modal/Offcanvas, Lottie/animation, data tables/charts and form stylers.
5. Prefer Core/Pro when it satisfies the requirement with equal or lower dependency/risk. Prefer an installed add-on widget when it is already the site's established dependency or provides a required capability not available natively.
6. Never install or introduce an add-on solely because it is popular without an explicit dependency decision.
7. Verify the exact add-on widget's controls and responsive/dynamic behavior from the runtime inventory before use.

Current web research may name candidate add-on families, but those names belong to the execution evidence for that run rather than this durable contract.

## Safe automatic correction

`tools/repair_elementor_json.py` applies only allowlisted, reversible source repairs and always writes to a separate output file. It never mutates the source artifact in place.

Current allowlist:

- `EJL-SAFE-001`: remove an empty/no-op Classic setting only when the exact runtime inventory proves that the control is unrecognized for that registered widget and the key is not private/special.

The repair tool deliberately blocks instead of guessing when:

- a widget is not registered;
- an unknown setting is non-empty;
- the element is Atomic/V4 and requires typed prop/style evidence;
- a safe repair would require changing content, layout, typography, interactions, Dynamic Tags, Forms, Loops, WooCommerce, Theme Builder placement, Components, globals/classes/variables or site-object IDs;
- replacing one add-on widget with another or with a native widget would change behavior without target proof.

Each applied repair records rule ID, affected path, before/after values and runtime version evidence. The report also records the source SHA-256 so rollback means restoring the exact source artifact.

## Verification loop

Use:

`object context -> inventory -> section intent -> candidate widgets -> capability intersection -> minimal plan -> audit -> safe repair -> re-audit -> importer/roundtrip/render evidence when applicable -> PASS|rollback`

After a repair, re-run the same audit. If validation worsens, a new error appears, importer/roundtrip/render evidence fails or uncertainty remains, discard the patched artifact and restore the source SHA baseline. Already-green sections remain frozen unless a later change can demonstrably affect them.
