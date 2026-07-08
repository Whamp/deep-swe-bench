# 0003 — Vocabulary reconciliation: run regains a noun sense; comparison stays a view

## Context

ADR-0001 fixed the post-reorganization vocabulary, including "**run** is a verb
only — never a noun," and described a **comparison** as a folder holding a
manifest and generated analysis under
`results/<model-leaf>/<thinking>/comparisons/<name>/`.

Two things changed after ADR-0001, and a 2026-07 architecture review confirmed
the glossary had drifted from the code:

1. **Structured run state landed.** `harness/run_state.py`,
   `results/_runs/<run_id>/` (manifest.json / status.json / events.ndjson),
   `scripts/run_dashboard.py`, and `QuotaResumer` auto-resume all describe one
   thing: a single invocation of `run_batch.py` — live, observable, and
   resumable. That *executory batch entity* needs a noun. "comparison" is the
   wrong word (it is the analytical view over finished reps); "rep" is the
   atomic unit. The only honest name already in the code is "run" (`run_id`,
   `RunStateWriter`, `results/_runs/`).

2. **The comparison manifest-folder was never built.** `harness/analyze.py`
   takes `--comparison` as a *label* (its own argparse help) and emits CSV to
   stdout over the results tree. It writes no manifest and creates no
   comparison folder. The glossary line "its folder holds only a manifest and
   generated analysis" described an aspiration as if it were reality.

Separately, the **model-leaf** concept (executor-only results key,
`exec+advisor` config-leaf form, single-sourced by `lib.model_leaf`) was
introduced by ADR-0001's path rules but never named in the glossary. And the
intro's claim that the repo "only ever runs one agent: `pi`" is false since
`harness/run_omp.py` made `omp` a second subject.

## Decision

- **run** is dual-purpose: a verb (execute reps) and a noun (one `run_batch.py`
  execution, identified by `run_id`, observed via `results/_runs/<run_id>/`).
  This partially supersedes ADR-0001's "run is a verb only." The noun is
  reserved for the executory batch entity; the analytical view remains
  **comparison** and the atomic unit remains **rep**.
- **comparison** remains a *logical view* over existing reps, realised today by
  `analyze.py` over the results tree. The ADR-0001 manifest-folder form is
  deferred (not abandoned) until a consumer needs persisted comparison
  artifacts. Until then the glossary describes what a comparison *is*, not a
  folder layout that does not exist.
- **model-leaf** is named in `CONTEXT.md` as the model's path-identity, with
  ADR-0001 continuing to own the derivation rules.
- The repo runs more than one subject (`pi`, `omp`); the **agent** entry now
  carries both senses instead of claiming `pi` is the only subject.

## Considered options

- **Introduce a new noun ("batch" / "session") for the executory entity.**
  Rejected: the code already chose "run" pervasively (`run_id`, `_runs`,
  `RunStateWriter`); adding a second word for the same thing creates friction
  without removing the existing one — the same mistake as a rule the code
  quietly breaks.
- **Keep "run is a verb only" and force the dashboard to say "batch."**
  Rejected: it pretends the code matches a rule it does not, which is exactly
  the glossary drift this ADR corrects.
- **Build the comparison manifest-folder now to match ADR-0001.** Rejected:
  nothing consumes it yet; building it just to validate a glossary line inverts
  the relationship. Reopen when a real consumer appears.

## Consequences

- `CONTEXT.md`'s `run` entry now carries the noun sense, cross-referenced here;
  its `comparison` entry no longer claims a manifest folder exists.
- Readers tracing ADR-0001 → `CONTEXT.md` should read this ADR for the
  post-structured-run correction. ADR-0001 otherwise stands in full.
- When a persisted comparison-artifact system is actually built, reopen this ADR
  rather than silently editing the glossary.
