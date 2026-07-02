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
  OpenRouter/default-provider rules, structured run-dashboard state, post-launch
  verification, and whether to run the container memory watchdog.
- **runboard** — use when the user explicitly asks for a Herdr/tail view. For
  new batch launches, prefer the structured dashboard written under
  `results/_runs/<run_id>/` and served with `scripts/run_dashboard.py`; runboard
  is now a compatibility/tail workflow, not the primary monitor.

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
  in the result tree. A live process, dashboard heartbeat, or an `ok` line is not
  enough.
- For long or high-concurrency benchmark batches, consider
  `scripts/container_memory_watchdog.py`. It is a host-side safety tool for
  active `dsw-*` containers, logs manual interventions separately under
  `runs/container-memory-watchdog/`, and must not mutate official `result.json`
  artifacts.
- Do not include `results/_contaminated/` in normal efficacy analyses. See
  `docs/result-quarantine.md` before using quarantined runs; those directories
  are diagnostic/harness-failure artifacts unless an analysis explicitly targets
  that failure mode.
