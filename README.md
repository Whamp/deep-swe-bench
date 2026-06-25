# deep-swe-bench

Hold the model constant, vary one pi harness variable, and measure the delta on
real [DeepSWE](https://deepswe.datacurve.ai/) tasks.

The first study is:

- model: `openrouter/deepseek/deepseek-v4-flash`
- thinking: `high` (pinned with `--thinking high`)
- baseline arm: stock pi, no skills/extensions
- treatment arm: pi + the real Ponytail Pi extension, **full/default** mode
- question: does Ponytail help or hurt DeepSWE reward, and does it use more or
  fewer tokens?

This is intentionally **not directly DeepSWE leaderboard-comparable** because of the harness change from mini-swe-agent to Pi. The point is to evaluate the real world effect of pi harness extensions and skills because that is what i actually use for development work. 

## Architecture

Each cell is one `(task, arm, rep)`:

1. Pull the DeepSWE task environment image.
2. Build a thin cached layer that adds `pi@0.80.2` to that image.
3. Run pi **inside the task container** at `/app`, so the agent can read/edit the
   repo and run the task's real toolchain.
4. Commit any uncommitted agent edits, then run the task's `pre_artifacts.sh` to
   produce `/logs/artifacts/model.patch`.
5. Build/run the task verifier image with `--network none` and capture
   `/logs/verifier/reward.json`.
6. Parse pi's `--mode json` stream for token/cost/turn/tool metrics.

The verifier always runs in a pristine separate container, matching DeepSWE's
separate-verifier setup.

## Arms

See [`arms/`](arms/).

- `baseline` — `--no-skills --no-extensions`.
- `ponytail-pi-extension` — loads the vendored Ponytail Pi extension, pins `PONYTAIL_DEFAULT_MODE=full`, and exposes Ponytail skills like a normal Pi install.
- `ponytail-full` — older diagnostic skill-only arm; kept for comparison, not the primary Ponytail result.
- `ponytail-lite` / `ponytail-ultra` — skill-only diagnostic arms with different pinned modes.
- `pi-advisor-glm52` — loads `pi-advisor` as an explicit extension, enables the
  advisor tool, and configures the advisor model as `zai/glm-5.2` using
  `ZAI_API_KEY`. The executor model remains `openrouter/deepseek/deepseek-v4-flash`.
- `pi-observational-memory` — loads only `pi-observational-memory` as an explicit
  extension. Memory workers use the session model, so the only model remains
  `openrouter/deepseek/deepseek-v4-flash`.

Only the arm changes. Model, thinking level, task image, verifier, time budget,
and runner are held constant.

## Run one cell

```sh
source ~/.bashrc   # provides OPENROUTER_API_KEY
python3 harness/run.py \
  --arm baseline \
  --task adaptix-name-mapping-aliases \
  --run-name smoke \
  --thinking high \
  --agent-timeout 150
```

Run the matched Ponytail extension cell:

```sh
python3 harness/run.py \
  --arm ponytail-pi-extension \
  --task adaptix-name-mapping-aliases \
  --run-name smoke \
  --thinking high \
  --agent-timeout 150
```

## Batch

```sh
python3 harness/run_batch.py \
  --arms baseline,ponytail-pi-extension \
  --slice 0:10 \
  --run-name ponytail-full-pilot \
  --thinking high \
  --workers 2
```

Use `--tasks a,b,c` instead of `--slice` for an explicit paired set. The batch
runner resumes existing `result.json` files unless `--force` is passed.

## Analyze

```sh
uv venv cache/venv
. cache/venv/bin/activate
uv pip install -e .
python harness/analyze.py --run ponytail-full-pilot --arms baseline,ponytail-pi-extension
```

Main success metric is `reward_partial` from DeepSWE `reward.json`. Binary
`reward` is reported, but long-horizon tasks often show partial progress before
full solve, so partial is the primary paired metric.

Token metric is pi-reported total tokens from the JSON stream:

```text
input_tokens + output_tokens + cache_read_tokens + cache_write_tokens
```

For advisor arms, `advisor_total_tokens` is parsed separately from advisor tool
result details, and `combined_total_tokens = total_tokens + advisor_total_tokens`.
Observational-memory worker calls are extension-internal; their debug/state is
persisted under each cell's `pi-agent/observational-memory/` for audit.

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
  --arms baseline,pi-observational-memory \
  --slice 0:10 \
  --run-name om-pilot \
  --workers 2
python3 harness/analyze.py --run om-pilot --arms baseline,pi-observational-memory
```

The `pi-observational-memory` arm vendors extension source under `arms/` and
seeds `settings.json` plus a minimal `models.json` OpenRouter auth config inside
the container so memory workers can use the same DeepSeek session model.
Extension artifacts are copied back to each cell under `pi-agent/` before
container cleanup.

## Advisor eval

After a baseline run exists for a task slice, compare the same baseline to the
advisor arm:

```sh
source ~/.bashrc   # provides OPENROUTER_API_KEY and ZAI_API_KEY
python3 harness/run_batch.py \
  --arms baseline,pi-advisor-glm52 \
  --slice 0:10 \
  --run-name advisor-glm52-pilot \
  --workers 2
python3 harness/analyze.py --run advisor-glm52-pilot --arms baseline,pi-advisor-glm52
```

The `pi-advisor-glm52` arm vendors `pi-advisor` source under `arms/` and seeds
`advisor.json`/`models.json` inside the container so the advisor tool is enabled
non-interactively.

## Report assets

The completed Ponytail extension run summary and social-card graphics are in
[`reports/ponytail-full-pilot-w2/`](reports/ponytail-full-pilot-w2/).

## Current trade-offs

- Agent container currently has normal outbound network so pi can reach
  OpenRouter. The verifier is air-gapped (`--network none`). For a stricter
  publication-quality run, add the programbench-style allowlist proxy so the
  agent can reach only OpenRouter. The comparison is still paired/symmetric, but
  default egress is less hermetic.
- Short timeouts are for harness validation only. Real DeepSWE runs should use
  the task timeout or a predeclared smaller budget.
- Baseline isolation relies on `--no-skills --no-extensions`. Treatment arms load
  explicit vendored skills/extensions from `arms/` so global Pi config does not
  contaminate the comparison.

## Files

- `harness/run.py` — one `(arm, task, rep)` cell.
- `harness/run_batch.py` — paired scheduler with resume.
- `harness/analyze.py` — paired summaries + Wilcoxon/Holm where enough pairs exist.
- `harness/parse_usage.py` — pi JSON stream token/cost parser.
- `harness/Dockerfile.pi-agent` — task image + pinned pi layer.
