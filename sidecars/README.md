# Sidecars

Optional project-specific authored contracts live here, separate from `templates/` so Elementor runtime never tries to import them as templates.

For `templates/homepage.json`, use matching names when needed:

- `sidecars/homepage.design-intent.json`
- `sidecars/homepage.content-contract.json`

The Page Composition Contract workflow pairs these sidecars with the template. It runs `tools/audit_page_composition.py` and separately generates `artifacts/visual-targets/homepage.json` with `tools/build_visual_target.py`.

Do not hand-maintain generated Visual Targets in `sidecars/`: they are derived source-prediction artifacts and must be rebuilt after material JSON changes. Keep client-specific wording, claims and proof policy in run/project-scoped inputs. Do not commit confidential client data or one-off production exports to the public default branch.
