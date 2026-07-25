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
  verification, and whether to run the container memory watchdog.
- **runboard** — use when the user explicitly asks for a Herdr/tail view. For
  new batch launches, prefer the structured dashboard written under
  `results/_runs/<run_id>/` and served with `scripts/run_dashboard.py`; runboard
  is now a compatibility/tail workflow, not the primary monitor.

## Agent skills

### Issue tracker

Issues and external PRs are tracked in GitHub with the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the default canonical triage labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, and `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

This is a single-context repo: read root `CONTEXT.md` and relevant ADRs under `docs/adr/`. See `docs/agents/domain.md`.

## Standing rules

- Before using a new provider/model/API path, prove it in a model-specific note
  under `docs/` with probe artifacts under `analysis/`.
- Do not persist raw per-cell `--mode json` streams. Main executor usage comes
  from native `session/*.jsonl`; secondary LLM roles need their own compact usage
  source.
- Do not bake feature-specific smoke checks into `harness/run_batch.py`; put them
  in config-authored `smoke.json` contracts.
- **Do not invent config prompt text.** When creating or changing a config, do not
  add `system_preamble.md`, `orchestration.md`, `--append-system-prompt`, or any
  other config-authored instruction text unless Will explicitly approves the
  exact wording first. This includes supposedly neutral guidance such as “work
  normally” or “use your judgment.” Allowed exceptions are prompt/tool surfaces
  registered by the extension or tool under test itself, such as tool definitions,
  prompt snippets, prompt guidelines, or extension-owned hook output. If extra
  wording seems necessary, propose the exact text and wait for approval before
  writing it.
- **Config leaves are split by thinking level.** Each model+thinking pair a config
  runs at lives under `configs/<config>/<model-leaf>/<thinking>/` (e.g.
  `configs/pi-codex-goal/gpt-5.5/xhigh/`) with a `settings.json` pinning
  `defaultThinkingLevel` and a per-thinking `smoke.json` that asserts the session
  actually ran at that level (`"thinkingLevel":"<level>"` in session logs) plus
  the matching `docs/`+`analysis/` thinking evidence. Leaf-local `smoke.json`
  wins over a top-level `configs/<config>/smoke.json`, which is only a fallback.
  Results are always split by thinking level too
  (`results/<model-leaf>/<thinking>/<config>/`). When adding a new thinking level
  to a config, create the leaf; do not rely on the top-level fallback.
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
- **Results analyses are delivered as a self-contained HTML page served on the
  tailnet** (the user's preferred review format). Do this by default for any
  per-config comparison, run summary, or post-run analysis — not as plain prose.
  Match the project report design system (CSS variables `--bg`/`--surface`/
  `--ink`/`--blue`/`--green`/`--red`/`--amber`, plus `.hero`, `.stats`/`.stat`,
  `.pill good/bad/caution/neutral`, comparison `<table>` with verdict `.tag`s,
  `.callout`, deterministic CSS/SVG bar charts — never AI-generated charts). The
  reference templates are `reports/om-memory-pilot-w10/index.html` and
  `analysis/omp-vs-pi-36v2/index.html`. Always include: hero + verdict pills +
  KPI stat cards, the key comparison table(s), and a conclusion in callouts.
  Serve with `python3 -m http.server <port> --bind 0.0.0.0` from the report dir
  inside a tmux session; pick a free port (8788/8789/5173 are taken), verify
  `curl http://100.112.72.93:<port>/` returns 200, then give the URL. lavish-axi
  has no tailnet host-bind, so do not use it for tailnet serving.
