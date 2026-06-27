# deep-swe-bench

A harness for measuring how pi coding-agent configuration choices affect
performance on real [DeepSWE](https://deepswe.datacurve.ai/) tasks. The model and
thinking level are held constant; one pi **config** is varied and compared
against a **baseline**.

Upstream vocabulary is shared with the [deep-swe](../deep-swe/) task corpus and
[Pier](https://github.com/datacurve-ai/pier) (a Harbor-compatible runner). This
repo owns one concept — **config** — that is a refinement of Pier's "agent" for
the single-agent case (this repo only ever runs one agent: `pi`).

## Language

**config**:
A pi coding-agent setup: the system-prompt addition (`orchestration.md`) plus
which skills/extensions load and any extra pi flags/env. The single variable a
comparison changes. `baseline` is the name of the control config — plain pi with
no skills, extensions, or special prompting.
_Avoid_: arm, treatment, variant, profile, agent (reserved for the CLI binary, per Pier)

**model**:
The LLM the agent runs, paired with its reasoning budget. A config carries a
leaf dir per model it supports; the leaf is immutable so it cannot be repurposed
into a different model. Advisor configs pair an executor model with an advisor
model, named `executor+advisor`.
_Avoid_: engine

**thinking**:
The reasoning effort level for the model. Choices: `off, minimal, low, medium,
high, xhigh`. Part of a config leaf's identity alongside the model.
_Avoid_: reasoning level, effort

**task**:
One DeepSWE task id. A corpus of 113 lives in the sibling
`~/evals/deep-swe/tasks/` checkout.
_Avoid_: instance, problem

**rep**:
A numbered repetition of one config on one task. The output of one rep lives at
`results/<model>/<thinking>/<config>/<task>/rep<N>/`. Reps are the atomic data
unit; there is no separate name for a single rep's output.
_Avoid_: cell, trial, run (reserved as a verb)

**subset**:
A named selection of task ids used to scope a batch or a comparison. Subsets are
selections, never storage locations — reps accumulate under a config regardless
of which subset produced them. Smaller subsets are defined as set-containment in larger ones
(`12_v0 ⊂ 36_v1 ⊂ 113_v0`) so a batch can expand a subset without re-running any
finished rep. Named `<size>_v<iteration>` (size as primary sort, version as
lineage) to avoid collision with thinking levels.
_Avoid_: subsample, slice, split

**baseline**:
The control config, produced once per `(model, thinking)` and reused by every
comparison under it. A minimum of 3 reps is recommended to even out noise.
_Avoid_: control group

**comparison**:
A paired evaluation of the baseline against one or more other configs, over a
fixed `(model, thinking, subset)`. A comparison is a view over already-existing
reps, not raw data: its folder holds only a manifest and generated analysis. Two
or more configs.
_Avoid_: study, experiment, run (reserved as a verb)

**run**:
A verb only: to execute reps. `harness/run.py` runs one rep. Never a noun.
_Avoid_: as a noun — use comparison for the batch entity, rep for the atomic unit
