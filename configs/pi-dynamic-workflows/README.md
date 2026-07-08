# pi-dynamic-workflows config

Uses the production `@quintinshaw/pi-dynamic-workflows` package, which builds on Michael Livs' original `michaelliv/pi-dynamic-workflows` prototype and adds the features needed for benchmark use: custom trigger words, real small/medium/big tier routing, persisted workflow runs, token/cost accounting, and (via a vendored patch) Pi CLI-style `:thinking` suffixes in `model-tiers.json`.

## Behavior

- Loads the extension explicitly with `pi-flags` despite the harness using `--no-extensions` by default.
- `extensions/pi-dynamic-workflows-config.ts` writes workflow settings before the package extension loads, but only inside harness cells where `/arm` and `/out` exist:
  - `keywordTriggerWord`: `pi-workflow`
  - `defaultConcurrency`: `4`
  - `defaultAgentRetries`: `1`
  - `defaultAgentTimeoutMs`: `600000` (10 min per subagent, so a hung model call fails fast instead of stalling the cell until the 90-min cell timeout)
- The same adapter wraps the first benchmark prompt with `pi-workflow` and the package's forced workflow prompt.
- The wrapper requires `background: false` so `pi --mode rpc` waits for the workflow result before the cell ends.
- `gpt-5.5/low/settings.json` sets `defaultThinkingLevel: low`, so routed OpenAI Codex subagents inherit low thinking even when a tier spec has no explicit `:thinking` suffix.
- All three tiers use `openai-codex/gpt-5.5` with an explicit `:thinking` suffix (`:low`, `:medium`, `:xhigh`). The main Pi session also runs `gpt-5.5` at the launch `--thinking` level (low); the tiers vary only the subagent thinking level. Using `gpt-5.5` (272K context) everywhere avoids the 128K-context overflow that killed `gpt-5.3-codex-spark` inventory agents on broad `rg` fan-out.

## Proposed role models

All roles use the existing OpenAI Codex subscription credential path (`--pass-openai-codex-oauth`):

| workflow tier | model:thinking | intended use |
| --- | --- | --- |
| `small` | `openai-codex/gpt-5.5:low` | repository inventory, quick searches, narrow fact gathering |
| `medium` | `openai-codex/gpt-5.5:medium` | focused implementation/debug/test analysis |
| `big` | `openai-codex/gpt-5.5:xhigh` | synthesis, judgment, final cross-context decisions |

All three tiers use `gpt-5.5`; only the thinking level varies (`low` → `medium` → `xhigh`). Adjust the suffixes in `extensions/pi-dynamic-workflows-config.ts` (`MODEL_TIERS`) and the matching `requireText` in `gpt-5.5/low/smoke.json` to change them.

These are config defaults, not a launch confirmation. Because this config uses secondary LLM roles, any benchmark launch must show the role table and get explicit confirmation.

## Vendored patched package

`extensions/package.json` depends on a **vendored tarball** (`file:vendor/quintinshaw-pi-dynamic-workflows-2.10.0.tgz`), not the published npm 2.10.0. The tarball is `npm pack`-ed from `/home/will/projects/pi-dynamic-workflows` at commit `d53b6a7` (2.10.0 + the `:thinking` suffix support for `model-tiers.json` and `/workflows-models`). The published 2.10.0 does **not** support `:thinking` suffixes, so do not switch back to the npm version.

To regenerate the tarball after editing the fork:

```sh
cd /home/will/projects/pi-dynamic-workflows
npm run build && npm test && npm pack
cp quintinshaw-pi-dynamic-workflows-2.10.0.tgz \
  /home/will/evals/deep-swe-bench/configs/pi-dynamic-workflows/extensions/vendor/
cd /home/will/evals/deep-swe-bench/configs/pi-dynamic-workflows/extensions
rm -rf node_modules package-lock.json && npm install --legacy-peer-deps
```

## Fresh checkout setup

```sh
cd configs/pi-dynamic-workflows/extensions
npm ci --legacy-peer-deps
```

## Usage accounting

The harness copies `/root/.pi/workflows` out of each cell to `pi-agent/workflows`, and `harness/parse_usage.py` accounts for persisted workflow run `tokenUsage` in the `workflow_*` and `combined_*` result fields. The smoke contract intentionally requires:

- `pi-agent/workflows/settings.json`
- `pi-agent/workflows/model-tiers.json`
- `pi-agent/workflows/projects/*/runs/*.json`
- `workflow_completed_runs >= 1`
- `workflow_failed_runs == 0`
- `workflow_agent_calls >= 1`
- `workflow_total_tokens >= 1`

This prevents collecting data where workflow subagent cost is invisible.

## Intended smoke/launch shape

```sh
python3 harness/run_batch.py \
  --configs pi-dynamic-workflows \
  --subset 12_v2 \
  --model openai-codex/gpt-5.5 \
  --thinking low \
  --runs 3 \
  --workers 4 \
  --agent-timeout 5400 \
  --rpc-quiescence 2 \
  --pass-openai-codex-oauth
```

Start with low benchmark worker concurrency: each cell may run up to 4 workflow subagents concurrently.
