# Target inventory

Optional: add `inventory.json` exported from the real Elementor installation you want to target.

Generate it with the included WordPress plugin:

```bash
wp ejl inventory --output=/tmp/inventory.json
```

The inventory contains Elementor/WordPress/plugin version metadata plus registered widget names, owners and control names. Do not put credentials, licensed plugin ZIP files or private download URLs in this directory.
