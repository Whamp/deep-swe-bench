# AGENTS.md

Agent-facing project memory for `deep-swe-bench`. Read this before configuring a
new **config** or touching the harness.

## Vocabulary

Canonical nouns and retired terms live in [`CONTEXT.md`](./CONTEXT.md). Use them.
The big ones: **config** (not arm/treatment), **comparison** (not study/run as a
noun), **subset** (not subsample), and **run** as a verb only.

## Repeatable workflows

Use project skills instead of re-reading long cautionary prose:

- **benchmark-config-validation** — use before adding or changing a config, model
  leaf, provider/model API path, usage parser, smoke contract, or worker usage
  accounting. It is the source of truth for native session usage, advisor stream
  filtering, observational-memory worker traces, nested-worker gotchas, provider
  validation notes, and smoke contracts.
- **benchmark-launch** — use before launching `harness/run_batch.py`, especially
  when more than the main executor model is involved. It is the source of truth
  for the confirmation table, credential preflight, thinking-level evidence,
  OpenRouter/default-provider rules, post-launch verification, and whether to
  run the container memory watchdog.

## Standing rules

- Before using a new provider/model/API path, prove it in a model-specific note
  under `docs/` with probe artifacts under `analysis/`.
- Do not persist raw per-cell `--mode json` streams. Main executor usage comes
  from native `session/*.jsonl`; secondary LLM roles need their own compact usage
  source.
- Do not bake feature-specific smoke checks into `harness/run_batch.py`; put them
  in config-authored `smoke.json` contracts.
- If a benchmark launch has advisor, observational-memory workers, subagents,
  local-vLLM shims, or any other secondary model, stop and get explicit user
  confirmation before running it.
- For benchmark launches, “working” means the smoke gate passed and left evidence
  in the result tree. A live process or an `ok` line is not enough.
- For long or high-concurrency benchmark batches, consider
  `scripts/container_memory_watchdog.py`. It is a host-side safety tool for
  active `dsw-*` containers, logs manual interventions separately under
  `runs/container-memory-watchdog/`, and must not mutate official `result.json`
  artifacts.
