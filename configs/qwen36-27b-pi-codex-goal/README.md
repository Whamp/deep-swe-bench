# Qwen3.6-27B + pi-codex-goal

Clean local-Qwen treatment using the existing `pi-codex-goal` package.

## Treatment

The config preserves the baseline Qwen3.6-27B model, high thinking, and sampling
payload. It adds:

1. `pi-codex-goal`, which registers `get_goal`, `create_goal`, and `update_goal`.
2. `initial-create-goal.ts`, which transforms the first benchmark task exactly as
   `/create-goal <task>`.

There is no `system_preamble.md` and no `orchestration.md`. The config does not
add task guidance beyond the package-owned `/create-goal` prompt template.

## Model

- Provider/model: `local-vllm/cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4`
- Thinking: `high`
- Server: `http://100.92.238.117:30000/v1`
- Sampling: temperature 1.0, top-p 0.95, top-k 20, min-p 0.0,
  presence penalty 0.0, repetition penalty 1.0

## Validation

The leaf smoke contract proves the task was wrapped, goal tools were invoked,
the goal reached complete status, and the outbound local-Qwen thinking/sampling
payload remained unchanged.
