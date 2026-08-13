# Subsamples

The harness supports `--subset subsets/<name>.txt` (one task id per line).

There are two families of nested subsamples, both valid for different jobs:

## Choosing a subsample

| family | subsamples | how tasks are picked | use it when |
|---|---|---|---|
| **signal-dense (hand-curated)** | `12_v0`, `36_v1` | tasks chosen for discriminative value across the arms under study (reproducer tasks, known wins/losses, cross-model headroom) | cheap directional pilots where you want maximum signal per task, and you are not publishing a cross-arm comparison that needs selection neutrality |
| **dataset-neutral (stratified)** | `12_v2`, `36_v2` | tasks chosen ONLY from task-intrinsic properties: language and cross-model pass-rate tercile. No arm outcome is ever consulted | publishable cross-arm comparisons, prompt optimization, thinking-level studies, anything where the optimizer/reader must not have peeked at arm outcomes |

Both families are nested (`12 ⊂ 36 ⊂ 113`) and reproducible. They overlap only by
chance. The signal-dense set is denser in known-discriminative tasks; the
dataset-neutral set reproduces the population's difficulty and language mix.

Selection-bias check against the 113-task population (mean cross-model pass
rate 49.5%):

| subsample | n | mean | Δ from pop | within-tercile drift |
|---|---|---|---|---|
| `36_v1` | 36 | 41.8 | -7.7 | picked the hard end of every bucket (-7.0 / -9.5 / -6.0) |
| `36_v2` | 36 | 49.2 | -0.3 | matches tercile means (+2.9 / -0.1 / +1.3) |
| `12_v0` | 12 | 55.2 | +5.7 | skews easy (2/4/6 H/M/E) |
| `12_v2` | 12 | 47.2 | -2.2 | balanced (4/5/3 H/M/E) |

The drift column is why the dataset-neutral family exists. `36_v1`'s tercile
counts look balanced (11/14/11) but inside each bucket it systematically picked
the harder, more discriminative tasks. That is fine for a pilot and a problem
for a neutral comparison.

## Signal-dense family: `12_v0` ⊂ `36_v1`

### Nesting: `12_v0` ⊂ `36_v1`

**`12_v0` (12 tasks) is fully contained in `36_v1` (36 tasks).**

Purpose: cheap, fast-iteration experiments on 12 tasks whose results expand
cleanly to the 36-task set without repeating any task. Run the 12 first; when
you expand to 36, the harness skips the 12 already-done cells and runs only the
24 new ones.

```
12_v0 (12) ──┐
                    ├──► 36_v1 (36)  [adds 24 tasks]
```

### `12_v0` — 12 tasks

| task | lang | why included |
|---|---|---|
| kgateway-consistent-hash-policy | go | **the clean wf win** (gpt-5.5: 0/3→3/3); policy/route generation |
| actionlint-action-pinning-lint | go | stable baseline solve (3/3); lint-rule addition; only near-bugfix task |
| anko-default-function-arguments | go | wf win (1/3→2/3); interpreter semantics |
| httpx-streaming-json-iteration | python | stable baseline solve (3/3); parser/iterator contract |
| fastapi-implicit-head-options | python | deepseek OM dramatic win (0→1); route/config inheritance |
| mashumaro-flattened-dataclass-fields | python | **floor rep** (gpt-5.5 0/0, deepseek 1.0); gives weak models signal |
| cattrs-partial-structuring-recovery | python | discrim (2/3→1/3); error-recovery structuring |
| awilix-async-container-initialization | ts | **strong baseline win** (3/3→1/3); async DI, wf regression |
| ts-pattern-match-each | ts | strong baseline win (3/3→1/3); pattern-matching compile |
| dynamodb-toolbox-lazy-recursive-schemas | ts | wf win (0/3→2/3); recursive schema builder |
| boa-hierarchical-evaluation-cancellation | rust | **cross-model wf/om win** (reproduces on gpt-5.5 AND deepseek); nested-eval cancellation |
| yjs-map-conflict-detection | javascript | only js signal task (3/3); CRDT conflict resolution |

### Design properties

- **Language coverage** proportional to v1: go 3 (25%), python 4 (33%), ts 3
  (25%), rust 1 (8%), js 1 (8%). v1 is go/py 31% each, ts 22%, rust 11%, js 6%.
  Rust is slightly under-represented (the other rust tasks are all 0-reward
  floor with no signal; `boa` is the highest-value one).
- **Signal-dense:** 11/12 are discriminative on gpt-5.5 (neither always-solved
  nor always-failed). One floor task (`mashumaro`) anchors the difficulty floor
  and gives weaker models (deepseek, qwen) measurable headroom.
- **Balanced wf/baseline signal:** 4 strong wf wins vs 2 strong baseline wins.
  (The raw count looks base-heavy at 7-vs-4, but 5 of those are 3/3→2/3
  near-ceiling single-test drops = noise, not real baseline favor. The 2 strong
  baseline wins are awilix and ts-pattern, both 3/3→1/3.)
- **Cross-model headroom:** 6/12 tasks have deepseek-v4-flash partial < 0.5
  (kgateway, anko-default, fastapi, mashumaro, ts-pattern, boa), so the set
  discriminates weak models too, not just gpt-5.5.
- **Contains the canonical reproducer tasks:** `boa` and `kgateway` are the two
  wf/om wins that reproduce across models and analyses — keeping them lets a
  12-task run confirm those signals cheaply.

### How to use

```sh
# cheap 12-task run (e.g. 3 reps × 1 config = 36 cells)
python3 harness/run_batch.py --configs <config> --subset 12_v0 \
  --model <model> --thinking <lvl> --runs 3 --workers 8

# later, expand to 36 without re-running any of the 12
python3 harness/run_batch.py --configs <config> --subset 36_v1 \
  --model <model> --thinking <lvl> --runs 3 --workers 8
# (harness skips cells with existing result.json, runs only the 24 new tasks)
```

**Important:** expansion only works if the 12-task run and the 36-task
expansion share the **same `--configs`, `--model`, `--thinking`, and rep
numbering**. The harness keys on `results/<model>/<thinking>/<config>/<task>/<rep>/result.json`.

## `36_v1` — 36 tasks (signal-dense)

The original fast-iteration subsample. Full list in `36_v1.txt`. Composed
of: go 11, python 11, typescript 8, rust 4, javascript 2; 34 feature_request,
1 bugfix, 1 enhancement.

## Dataset-neutral family: `12_v2` ⊂ `36_v2`

Tasks selected ONLY from task-intrinsic properties: language and cross-model
pass-rate tercile (from `data/deepswe-v1.1-task-difficulty.tsv`). No arm
outcome is consulted, so these subsamples are a neutral substrate for
comparing the very arms they were not selected on. Regenerate with
`subsets/make_stratified.py` (deterministic by `--seed`).

```
12_v2 (12) ──┐
              ├──► 36_v2 (36)  [adds 24 tasks] ──► 113 (full)
```

### `12_v2` — 12 tasks

| terciles | languages | mean pass rate | range |
|---|---|---|---|
| hard 4 / medium 5 / easy 3 | go 4, python 4, ts 4 | 47.2 | 16-83 |

The 12-task set cannot carry rust/javascript at population share (4% of 12 is
~0 slots), so it splits the three large languages evenly. Full list in
`12_v2.txt`.

### `36_v2` — 36 tasks

| terciles | languages | mean pass rate | range |
|---|---|---|---|
| hard 12 / medium 14 / easy 10 | go 11, ts 11, python 10, js 2, rust 2 | 49.2 | 4-91 |

Matches the 113-population mean (49.5) to within 0.3 points and reproduces the
population language mix (ts/go/py ~30% each, rust/js ~5% each). Full list in
`36_v2.txt`.

### How to use

```sh
python3 harness/run_batch.py --configs <config> --subset 12_v2 \
  --model <model> --thinking <lvl> --runs 3 --workers 8

# expand to 36 without re-running the 12 already done
python3 harness/run_batch.py --configs <config> --subset 36_v2 \
  --model <model> --thinking <lvl> --runs 3 --workers 8
```

Same expansion rule as the signal-dense family: share `--configs`, `--model`,
`--thinking`, and rep numbering so the harness skips completed cells.

## Regenerating the dataset-neutral family

`subsets/make_stratified.py` rebuilds `12_v2` and `36_v2` deterministically:

```sh
python3 subsets/make_stratified.py            # write 12_v2.txt, 36_v2.txt
python3 subsets/make_stratified.py --dry-run   # print allocation, write nothing
```

Within-cell order is a pure function of `(seed, slug)` via sha256, so the
output is stable regardless of Python dict ordering. Nesting (`12 ⊂ 36`) is
enforced by construction: the 12-task per-cell allocations are drawn as subsets
of the 36-task per-cell allocations. Change `--seed` to get a different
stratified draw with the same statistical properties; this is how you build a
fresh neutral subsample that does not overlap an existing one.

## Mechanism-diagnostic subset: `testing_skills_24_v0`

`testing_skills_24_v0` is an outcome-informed diagnostic subset for cumulative
changes to the `testing`, `property-based-testing`, and `fuzzing` skills. It
contains contract-observation sentinels, final-evidence and stopping cases,
property-testing opportunities, fuzzing opportunities, and negative controls.
It intentionally uses prior `testing-skills@1.1.0` trajectories to maximize
mechanism signal.

Use this subset to decide which wording mechanism merits a neutral or full-set
confirmation. Do not present its solve-rate delta as an unbiased estimate of
full-corpus efficacy.
