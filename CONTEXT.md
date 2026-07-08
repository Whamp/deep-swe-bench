# deep-swe-bench

A harness for measuring how coding-agent configuration choices affect
performance on real [DeepSWE](https://deepswe.datacurve.ai/) tasks. The model and
thinking level are held constant; one **config** is varied and compared against a
**baseline**.

Upstream vocabulary is shared with the [deep-swe](../deep-swe/) task corpus and
[Pier](https://github.com/datacurve-ai/pier) (a Harbor-compatible runner). This
repo refines Pier's "agent" into **config** for the single-subject case. More
than one coding agent can run as the subject, though — see **agent** below.

This file is a glossary: it names the nouns, not the on-disk layout. The path
realisation is fixed by
[ADR-0001](docs/adr/0001-directory-and-vocabulary-reorganization.md); vocabulary
reconciled with the code since then is in
[ADR-0003](docs/adr/0003-vocabulary-reconciliation-run-and-comparison.md), the
grandfathered legacy schema in
[ADR-0004](docs/adr/0004-freeze-legacy-arm-result-schema.md), and the legitimized
`cell` term in
[ADR-0005](docs/adr/0005-legitimize-cell-as-rep-container.md).

## Language

**config**:
A coding-agent setup: the system-prompt layers plus which skills/extensions load
and any extra flags/env. The single variable a comparison changes. `baseline` is
the control config.
_Avoid_: arm, treatment, variant, profile. (The legacy `arm_*` fields in
`result.json` and the `/arm:ro` mount are a frozen historical schema — see
ADR-0004 — not new vocabulary.)

**agent** (overloaded — disambiguate by context):
1. The CLI binary that runs a rep (`pi`, per Pier/upstream).
2. The coding agent under test, selected by `run_batch --agent {pi, omp}` and
   recorded on each rep's `agent` field. The thing a config configures.
Both senses are entrenched in the code. When ambiguous, say "the CLI" or "the
subject."

**model**:
The LLM a rep runs, paired with its reasoning budget. Advisor configs pair an
executor model with an advisor model, named `executor+advisor`.
_Avoid_: engine

**model-leaf**:
The path-identity of a model: the last `/`-segment of the model id (e.g.
`openrouter/deepseek/deepseek-v4-flash` → `deepseek-v4-flash`). The key a
model's reps accumulate under. Executor-only in the results tree; the
`exec+advisor` form appears only on the config leaf. Single-sourced by
`lib.model_leaf` so the harness and migrations derive it identically. Derivation
rules live in ADR-0001.

**thinking**:
The reasoning effort for the model. Choices: `off, minimal, low, medium, high,
xhigh`. Part of a config leaf's identity alongside the model.
_Avoid_: reasoning level, effort

**task**:
One DeepSWE task id. A corpus of 113 lives in the sibling
`~/evals/deep-swe/tasks/` checkout.
_Avoid_: instance, problem

**rep**:
A numbered repetition of one config on one task under a fixed
`(model-leaf, thinking)`. The atomic data unit: one rep is one agent run plus one
verifier grade. Reps accumulate under a config regardless of which subset
produced them. Its on-disk address is fixed by ADR-0001.
_Avoid_: trial

**cell**:
The on-disk container and address of one rep: the directory tree holding a rep's
outputs (`result.json`, `artifacts/`, `logs/`, `session/`, …). Distinct from
**rep** — rep is the run (the logical, numbered unit), cell is where its
artifacts live. Both share the identity `(model-leaf, thinking, config, task,
rep)`, fixed by ADR-0001. Entrenched in the code (`run_cell`, the
`-v {cell}:/out` mount, ~140 uses in `harness/*.py`); the results-tree address
module's `Cell` type is this concept. Don't use "cell" for the unit itself —
say rep.

**subset**:
A named selection of task ids used to scope a batch or a comparison — a
selection, never a storage location. Named `<size>_v<iteration>` (size as
primary sort, version as lineage) to avoid collision with thinking levels.
Conventionally nested by content (`12_v0 ⊂ 36_v1 ⊂ 113_v0`) so a wider batch
fills only new tasks; this nesting is a manual file convention, **not** enforced
or relied on by the harness — resume keys off existing reps, not subset
structure.
_Avoid_: subsample, slice, split

**baseline**:
The control config, produced once per `(model-leaf, thinking)` and reused by
every comparison under it. A minimum of 3 reps is recommended to even out noise.
The bare `baseline` is clean stock pi; `baseline-*` variants (e.g.
`baseline-preamble-orchestration`) are historical or controlled baselines, not
the canonical control — see ADR-0001.
_Avoid_: control group

**comparison**:
A paired evaluation of the baseline against one or more other configs over a
fixed `(model-leaf, thinking, subset)`. A comparison is a *view* over
already-existing reps, not raw data. Today it is a logical view realised by
`harness/analyze.py` over the results tree; the manifest-folder form described
in ADR-0001 is aspirational and not yet implemented (see ADR-0003).
_Avoid_: study, experiment

**run**:
Either a verb (to execute reps; `harness/run.py` runs one rep) or a noun for one
execution of `run_batch.py` — a live, resumable batch process identified by a
**run_id** and observed via the structured state under `results/_runs/<run_id>/`.
Distinct from a comparison (the analytical view) and a rep (the atomic unit).
The noun sense was re-introduced after ADR-0001; see ADR-0003.
_Avoid_: "run" for the analytical view (say comparison) or the atomic unit (say
rep).

**preflight** (a.k.a. smoke):
A one-cell gate that proves a config actually works at a `(model-leaf,
thinking)` before batch fan-out. Runs one rep on a smoke task and checks a
config-authored smoke contract. Failure stops the batch before any cell runs.
_Avoid_: smoke test (prefer preflight as the noun; "smoke" survives in
`smoke.json` contract filenames and the `SMOKE_SUBSET`).

**transient**:
A rep-killing provider error — a subscription **quota window** exhausted or a
short rate-limit — that is eligible for automatic wait-and-resume rather than
counted as a real failure. Signalled by exit 75 and the `transient_model_error`
field on the rep.

**quota window**:
A provider usage window (e.g. the OpenAI Codex 5h or weekly window) that, when
exhausted, blocks further reps until it resets. Read by `harness/quota.py` so a
paused run can sleep until the reset and resume on its own.
