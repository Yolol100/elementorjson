# Section widget capability and safe repair

This controlled runtime does not use one static Elementor/Elementor Pro widget list as execution truth. It exports the widgets and controls actually registered by the exact runtime and uses that inventory as availability evidence.

## Version-bound inventory

For each run, bind the Elementor Core version, Elementor Pro version when loaded, active plugins, active devices/breakpoints, registered widgets, widget ownership and exposed controls. Release history and documentation can explain drift, but they do not prove that a widget/control exists in the current runtime.

Classic widgets expose controls that can be checked against the generated inventory. Atomic/V4 typed props/styles must stay on their dedicated typed validation path rather than being treated as Classic controls.

## Per-section selection contract

The calling Elementor Skill remains responsible for translating section intent into a small candidate set. For each section or reusable component it must:

1. determine content, semantic role, functionality, dynamic data, layout, visual treatment, responsive behavior and accessibility needs;
2. prefer the smallest native Elementor Core/Pro composition that can satisfy those needs;
3. intersect candidate widgets with the exact runtime inventory;
4. reject any widget that is not registered in the runtime;
5. verify required controls/capabilities before writing settings;
6. record Pro/add-on/site-object dependencies and unresolved target assumptions;
7. keep unknown site-bound data unknown instead of inventing IDs or mappings.

The runtime inventory proves availability only. It does not prove that the choice is visually correct on a customer target.

## Safe automatic correction

`tools/repair_elementor_json.py` applies only allowlisted, reversible source repairs and always writes to a separate output file. It never mutates the source artifact in place.

Current allowlist:

- `EJL-SAFE-001`: remove an empty/no-op Classic setting only when the exact runtime inventory proves that the control is unrecognized for that registered widget and the key is not private/special.

The repair tool deliberately blocks instead of guessing when:

- a widget is not registered;
- an unknown setting is non-empty;
- the element is Atomic/V4 and requires typed prop/style evidence;
- a safe repair would require changing content, layout, typography, interactions, Dynamic Tags, Forms, Loops, WooCommerce, Theme Builder placement, Components, globals/classes/variables or site-object IDs.

Each applied repair records rule ID, affected path, before/after values and runtime version evidence. The report also records the source SHA-256 so rollback means restoring the exact source artifact.

## Verification loop

Use:

`inventory -> section intent -> candidate widgets -> capability intersection -> minimal plan -> audit -> safe repair -> re-audit -> importer/roundtrip/render evidence when applicable -> PASS|rollback`

After a repair, re-run the same audit. If validation worsens, a new error appears, importer/roundtrip/render evidence fails or uncertainty remains, discard the patched artifact and restore the source SHA baseline. Already-green sections remain frozen unless a later change can demonstrably affect them.
