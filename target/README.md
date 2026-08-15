# Target inventory

`target/inventory.json` is optional target evidence for the Elementor JSON auditor. Generate it only from a controlled WordPress/Elementor installation with:

```bash
wp ejl inventory --output=/tmp/inventory.json
```

The inventory can contain WordPress, Elementor, Elementor Pro, theme and plugin versions plus registered widget owners and control names.

## Public-repository rule

This repository is public and `.gitignore` excludes `target/inventory.json` by default.

Do **not** commit a real client inventory when it exposes private plugin names, versions, URLs, configuration or other client-specific information. Use one of these routes instead:

1. create a deliberately sanitized fixture containing only the dependency facts required for the test; or
2. run the same workflow in a private repository/runtime.

Never store credentials, license keys, licensed plugin ZIP files, Composer auth or private download URLs in this directory.

## Evidence boundary

A target inventory proves only what versions, widgets, controls and owners were observed in the scanned installation. It does not prove that this disposable runtime visually matches the target, and it does not replace staging/browser verification.

For third-party widgets, the matching add-on must also exist in the preview runtime before a visual-render claim is valid.
