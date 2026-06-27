# deep-swe-bench

Hold the model constant, vary one pi harness variable, and measure the delta on
real [DeepSWE](https://deepswe.datacurve.ai/) tasks.

The first comparison is:

- model: `openrouter/deepseek/deepseek-v4-flash`
- thinking: `high` (pinned with `--thinking high`)
- baseline config: stock pi, no skills/extensions
- treatment config: pi + the real Ponytail Pi extension, **full/default** mode
- question: does Ponytail help or hurt DeepSWE reward, and does it use more or
  fewer tokens?

This is intentionally **not directly DeepSWE leaderboard-comparable** because of the harness change from mini-swe-agent to Pi. The point is to evaluate the real world effect of pi harness extensions and skills because that is what i actually use for development work. 

## Architecture

Each cell is one `(task, config, rep)`:

1. Pull the DeepSWE task environment image.
2. Build a thin cached layer that adds `pi@0.80.2` to that image.
3. Run pi **inside the task container** at `/app`, so the agent can read/edit the
   repo and run the task's real toolchain.
4. Commit any uncommitted agent edits, then run the task's `pre_artifacts.sh` to
   produce `/logs/artifacts/model.patch`.
5. Build/run the task verifier image with `--network none` and capture
   `/logs/verifier/reward.json`.
6. Read usage from pi's native `session/*.jsonl` (the `--mode json` stream is no
   longer persisted — see `docs/adr/0002-retire-pi-jsonl-stream-capture.md`).

The verifier always runs in a pristine separate container, matching DeepSWE's
separate-verifier setup.

## Configs

See [`configs/`](configs/) and [`configs/README.md`](configs/README.md). A
**config** is one pi setup (prompt treatment + skills/extensions); **model +
thinking** is a separate path axis under it (the immutable-leaf rule, see
`docs/adr/0001-directory-and-vocabulary-reorganization.md`). Only the config
changes — model, thinking level, task image, verifier, time budget, and runner
are held constant.

- `baseline` — no skills and no discovered extensions; loads only the local-vLLM
  preserve-thinking shim (a no-op for non-`local-vllm` models).
- `baseline-wf` — baseline plus the mini-swe-agent step-by-step workflow prompt.
- `ponytail-extension` — the vendored Ponytail Pi extension, pinned to
  `PONYTAIL_DEFAULT_MODE=full`.
- `ponytail-full` / `ponytail-lite` / `ponytail-ultra` — skill-only configs with
  different pinned modes.
- `advisor` — `pi-advisor` extension; advisor model `zai/glm-5.2` via
  `ZAI_API_KEY` (configs leaf `deepseek-v4-flash+glm-5.2`).
- `observational-memory` — `pi-observational-memory` extension; memory workers
  are pinned per model leaf (`settings.json` carries the worker model).

## Run one cell

```sh
source ~/.bashrc   # provides OPENROUTER_API_KEY
python3 harness/run.py \
  --config baseline \
  --task adaptix-name-mapping-aliases \
  --thinking high \
  --agent-timeout 150
```

Run the matched Ponytail extension cell:

```sh
python3 harness/run.py \
  --config ponytail-extension \
  --task adaptix-name-mapping-aliases \
  --thinking high \
  --agent-timeout 150
```

Output lands at `results/<model-leaf>/<thinking>/<config>/<task>/rep<N>/`.

## Batch

```sh
python3 harness/run_batch.py \
  --configs baseline,ponytail-extension \
  --range 0:10 \
  --thinking high \
  --workers 2
```

Use `--tasks a,b,c` for an explicit paired set, or `--subset 36_v1` to read
`subsets/36_v1.txt`. The batch runner resumes existing `result.json` files
unless `--force` is passed (resume is by `(task, rep)` existence).

### Codex OAuth models

For `openai-codex/*` models, pass only the host Pi `openai-codex` OAuth entry
into each container (`--pass-openai-codex-oauth` is **required** for these
models or the cell exits early):

```sh
python3 harness/run_batch.py \
  --configs baseline \
  --model openai-codex/gpt-5.3-codex-spark \
  --thinking high \
  --workers 2 \
  --pass-openai-codex-oauth
```

The runner copies only `openai-codex` from `~/.pi/agent/auth.json`; it does not
mount the whole host Pi agent directory.

### Local Qwen on server60

Current local model endpoint, verified before wiring this run:

- API: `http://100.92.238.117:30000/v1`
- model: `local-vllm/cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4`

Pi supports this via `compat.thinkingFormat: "qwen-chat-template"`, which sends
`chat_template_kwargs.enable_thinking` and `preserve_thinking` for Qwen-compatible
local servers. Both `baseline` and `observational-memory` load the vendored
`local-vllm-preserve-thinking.ts` shim — a symmetric local-vLLM workaround, not a
treatment advantage.

```sh
MODEL=local-vllm/cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4
python3 harness/run_batch.py \
  --configs baseline,observational-memory \
  --model "$MODEL" \
  --thinking high \
  --workers 4
```

(For local Qwen, ~4 workers is the server's sweet spot; 8 gets slow. Codex /
OpenAI-codex models use separate remote subscriptions with no local contention.)

## Analyze

```sh
uv venv cache/venv
. cache/venv/bin/activate
uv pip install -e .
python harness/analyze.py \
  --model openrouter/deepseek/deepseek-v4-flash \
  --thinking high \
  --comparison ponytail-full-pilot \
  --configs baseline,ponytail-extension
```

Main success metric is `reward_partial` from DeepSWE `reward.json`. Binary
`reward` is reported, but long-horizon tasks often show partial progress before
full solve, so partial is the primary paired metric.

Token metric is the executor total read from the native session:

```text
input_tokens + output_tokens + cache_read_tokens + cache_write_tokens
```

For the `advisor` config, advisor usage is read from the filtered
`tool-usage.jsonl` (advisor `tool_execution_end` events only):
`advisor_total_tokens`, `advisor_cost_usd`, and `combined_total_tokens` /
`combined_cost_usd`. `cost_usd` remains the main-agent cost.

Observational-memory worker calls are extension-internal (a known unmeasured
usage gap — see `AGENTS.md`); their debug/state persists under each cell's
`pi-agent/observational-memory/` for audit.

For reasoning models, pi/OpenRouter includes reasoning tokens in `output_tokens`.

## Smoke evidence

Validated end-to-end on `adaptix-name-mapping-aliases` with a deliberately short
150s agent budget:

```text
baseline       partial=0.000  binary=0  tokens=1,248,150  cost=$0.0320  patch=7,053B
ponytail-full  partial=0.000  binary=0  tokens=1,377,521  cost=$0.0349  patch=4,894B
```

This is not a conclusion about ponytail. It only proves the harness runs:
non-empty patches, verifier reward, token/cost accounting, and paired analysis.

## Observational-memory eval

Compare baseline to Pi with only the observational-memory extension:

```sh
source ~/.bashrc   # provides OPENROUTER_API_KEY
python3 harness/run_batch.py \
  --configs observational-memory \
  --model openrouter/deepseek/deepseek-v4-flash \
  --thinking high \
  --workers 2
python harness/analyze.py \
  --model openrouter/deepseek/deepseek-v4-flash \
  --thinking high \
  --comparison om-memory \
  --configs baseline,observational-memory
```

Reps accumulate under a config regardless of which subset produced them, so an
existing baseline (e.g. from `ponytail-full-pilot`) is reused — do not rerun
baseline unless you want fresh reps. The `observational-memory` config vendors
extension source under `configs/` and seeds the leaf `settings.json` (worker
model) + `models.json` from the model leaf.

## Advisor eval

```sh
source ~/.bashrc   # provides OPENROUTER_API_KEY and ZAI_API_KEY
python3 harness/run_batch.py \
  --configs baseline,advisor \
  --model openrouter/deepseek/deepseek-v4-flash \
  --thinking high \
  --workers 2
python harness/analyze.py \
  --model openrouter/deepseek/deepseek-v4-flash \
  --thinking high \
  --comparison advisor-glm52 \
  --configs baseline,advisor
```

The `advisor` config vendors `pi-advisor` source under `configs/` and seeds the
leaf `advisor.json`/`models.json`/`settings.json`. `models.json` is Z.AI-only for
GLM-5.2 (`ZAI_API_KEY`), not OpenRouter. `settings.json` enables Pi retry with
`maxRetries: 12` / `baseDelayMs: 1000` to soften transient Z.AI 429s.

## Report assets

Completed run summaries and social-card graphics are under `reports/`.

## Current trade-offs

- Agent container currently has normal outbound network so pi can reach
  OpenRouter. The verifier is air-gapped (`--network none`).
- Short timeouts are for harness validation only. Real DeepSWE runs use the task
  timeout or a predeclared smaller budget.
- Baseline isolation relies on `--no-skills --no-extensions`. Treatment configs
  load explicit vendored skills/extensions from `configs/` so global Pi config
  does not contaminate the comparison.

## Files

- `harness/run.py` — one `(config, task, rep)` cell.
- `harness/run_batch.py` — scheduler with resume.
- `harness/analyze.py` — paired summaries + Wilcoxon/Holm where enough pairs exist.
- `harness/parse_usage.py` — native-session token/cost parser (+ advisor tool-usage path).
- `harness/lib.py` — shared helpers incl. `model_leaf()`.
- `harness/Dockerfile.pi-agent` — task image + pinned pi layer.
- `scripts/materialize_configs.py` — build `configs/` from provenance.
- `scripts/migrate_results.py` — migrate `runs/` -> `results/`.
