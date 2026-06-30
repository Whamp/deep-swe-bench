# baseline-cursor

Baseline config for running DeepSWE cells through Cursor Composer via `pi-cursor-sdk`.

## Model contract

Use:

```sh
--model cursor/composer-2-5 --thinking off
```

This config's `pi-flags` loads `pi-cursor-sdk` and passes `--cursor-no-fast`, so the Cursor SDK request uses Composer 2.5 with `fast=false` (Cursor's standard/slow Composer tier). Pi reports `thinking=off` because Cursor Composer exposes no Pi-controllable thinking or reasoning-effort parameter. See `docs/cursor-composer-thinking.md` and `analysis/cursor-composer-slow-probes/` for validation evidence.

## Local setup

The extension dependency install is intentionally not committed. Before running this config on a fresh checkout:

```sh
cd configs/baseline-cursor/extensions
npm ci
```

`node_modules/` is ignored. The container sees it through the config mount at `/arm/extensions/node_modules/pi-cursor-sdk`.

The Cursor API key must be available in the agent container. Current harness support can pass config-local `env` entries; keep `configs/baseline-cursor/env` local and ignored if you use it for `CURSOR_API_KEY`.

Do not commit Cursor secrets.
