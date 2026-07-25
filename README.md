# deep-swe-bench

Hold the model constant, vary one pi harness variable, and measure the delta on
real [DeepSWE](https://deepswe.datacurve.ai/) tasks.

The first comparison is:

- model: `openrouter/deepseek/deepseek-v4-flash`
- thinking: `high` (pinned with `--thinking high`)
- baseline config: clean stock Pi for the selected model/thinking level, no skills/extensions and no config-authored prompt append
- comparison config: pi + the real Ponytail Pi extension, **full/default** mode
- question: does Ponytail help or hurt DeepSWE reward, and does it use more or
  fewer tokens?

This is intentionally **not directly DeepSWE leaderboard-comparable** because of the harness change from mini-swe-agent to Pi. The point is to evaluate the real world effect of pi harness extensions and skills because that is what i actually use for development work. 

## Architecture

Each cell is one `(task, config, rep)`:

1. Pull the DeepSWE task environment image.
2. Build a thin cached layer that adds `pi@0.80.2` to that image.
3. Run pi **inside the task container** at `/app` through `pi --mode rpc`, so the
   agent can read/edit the repo, run the task's real toolchain, and let
   extension follow-up work finish before the harness stops the cell.
4. Commit any uncommitted agent edits, then run the task's `pre_artifacts.sh` to
   produce `/logs/artifacts/model.patch`.
5. Build/run the task verifier image with `--network none` and capture
   `/logs/verifier/reward.json`.
6. Read usage from pi's native `session/*.jsonl`; the full RPC event stream is
   not persisted. Compact sidecars such as advisor `tool-usage.jsonl` are
   filtered live when needed (see `docs/adr/0002-retire-pi-jsonl-stream-capture.md`).
7. Capture the initial executor surface under each cell's `initial_context/`:
   generated system prompt, system-prompt build inputs, first user prompt, and
   the first provider request payloads. This is on by default for Pi and OMP
   runners; pass `--no-initial-context-capture` to disable it for a run.

The verifier always runs in a pristine separate container, matching DeepSWE's
separate-verifier setup.

## Configs

See [`configs/`](configs/) and [`configs/README.md`](configs/README.md). A
**config** is one pi setup (optional prompt layers + skills/extensions); **model +
thinking** is a separate path axis under it (the immutable-leaf rule, see
`docs/adr/0001-directory-and-vocabulary-reorganization.md`). Only the config
changes — model, thinking level, task image, verifier, time budget, and runner
are held constant.

- `baseline` — clean stock Pi: no skills, no config-authored extensions, no
  harness system preamble, and no `orchestration.md` append prompt.
- `baseline-preamble-orchestration` — historical prompt-bearing control: the
  DeepSWE sandbox preamble plus the old "No extra guidance" orchestration.
  Old results previously labeled `baseline` belong under this name.
- `baseline-preamble-orchestration-wf` — historical prompt-bearing workflow
  control: the same preamble plus the mini-swe-agent step-by-step workflow
  prompt. Old results previously labeled `baseline-wf` belong under this name.
- `ponytail-extension` — the vendored Ponytail Pi extension, pinned to
  `PONYTAIL_DEFAULT_MODE=full`.
- `ponytail-full` / `ponytail-lite` / `ponytail-ultra` — the same vendored
  Ponytail Pi extension, pinned to full/lite/ultra modes for non-interactive
  benchmark cells.
- `advisor` — `pi-advisor` extension; advisor model `zai/glm-5.2` via
  `ZAI_API_KEY` (configs leaf `deepseek-v4-flash+glm-5.2`).
- `observational-memory` — `pi-observational-memory` extension; memory workers
  are pinned per model leaf (`settings.json` carries the worker model).

## Run one draft probe

Direct one-cell debugging is an explicit draft/probe path. It cannot write a
canonical result cell:

```sh
source ~/.bashrc   # provides OPENROUTER_API_KEY
python3 harness/run.py \
  --config baseline \
  --task adaptix-name-mapping-aliases \
  --thinking high \
  --agent-timeout 150 \
  --probe-output scratch/probes/baseline-adaptix
```

OMP uses the same required `--probe-output` contract. Scratch probes are
diagnostic only and are not reusable benchmark reps.

## Confirmed batch

Canonical results can be created only from a compiled launch plan and its exact
confirmation identity. First prepare model-free review artifacts:

```sh
export DEEP_SWE_BENCH_STATE_ROOT=/home/will/evals/deep-swe-bench/results/_runs
python3 -m harness.run_batch plan \
  --subject pi \
  --configs 'baseline@1.0.0,ponytail-extension@1.0.0' \
  --baseline-config 'baseline@1.0.0' \
  --model openrouter/deepseek/deepseek-v4-flash \
  --thinking high \
  --range 0:10 \
  --reps 1 \
  --workers 2 \
  --cell-retries 1 \
  --agent-timeout 150 \
  --rpc-quiescence 2 \
  --run-id ponytail-review \
  --state-root "$DEEP_SWE_BENCH_STATE_ROOT" \
  --plan-out runs/launch-plans/ponytail-review.json \
  --receipt-out runs/launch-plans/ponytail-review.txt
```

Review the receipt, including warnings, model roles, credential and billing
routes, tested subject versions, worker count, retry limit, agent timeout, RPC
quiescence, initial-context capture, preflight cells, conditional batch fan-out,
behavior differences, and exact paths. After approving the printed plan
identity, execute only that stored plan:

```sh
python3 -m harness.run_batch execute \
  --plan runs/launch-plans/ponytail-review.json \
  --confirm 'sha256:<exact-reviewed-plan-identity>'
```

Repeating raw config/model/task arguments is not confirmation and is rejected.
Resume uses the same plan file and identity; compatible completed reps are read
without rewriting, while provenance mismatch or launch-input drift stops the
run. Execution uses the worker count and retry limit stored in the plan. It
rechecks config, runtime, capability, and credential-route inputs before every
new or retried rep. A required or new-config preflight remains atomic until
generic health and the config-owned `smoke.json` assertions pass, then the
approved fan-out starts without a second confirmation. See
[`configs/README.md#smoke-tests-and-contracts`](configs/README.md#smoke-tests-and-contracts).

### Live dashboard

Every confirmed execution writes structured state under its configured central
state root:

- `manifest.json` — command, selection, configs, planned reps, and preflight cells
- `status.json` — live counts, active cells, heartbeat, outcomes, compact metrics
- `events.ndjson` — append-only lifecycle events

The plan's stable `--run-id` remains visible to operators. The directory
key combines the requested run id with the confirmed plan identity, so plans
from separate worktrees cannot overwrite each other. `manifest.json` retains
the requested run id and records the run key, originating workspace, result
root, state root, versioned config identities, and launch-plan identity.

Serve the polling dashboard without starting or stopping any benchmark work:

```sh
python3 scripts/run_dashboard.py --host 127.0.0.1 --port 8765 --detail operational
```

Open `http://127.0.0.1:8765/`. Detail levels are `summary`, `operational`, and
`diagnostic`. The page links result/log paths and capped file tails rather than
inlining large raw logs. Existing `scripts/open_runboard.py` / `track.out` flows
still work; the dashboard also lists legacy `runs/*/track.out` files when found.

### Container memory watchdog

`scripts/container_memory_watchdog.py` is a host-side safety tool for active
benchmark containers. It monitors running `dsw-*` containers and, after a
sustained memory spike, kills the largest non-protected child process inside the
container. It protects `pi`, `sleep`, shells, and zombies; if `pi` is the largest
process, it logs an alert only. The script does not edit `result.json` or any
official result artifact.

Use it for long or high-concurrency batches when a pathological agent-written
test could consume host RAM before `--agent-timeout` fires. Current conservative
emergency policy:

```sh
nohup setsid python3 scripts/container_memory_watchdog.py \
  --cap-gb 12 \
  --interval 5 \
  --consecutive 3 \
  --grace 10 \
  --target 'dsw-*' \
  --manual-log runs/container-memory-watchdog/manual_interventions.ndjson \
  --peak-log runs/container-memory-watchdog/container_peaks.ndjson \
  --pidfile runs/container-memory-watchdog/watchdog.pid \
  > runs/container-memory-watchdog/watchdog.out 2>&1 < /dev/null &
```

Run with `--dry-run` first when changing the policy. The separate logs are for
future reference and manual-intervention auditing, not official benchmark
reporting.

### Codex OAuth models

Direct probes of `openai-codex/*` models require
`--pass-openai-codex-oauth`. Confirmed launches do not accept that raw execution
flag. Declare `OPENAI_CODEX_OAUTH` on the executor role in the config lock so the
plan can verify the route and pass only the host Pi `openai-codex` OAuth entry
into each container.

Use the confirmed `plan` command above with
`--model openai-codex/gpt-5.3-codex-spark`. Planning verifies the named route
without putting its value in the plan or receipt. Confirmed execution copies
only the `openai-codex` credential; it does not mount the whole host Pi agent
directory.

#### Subscription quota limits and confirmed resume

The OpenAI Codex subscription has 5-hour and weekly usage windows that can
exhaust mid-batch. A detected transient writes its cell sentinel, records the
confirmed run as paused, and makes `harness.run_batch execute` exit 75.

After the provider window resets, resume by running the same `execute` command
with the same stored plan and confirmation identity. Before another rep starts,
the harness rechecks launch inputs. Completed results created by that exact plan
are provenance-checked and skipped read-only; incompatible occupants or drift
stop instead of being overwritten. Never recompile or repeat raw launch
arguments merely to resume.

### Local Qwen on server60

Current local model endpoint, verified before wiring this run:

- API: `http://100.92.238.117:30000/v1`
- model: `local-vllm/cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4`

Pi supports this via `compat.thinkingFormat: "qwen-chat-template"`, which sends
`chat_template_kwargs.enable_thinking` and `preserve_thinking` for Qwen-compatible
local servers. Both `baseline` and `observational-memory` load the vendored
`local-vllm-preserve-thinking.ts` shim — a symmetric local-vLLM workaround, not a
config advantage.

Use the confirmed `plan` command with model
`local-vllm/cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4`, the versioned baseline and
observational-memory config identities, and `--workers 4`; review the local
compute role and credential route in the receipt before confirming.

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

Analysis requires complete compatible modern provenance by default. Historical
comparisons may use `--allow-legacy-results` only as an explicit decision over an
entirely legacy corpus; mixed modern/legacy provenance and unreadable selected
results still fail visibly.

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

Important: stock headless `observational-memory` DeepSWE runs are diagnostic for
this benchmark regime unless compaction/projection is explicitly exercised. In
single-shot `pi -p` cells, observations/reflections can be recorded and folded
without becoming executor-visible before useful work. Those historical stock OM
result dirs are quarantined under `results/_contaminated/om-no-executor-projection/`;
see [`docs/result-quarantine.md`](docs/result-quarantine.md).

For memory-content isolation, use the explicit 4-arm design:

Prepare this comparison with the confirmed `plan` command using the released,
versioned identities for baseline, recall-placebo, observational-memory, and
projected-om, `--subset 12_v2`, `--reps 3`, and `--workers 2`. The receipt must
show every OM worker role and compact usage source before confirmation.

Delta interpretation:

- `recall-placebo - baseline` isolates recall-tool/system-prompt scaffolding.
- `observational-memory - recall-placebo` isolates background worker side effects
  without guaranteed memory-content projection.
- `projected-om - observational-memory` isolates executor-visible memory content
  from the live projection shim.

Reps accumulate under a config regardless of which subset produced them, so an
existing baseline can be reused — do not rerun baseline unless you want fresh
reps. The OM configs vendor extension source under `configs/` and seed model leaf
`settings.json` / `models.json` as needed.

## Advisor eval

Prepare and confirm the advisor comparison through `harness.run_batch plan`
and `execute`; the receipt must show both executor and advisor roles, their
credential routes, billing categories, bounded calls, and usage sources. Analyze
the resulting compatible reps with:

```sh
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
- `harness/run_batch.py` — confirmed plan/execute CLI and subject-runner adapters.
- `harness/run_state.py` — structured `results/_runs/<run_id>/` manifest/status/events writer.
- `harness/analyze.py` — paired summaries + Wilcoxon/Holm where enough pairs exist.
- `harness/parse_usage.py` — native-session token/cost parser (+ advisor tool-usage path).
- `harness/lib.py` — shared helpers incl. `model_leaf()`.
- `harness/Dockerfile.pi-agent` — task image + pinned pi layer.
- `scripts/run_dashboard.py` — polling web dashboard for `results/_runs` and legacy track files.
- `scripts/materialize_configs.py` — build `configs/` from provenance.
- `scripts/migrate_results.py` — migrate `runs/` -> `results/`.
- `scripts/container_memory_watchdog.py` — host-side emergency RAM watchdog for
  running `dsw-*` benchmark containers.
- `docs/result-quarantine.md` — local quarantine policy for invalid/diagnostic result dirs.
