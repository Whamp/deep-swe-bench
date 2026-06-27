# Subsamples

The harness supports `--subsample harness/subsamples/<name>.txt` (one task id per line).

## Nesting: `12_v0` ⊂ `36_v1`

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
# cheap 12-task run (e.g. 3 reps × 1 arm = 36 cells)
python3 harness/run_batch.py --arms <arm> --subsample 12_v0 \
  --run-name <run> --model <model> --thinking <lvl> --runs 3 --workers 8

# later, expand to 36 without re-running any of the 12
python3 harness/run_batch.py --arms <arm> --subsample 36_v1 \
  --run-name <run> --model <model> --thinking <lvl> --runs 3 --workers 8
# (harness skips cells with existing result.json, runs only the 24 new tasks)
```

**Important:** expansion only works if the 12-task run and the 36-task
expansion share the **same `--run-name`, `--arms`, `--model`, `--thinking`,
and rep numbering**. The harness keys on `runs/<run>/<arm>/<task>/<rep>/result.json`.

## `36_v1` — 36 tasks

The original fast-iteration subsample. Full list in `36_v1.txt`. Composed
of: go 11, python 11, typescript 8, rust 4, javascript 2; 34 feature_request,
1 bugfix, 1 enhancement.
