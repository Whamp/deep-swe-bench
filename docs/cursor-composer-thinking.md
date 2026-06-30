# Cursor Composer via `pi-cursor-sdk`

Status: validated 2026-06-29 for a baseline DeepSWE run using Cursor Composer slow mode.

## Provider path

- Pi extension: [`pi-cursor-sdk`](https://github.com/fitchmultz/pi-cursor-sdk/tree/74878ed1996f48acd0584133d44e18deb67354e1), version 0.1.52.
- Runtime: pi 0.80.2 with global extension installed at `/home/will/.pi/agent/npm/node_modules/pi-cursor-sdk`.
- Harness-style invocation must load the extension explicitly because `harness/run.py` starts pi with `--no-extensions`:

```sh
--no-extensions -e /home/will/.pi/agent/npm/node_modules/pi-cursor-sdk
```

## Model and slow mode

Use a virtual slow alias, preferably:

```text
cursor/composer-2-5:slow
```

`pi-cursor-sdk` documents `:fast` / `:slow` aliases for models exposing Cursor's boolean `fast` parameter. The alias sends the same Cursor SDK model id with an explicit `fast=false` or `fast=true` param and overrides saved `/cursor-fast` defaults without mutating them. Source: README lines 192 and 228-237 at commit `74878ed1996f48acd0584133d44e18deb67354e1`.

Equivalent one-shot form:

```sh
pi --model cursor/composer-2-5 --cursor-no-fast ...
```

The alias is cleaner for benchmark paths because the model id itself records slow mode.

## Thinking levels

Live catalog output for Composer rows reports `thinking=no`:

```text
cursor     composer-2-5        200K  16.4K  no  yes
cursor     composer-2-5:slow   200K  16.4K  no  yes
```

This means pi cannot control a Cursor SDK thinking parameter for Composer. It does **not** mean Composer cannot think internally. `pi-cursor-sdk` distinguishes Cursor-internal thinking from pi-controllable thinking; `thinking=no` means no exposed `reasoning`, `effort`, or boolean `thinking` parameter. Source: README lines 196-210.

For benchmark axis naming, prefer:

```text
thinking = off
```

`--thinking high` is accepted in a live smoke, but it does not map to a Composer provider parameter. Calling this leaf `high` would imply a controllable condition that does not exist.

## Effort semantics

Cursor's official Composer 2.5 blog and model page mention **effort calibration** as a model behavior improvement, not as a user-settable API field. The official pages also distinguish only the standard and fast variants: fast is the product default, while the standard tier is lower-cost.

The live `@cursor/sdk` catalog item for `composer-2.5` exposes exactly one parameter: `fast`, with values `true` and `false`. It does **not** expose `effort`, `reasoning`, or `thinking`. The default SDK variant is `fast=true`; the benchmark model `cursor/composer-2-5:slow` forces `fast=false`.

Run contract for effort:

```text
effort = provider-internal/adaptive; no benchmark-controlled effort parameter
fast = false via cursor/composer-2-5:slow
pi thinking axis = off because no Composer SDK thinking/effort parameter is exposed
```

If Cursor later adds an `effort` parameter to `Cursor.models.list()`, this note and the benchmark config must be updated before comparing new cells with old ones.

## Docker-cell auth and extension mounting

The host already has a Cursor key, but benchmark cells run inside Docker. A Docker proof showed a working non-secret path:

```text
-e CURSOR_API_KEY
-v /home/will/.pi/agent/npm:/cursor-install:ro
pi ... --no-extensions -e /cursor-install/node_modules/pi-cursor-sdk
```

Important mount detail: mounting only `pi-cursor-sdk` fails because its sibling dependency `@cursor/sdk` is not in Node's resolution path. Mounting `/home/will/.pi/agent/npm` at `/cursor-install` preserves the `node_modules/` layout, so `/cursor-install/node_modules/pi-cursor-sdk` can resolve `/cursor-install/node_modules/@cursor/sdk`.

The committed `configs/baseline-cursor` config uses the same principle with a config-local npm install instead of a global mount: commit `extensions/package.json` and `package-lock.json`, run `npm ci` locally, keep `extensions/node_modules/` ignored, and load `/arm/extensions/node_modules/pi-cursor-sdk` from `pi-flags`. Keep `CURSOR_API_KEY` local/secret; do not commit it.

## Probe evidence

Artifacts:

- `analysis/cursor-composer-slow-probes/live-composer-models.txt`
- `analysis/cursor-composer-slow-probes/live-composer-2.5-model-item.json`
- `analysis/cursor-composer-slow-probes/docker-cell-auth-proof.json`
- `analysis/cursor-composer-slow-probes/summary.json`

Checks run:

1. SDK unit tests: `model-discovery-selection`, `cursor-provider-stream-config`, `index-registration` — 39 tests passed.
2. Temporary Composer request-shape unit test — `cursor/composer-2-5:slow` maps to `ModelSelection { id: "composer-2-5", params: [{ id: "fast", value: "false" }] }`; `:fast` maps to `fast=true`; unsuffixed + process no-fast override maps to `fast=false`.
3. Live Cursor catalog refresh with `PI_CURSOR_SDK_DISABLE_MODEL_CACHE=1` — Composer slow aliases present and `thinking=no`.
4. Live slow alias smoke — `cursor/composer-2-5:slow --thinking off` returned exact text with empty stderr.
5. Live slow alias with `--thinking high` — accepted and returned exact text, confirming high is harmless but not a controllable Composer condition.
6. Live unsuffixed Composer + `--cursor-no-fast` — returned exact text.
7. Harness-style smoke with `--offline --session-dir --no-skills --no-extensions -e /home/will/.pi/agent/npm/node_modules/pi-cursor-sdk` — returned exact text, wrote one native session JSONL, and `harness.parse_usage` read `total_tokens=2483`, `turns=1`.
