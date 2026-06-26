# Difficulty causal analysis: why OM helped hard tasks but hurt medium/easy

Source set: `runs/om-memory-pilot-w10/reports/paired_manifest.json`, `runs/om-memory-pilot-w10/reports/initial_summary.md`, `runs/om-memory-pilot-w10/reports/pair_0_top_wins.md`, `runs/om-memory-pilot-w10/reports/pair_1_top_losses.md`, `runs/om-memory-pilot-w10/reports/pair_3_pathology_rescues.md`, `runs/om-memory-pilot-w10/reports/pair_4_hard_bucket_wins.md`, `runs/om-memory-pilot-w10/reports/pair_5_medium_easy_regressions.md`.

## Bottom line

OM observational memory seems to help when the task is **deep, stateful, and cross-file**, because it preserves a hypothesis long enough to stitch together the missing seam and verify it.
It tends to hurt on **near-solved medium/easy tasks**, because the benchmark has little headroom left: a single missed integration file, export path, or validation seam can erase a small gain, and the memory loop can keep the agent exploring the wrong layer instead of locking onto the final contract.

## Bucket metrics

From `paired_manifest.json` and `initial_summary.md`:

| bucket | n | baseline mean_partial | OM mean_partial | delta | baseline solves | OM solves |
|---|---:|---:|---:|---:|---:|---:|
| hard | 38 | 0.401454 | 0.709870 | **+0.308417** | 0 | 1 |
| medium | 37 | 0.934380 | 0.912542 | -0.021838 | 0 | 4 |
| easy | 38 | 0.990884 | 0.948064 | -0.042819 | 2 | 5 |

Distribution matters:

- hard: 26 improved / 9 worse / 3 tie; median delta `+0.220681`
- medium: 24 improved / 10 worse / 3 tie; median delta `+0.010309`
- easy: 19 improved / 14 worse / 5 tie; median delta `+0.000119`

So medium/easy are not uniformly worse; the mean is dragged down by a few severe regressions.

## Why hard improves

Hard rows have more latent structure to recover:

- baseline is often empty or broken (`4/38` hard rows had empty baseline patches; OM reduced that to `1/38`)
- OM patches are broader and more test-heavy
  - hard baseline mean patch files `5.05` → OM `7.37`
  - hard baseline mean test files `0.68` → OM `1.45`
  - hard baseline mean generated files `0.05` → OM `0.63`
- OM also shows more reflection cycles on hard wins than hard losses
  - improved hard rows: observer mean `8.35`, reflector mean `9.31`
  - regressed hard rows: observer mean `5.33`, reflector mean `4.78`

Representative wins:

- `mashumaro-flattened-dataclass-fields` (`runs/om-memory-pilot-w10/pi-observational-memory/mashumaro-flattened-dataclass-fields/rep0/artifacts/model.patch`)
  - baseline was a 3-file patch; OM added `tests/test_flatten.py`
  - baseline was syntactically broken; OM fixed `mashumaro/core/meta/code/builder.py`, `mashumaro/helper.py`, and tests
- `fastapi-implicit-head-options` (`runs/om-memory-pilot-w10/pi-observational-memory/fastapi-implicit-head-options/rep0/artifacts/model.patch`)
  - OM propagated `auto_head` / `auto_options` through `fastapi/applications.py`, `fastapi/routing.py`, `fastapi/middleware/__init__.py`, and `fastapi/openapi/utils.py`
  - validation reached real behavior (`TestClient().options(...)` in the trace per `pair_4_hard_bucket_wins.md`)
- `kgateway-consistent-hash-policy` (`runs/om-memory-pilot-w10/pi-observational-memory/kgateway-consistent-hash-policy/rep0/artifacts/model.patch`)
  - baseline was empty
  - OM added API types, deepcopy generation, CRD YAML, plugin code, and tests across 15 files
- `anko-default-function-arguments` (`runs/ponytail-full-pilot-w2/baseline/anko-default-function-arguments/rep0/artifacts/model.patch` vs OM)
  - baseline empty; OM carried default arguments through parser, AST, VM, and tests

Interpretation: hard tasks reward memory because the agent must hold onto a hypothesis while traversing multiple layers (API/schema/codegen/runtime/tests) and revisit earlier findings after each edit.

## Why medium/easy hurt

Medium/easy tasks already start near the ceiling, so the main failure mode is not “no solution” but “miss one indispensable seam.”
That makes the score fragile: a small local mistake can turn a nearly-solved row into a big regression.

The mean loss is concentrated in a few rows:

- medium: top 1 loss (`cattrs-partial-structuring-recovery`) explains ~50% of all negative medium delta; top 3 explain ~79%
- easy: top 1 loss (`adaptix-name-mapping-aliases`) explains ~58% of all negative easy delta; top 3 explain ~84%

Representative regressions:

- `adaptix-name-mapping-aliases` (`runs/om-memory-pilot-w10/pi-observational-memory/adaptix-name-mapping-aliases/rep0/artifacts/model.patch`)
  - baseline touched `loader_provider.py`, `overlay_schema.py`, and two tests
  - OM kept alias/name-mapping logic in code, but dropped the baseline test files and the overlay-schema seam
  - result: `0.999 -> 0.000` partial
- `cattrs-partial-structuring-recovery` (`runs/om-memory-pilot-w10/pi-observational-memory/cattrs-partial-structuring-recovery/rep0/artifacts/model.patch`)
  - OM moved the feature into a new `src/cattrs/partial.py` and added `PartialResult`
  - but it missed the compatibility/export path in `src/cattr/converters.py` that the baseline had extended
  - result: `0.947 -> 0.132` partial
- `task-task-graph-export` (`runs/om-memory-pilot-w10/pi-observational-memory/task-task-graph-export/rep0/artifacts/model.patch`)
  - OM skipped `errors/errors_task.go`, the shared error seam baseline used
- `dasel-html-document-format` (`runs/om-memory-pilot-w10/pi-observational-memory/dasel-html-document-format/rep0/artifacts/model.patch`)
  - OM spent effort in `parsing/html/*` and tests, but skipped `cmd/dasel/main.go`, the CLI registration seam
- `onedump-dump-encryption-pipeline` (`runs/om-memory-pilot-w10/pi-observational-memory/onedump-dump-encryption-pipeline/rep0/artifacts/model.patch`)
  - same breadth, but still missed the header/validation edge case

Interpretation: memory can keep search alive too long on near-solved rows, and that can bias the agent toward a plausible-but-wrong adjacent layer instead of the exact integration file that decides the benchmark.

## Task traits: useful vs harmful

### Memory is useful when the task has:

- **cross-file state propagation**: one concept must be threaded through API, runtime, and tests
- **generated or derived artifacts**: deepcopy, CRD YAML, OpenAPI, snapshots, fixtures
- **long hypothesis chains**: the fix is not local, and later edits need earlier findings preserved
- **baseline incompleteness**: empty patch, broken patch, or obvious missing coverage
- **verification loops**: success depends on repeating test/trace feedback after each stage

Examples: `mashumaro-flattened-dataclass-fields`, `fastapi-implicit-head-options`, `kgateway-consistent-hash-policy`, `anko-default-function-arguments`.

### Memory is harmful when the task has:

- **one narrow integration seam**: export file, CLI registration, compat shim, shared symbol, or test file
- **high baseline partial**: there is little room to improve, so any miss dominates the mean
- **many plausible nearby fixes**: memory can over-anchor on the wrong layer
- **light validation needs**: if the right answer is small, extra exploration mostly adds noise

Examples: `adaptix-name-mapping-aliases`, `cattrs-partial-structuring-recovery`, `task-task-graph-export`, `dasel-html-document-format`.

## Causal read

The cleanest explanation is:

1. **Hard tasks** benefit from memory because they need sustained multi-step reasoning across files, and OM preserves intermediate discoveries long enough to finish the wiring and tests.
2. **Medium/easy tasks** are already close to solved, so OM’s extra search mostly changes *where* the agent looks, not *whether* it can find a fix.
3. On those near-ceiling rows, the dominant failure is a **missed seam** or **wrong layer**, which causes a large score drop that outweighs small wins.

## Caveat

This is still correlational, not a clean ablation.
OM usually used more turns/tokens than baseline, so memory is confounded with extra search budget and time.
But the file-level examples line up with the metric shape: hard wins are multi-file integration repairs; medium/easy losses are seam misses or over-scoped fixes.
