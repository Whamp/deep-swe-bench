# AGENTS.md

Agent-facing project memory for `deep-swe-bench`. Read this before configuring a
new **config** or touching the harness.

## Vocabulary

Canonical nouns and retired terms live in [`CONTEXT.md`](./CONTEXT.md). Use them.
The big ones: **config** (not arm/treatment), **comparison** (not study or run
for an analytical view), **subset** (not subsample), and **run** as either the
verb or one execution of a confirmed launch plan (never an individual rep).

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
  verification, and container resource supervisor checks.
- **runboard** — use when the user explicitly asks for a Herdr/tail view. For
  new batch launches, prefer the structured dashboard written under
  `results/_runs/<run_id>/` and served with `scripts/run_dashboard.py`; runboard
  is now a compatibility/tail workflow, not the primary monitor.

## Agent skills

### Issue tracker

Issues and external PRs are tracked in GitHub with the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the canonical triage labels listed in `docs/agents/issue-tracker.md`.

### Domain docs

This is a single-context repo: read root `CONTEXT.md` and relevant ADRs under `docs/adr/`. See `docs/agents/domain.md`.

### Local-model analysis

When an analysis includes a local model, read
[local-model analysis](docs/agents/local-model-analysis.md). Treat frontier
models as capability references, not expected peers; lead with the local
model's reliable abilities, failure stages, scaffoldable weaknesses, and
concrete support experiments.

## Standing rules

- Before using a new provider/model/API path, prove it in a model-specific note
  under `docs/` with probe artifacts under `analysis/`.
- Do not persist raw per-cell `--mode json` streams. Main executor usage comes
  from native `session/*.jsonl`; secondary LLM roles need their own compact usage
  source.
- Do not bake feature-specific smoke checks into `harness/run_batch.py`; put them
  in config-authored `smoke.json` contracts.
- **Do not invent config prompt text** — approval-gated, with narrow
  extension-owned exceptions. [benchmark-config-validation](.pi/skills/benchmark-config-validation/SKILL.md)
  owns the rule.
- **Config leaves are split by thinking level** — leaf layout, smoke precedence,
  and results-tree paths are owned by
  [benchmark-config-validation](.pi/skills/benchmark-config-validation/SKILL.md).
- Launches with any secondary model (advisor, observational-memory workers,
  subagents, local-vLLM shims) go through the same exact-plan gate as every other
  launch — [benchmark-launch](.pi/skills/benchmark-launch/SKILL.md) owns it.
- A benchmark launch counts as **working** only per
  [benchmark-launch](.pi/skills/benchmark-launch/SKILL.md) step 9 — never from
  liveness, heartbeats, or an `ok` line.
- Every confirmed launch must declare subject/verifier memory, additional swap,
  and host reserve in its approved plan. Verify the persistent
  `scripts/container_resource_supervisor.py` singleton before execution. It
  contains complete labeled runs, writes halt evidence under structured state,
  logs interventions separately under `runs/container-resource-supervisor/`,
  and must not mutate official `result.json` artifacts. See ADR-0008.
- Do not include `results/_contaminated/` in normal efficacy analyses. See
  `docs/result-quarantine.md` before using quarantined runs; those directories
  are diagnostic/harness-failure artifacts unless an analysis explicitly targets
  that failure mode.
- **Pi version differences are provenance-only by default.** Reuse and compare
  baseline results across Pi subject versions. Record the version difference,
  but do not treat it as a behavioral confound or use it to require or recommend
  rerunning a baseline. Treat a specific Pi version change as behaviorally
  material only when Will explicitly tags it as capable of changing behavior.
- **Results analyses are delivered as tailnet-served HTML reports**, by default
  for any per-config comparison, run summary, or post-run analysis — never plain
  prose. Format, design system, report home, and serving procedure live in
  [report-delivery](docs/agents/report-delivery.md).
