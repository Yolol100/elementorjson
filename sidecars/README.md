# Sidecars

Optional project-specific composition contracts live here, separate from `templates/` so the Elementor runtime never tries to import them as templates.

For `templates/homepage.json`, use matching names when needed:

- `sidecars/homepage.design-intent.json`
- `sidecars/homepage.content-contract.json`

The `Page Composition Contract` workflow automatically pairs these sidecars with the template stem and runs `tools/audit_page_composition.py`.

Keep client-specific wording, claims and proof policy in run/project-scoped inputs. Do not commit confidential client data or one-off production exports to the default branch.
