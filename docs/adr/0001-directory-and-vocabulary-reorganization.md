# 0001 — Directory and vocabulary reorganization

## Context

The original layout overloaded three words as nouns — "arm" (clinical-trial
baggage), "run" (a verb that also named the output directory), and "subsample"
(diverged from upstream Pier's "subset") — and let the model+thinking vary
mutably inside a config dir. The mutability caused a real incident: two baseline
dirs were repurposed from DeepSeek to Qwen, silently invalidating every older
comparison that referenced them and breaking resume.

A naming/structure pass was grilled to a close. This ADR records the resulting
layout so the next reader (or agent) doesn't re-litigate it.

## Decision

Adopt the canonical nouns in `CONTEXT.md` (config, model, thinking, task, rep,
subset, comparison, baseline) and reorganize the tree so every axis is an
explicit path component, not an in-memory assumption.

```
configs/<config>/{<constant pi setup files>}              # was arms/
configs/<config>/<model-leaf>/<thinking>/models.json       # non-advisor leaf, immutable
configs/<config>/<exec>+<advisor>/<thinking>/{models.json,advisor.json}   # advisor leaf, immutable

subsets/<N>.txt                                           # was harness/subsamples/

results/<model-leaf>/<thinking>/<config>/<task>/rep<N>/result.json   # was runs/
results/<model-leaf>/<thinking>/comparisons/<name>/{manifest.json,analysis.md}
```

**`<model-leaf>` is executor-only.** It is the last `/`-segment of the executor
`model` (e.g. `deepseek-v4-flash`), computed by `lib.model_leaf(model)`. The
`<exec>+<advisor>` form appears ONLY in the configs leaf, never in the results
path — so a resumed `run_batch`, which receives only the executor `--model`,
can recompute the same results path migrate wrote.

Three structural commitments:

1. **Config leaf is immutable.** Each `(config, model, thinking)` is its own
   dir. You cannot mutate one model into another — the resume incident cannot
   recur.
2. **Model+thinking live in the path.** Results under one model+thinking are a
   different tree from another. Identity is structural, not remembered.
3. **Subset is a selection, not a location.** Reps accumulate under a config and
   span every subset ever run. Subsets are prefix-nested (`12 ⊂ 36 ⊂ 113`) so
   `run_batch --subset 36` after `--subset 12` fills only the new tasks. The
   harness resumes by existence-checking `result.json`, not by reading subset
   nesting — prefixing is a file convention that makes "expand" literal.

## Considered options

- **Subset in the path** (`results/<model>/<thinking>/<subset>/...`): rejected.
  It breaks nesting-resume — smaller and larger subsets would hold disjoint
  copies of the overlapping tasks, defeating the whole point of subset-nesting.
  Subset stays a selection.
- **One global `runs/` tree keyed by `--run-name`** (status quo): rejected. Free
  text (`-w2`, `-sub`, `-pilot`, `-rerun`) encoded run parameters in the name,
  and resume was unsafe because the name didn't pin model+thinking.
- **Adjective subset names** (`small`/`medium`/`full`): rejected. `medium` is
  already a thinking level (`off..xhigh`), so `--thinking medium --subset medium`
  would be valid and meaningless. Subsets are named by task count instead.
- **Clinical-trial vocabulary** (arm/study/cell): rejected by the operator as
  non-native. `config`/`comparison`/`rep` replaced it.

## Consequences

- `harness/run.py --arm` becomes `--config`; `--run-name` is replaced by the
  `results/<model>/<thinking>/<config>/` path derived from the inputs.
- `run_batch.py --arms` becomes `--configs`; `--subsample` becomes `--subset`.
- `analyze.py --run` is replaced by `--comparison` (pointing at a
  `results/<model>/<thinking>/comparisons/<name>/manifest.json`) plus the model
  and thinking it sits under.
- Existing `arms/` and `runs/` are migrated by a script (see RENAME-PLAN.md):
  per-config files are split into config-constant and model-leaf trees; existing
  results are regrouped by `(model, thinking)` from their `result.json` `model`
  field. Older batch log files (`*.out`, `*.pid`, `*.sh`) are archived, not
  migrated into the new layout.
- The `models.json` migration needs care: the old arms sometimes mutated
  `baseline/` across model changes. Each `(config, model)` leaf is materialized
  from the `model` recorded in that rep's `result.json` plus the matching
  provider config, not trusted from the current state of `arms/`.
- `baseline-wf` is a distinct config from `baseline`. The two are compared to
  decide which to standardize on; the structure makes no commitment and lets both
  coexist under the same `(model, thinking)`. `baseline` keeps the clean name and
  is the no-prompt control; `baseline-wf` carries the benchmark-specific workflow
  prompt.
