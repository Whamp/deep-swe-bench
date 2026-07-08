# harness-forensics — repeatable config-vs-config deep analysis

Deterministic, one-command pipeline that explains **why** one agent config takes more
turns / burns more tokens than another, holding model + thinking + subset constant.

It was built to compare the **OMP** harness (`baseline-omp`) against the **Pi** harness
(`baseline`) on DeepSWE tasks, but it is fully parametrized — point it at any two result
trees that share a model/thinking root and a subset.

## Two stages

| stage | what | how | cost |
|---|---|---|---|
| **1. extract** | per-cell forensics (turns, tool calls, failures, retries, tool-result sizes, per-turn usage, harness-wrapper overhead) + aggregate comparison table | `run_analysis.py` (pure Python) | seconds, **0 model calls** |
| **2. characterize** | per-task-pair qualitative explanation of the gap (exploration breadth, redundant ops, tool-result bloat, verification loops, harness waste) + synthesized `DEEP_ANALYSIS.md` | `harness_forensics.workflow.mjs` (pi workflow, subagents) | ~minutes, model tokens |

Stage 1 is the backbone and is fully reproducible. Stage 2 adds the qualitative layer
and writes the narrative report; it consumes stage 1's `per_pair.json`.

## Run it

### Stage 1 — extract (deterministic)

```bash
python3 analysis/harness-forensics/run_analysis.py \
    --a baseline        --label-a Pi \
    --b baseline-omp    --label-b OMP \
    --root results/gpt-5.5/low \
    --subset 36_v2 \
    --out analysis/omp-vs-pi-36v2
```

Outputs, under `<out>/summaries/`:
- `all_cells.json` — per-cell forensic dicts (both configs, all reps in subset)
- `per_pair.json` — per-task median comparison + per-turn wrapper overhead
- `workflow_args.json` — params for stage 2

Prints an aggregate table (turns, tool calls, failures, cacheRead, input, output,
reasoning, tool-result bytes, solves, mean partial) and a per-tool mix comparison.

Flags: `--reps N` caps reps per task; `--root` is the model+thinking prefix
(`results/<model>/<thinking>`).

### Stage 2 — characterize + synthesize (workflow)

1. Read the emitted params:
   ```bash
   cat analysis/omp-vs-pi-36v2/summaries/workflow_args.json
   ```
2. Submit `harness_forensics.workflow.mjs` to the workflow tool with `args` = that JSON.
   - It chunks the subset's tasks into groups of 2, runs one medium-tier agent per group
     (reads `per_pair.json` + samples the real session traces), then one big-tier
     synthesis agent writes `<out>/DEEP_ANALYSIS.md`.

The workflow is fully parametrized via `args` — nothing is hardcoded to OMP/Pi.

## What the metrics mean

- `non_message_tokens_t1` / `<config>_overhead_tokens` — the constant per-turn harness
  payload (system prompt + tool defs) recorded by configs that emit `contextSnapshot`
  (OMP does; plain Pi does not). This is the direct "harness tax" re-sent every turn.
- `sum_cacheRead` — the dominant token component; a stable cached prefix lands here.
- `total_result_bytes` / `max_result_bytes` — tool-output size. Big outputs (test runs,
  file dumps) accumulate into conversation history and are re-cached each later turn.
- `tool_failures` (`isError`) + `retries_approx` — failure/retry churn.
- `custom_events` — `tool_execution_start` (one per tool call, with an `intent` string)
  and `session_exit` for OMP; plain Pi has none.

## First instance (12_v2)

The original OMP-vs-Pi analysis lives at `analysis/omp-vs-pi-harness/`:
- `DEEP_ANALYSIS.md` — the full report
- `summaries/` — the stage-1 outputs
- `extract_pair.py` — the original (pre-generalization) extractor; superseded by
  `../harness-forensics/extract_session.py`

Headline finding (12_v2, gpt-5.5 low, 36 cells/arm): the ~3× token gap is a
**harness-behavior + prompt-size effect** — not model, cache, tool-failure, or hidden
agents. ~24–31% direct wrapper overhead (7968 tok/turn), ~17% more-turns multiplier,
~52–59% OMP-induced exploratory/serial workflow + replayed tool-history bloat.
