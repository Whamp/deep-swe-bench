# Why pi-observational-memory likely improved DeepSWE outcomes

Sources: paired manifest `runs/om-memory-pilot-w10/reports/paired_manifest.json`, report directory `runs/om-memory-pilot-w10/reports`, and run artifacts under `runs/om-memory-pilot-w10/pi-observational-memory/*/rep0/`. The comparison uses `rep0` for 113 task pairs and reuses the baseline from `runs/ponytail-full-pilot-w2/baseline`.

## Executive summary

`pi-observational-memory` raised mean partial reward from `0.774167` to `0.856332`: a `+0.082166` absolute lift, or `10.6%` relative. Binary solves rose from `2/113` to `10/113`. Row-level partial reward improved on `69` tasks, regressed on `33`, and tied on `11`.

The lift came from hard, cross-file tasks. Hard rows moved from `0.401454` to `0.709870` (`+0.308417`), with `26/38` hard rows improving. Medium and easy buckets gained binary solves, but their means fell because a few near-ceiling tasks missed one integration seam and lost heavily.

The mechanism is probably persistence, not magic. The OM loop ran on every row: `774` `observer.start` events, `799` reflector starts/results, and `698` dropper waits. Successful hard rows tended to carry more observations into broader, more test-heavy patches; cheap wins show the same system can also compress redundant search when it finds the shared seam earlier.

This was not a cost win. OM used fewer tokens on only `24/113` rows, lower direct cost on `33/113`, and lower wall time on `41/113`. Median totals moved from `3,291,131` to `5,454,728` tokens, `57` to `80` turns, and `776.4s` to `929.2s` wall time. The manifest excludes OM worker-model overhead as a separate cost column, so the full-system cost is higher than the agent-side numbers alone show.

## API-error audit result

I found no evidence that provider/API false failures explain the outcome. Public framing and manifest checks show zero nonzero agent exits and zero agent timeouts. The only nonzero OM verifier outcomes were `boa-hierarchical-evaluation-cancellation` (`timeout`) and `opa-rego-rule-profiling` (`skipped_empty_patch`); both are benchmark outcomes, not provider/API failures.

The real internal issue is a stale extension-context worker error in `22/113` tasks: `9` `observer.error` events and `13` `reflector.error` events with the same `ctx is stale after session replacement or reload` message. It was not a strong failure signal: stale-error rows were `15` wins, `5` losses, and `2` ties, with mean partial delta `+0.078` versus `+0.083` on no-error rows. Treat it as recoverable overhead and a lifecycle bug to fix, not as the main reason OM won or lost.

## Headline metrics

| metric | baseline | OM | delta / note |
|---|---:|---:|---:|
| pairs | 113 | 113 | rep0 only |
| mean partial reward | 0.774167 | 0.856332 | +0.082166 |
| relative mean partial lift | — | — | 10.6% |
| binary solves | 2/113 | 10/113 | +8 solves |
| partial rows | — | — | 69 improved / 33 worse / 11 tied |
| median total tokens | 3,291,131 | 5,454,728 | median Δ 1,830,763 |
| median turns | 57 | 80 | median Δ +20 |
| median wall time | 776.4s | 929.2s | median Δ +144.2s |
| median tool-call delta | — | — | +21 |
| median patch-byte delta | — | — | 5,025 |

Top gains:

| task | bucket | baseline partial | OM partial | Δpartial | Δtokens |
|---|---|---:|---:|---:|---:|
| `mashumaro-flattened-dataclass-fields` | hard | 0.000000 | 0.999668 | +0.999668 | +7,792,399 |
| `fastapi-implicit-head-options` | hard | 0.000315 | 0.997167 | +0.996852 | +20,581,688 |
| `kombu-single-active-consumer-priority` | hard | 0.000000 | 0.992696 | +0.992696 | +10,508,933 |
| `anko-default-function-arguments` | hard | 0.000000 | 0.991736 | +0.991736 | +4,958,124 |
| `kgateway-consistent-hash-policy` | hard | 0.000000 | 0.990741 | +0.990741 | +7,598,262 |
| `sqlite-utils-safe-import-checkpoints` | hard | 0.000000 | 0.970856 | +0.970856 | +3,325,338 |
| `ts-pattern-match-each` | hard | 0.065934 | 0.989011 | +0.923077 | -894,160 |
| `oxvg-structural-selector-preservation` | hard | 0.000000 | 0.911765 | +0.911765 | +11,449,771 |
| `go-critic-doc-link-checker` | hard | 0.000000 | 0.894737 | +0.894737 | +2,269,028 |
| `helm-array-merge-strategies` | hard | 0.000000 | 0.762712 | +0.762712 | +5,434,670 |

Top losses:

| task | bucket | baseline partial | OM partial | Δpartial | Δtokens |
|---|---|---:|---:|---:|---:|
| `adaptix-name-mapping-aliases` | easy | 0.998562 | 0.000000 | -0.998562 | -19,855,300 |
| `cattrs-partial-structuring-recovery` | medium | 0.947368 | 0.131579 | -0.815789 | -2,461,302 |
| `opa-rego-rule-profiling` | hard | 0.580645 | 0.000000 | -0.580645 | -3,264,593 |
| `etree-xml-diff-patch` | hard | 0.791045 | 0.253731 | -0.537313 | +1,932,206 |
| `igel-persist-feature-schema` | hard | 0.576923 | 0.076923 | -0.500000 | +5,859,599 |
| `task-task-graph-export` | medium | 0.837838 | 0.540541 | -0.297297 | +3,211,156 |
| `dasel-html-document-format` | easy | 0.992228 | 0.697755 | -0.294473 | +133,749 |
| `abs-stepped-slices` | hard | 0.666667 | 0.416667 | -0.250000 | -5,525,069 |
| `go-git-worktree-merge-conflicts` | hard | 0.736842 | 0.526316 | -0.210526 | +1,896,650 |
| `kcp-go-multiplexed-kcp-streams` | hard | 0.523810 | 0.333333 | -0.190476 | +1,389,870 |

## Difficulty-bucket interpretation

| bucket | n | baseline mean | OM mean | mean Δ | median Δ | solves | improved / worse / tie | median Δtokens | median Δwall | median Δturns |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hard | 38 | 0.401454 | 0.709870 | +0.308417 | +0.220681 | 0→1 | 26 / 9 / 3 | +4,140,185 | +262.3s | +38.5 |
| medium | 37 | 0.934380 | 0.912542 | -0.021838 | +0.010309 | 0→4 | 24 / 10 / 3 | +1,330,316 | +139.3s | +16.0 |
| easy | 38 | 0.990884 | 0.948064 | -0.042819 | +0.000119 | 2→5 | 19 / 14 / 5 | +1,597,302 | +73.6s | +13.5 |

Hard tasks start far from the ceiling and often require API, runtime, generated artifact, fixture, and test changes to agree. OM improved this bucket because remembered observations helped maintain one hypothesis across those layers. The hard patch-shape signal matches the story: hard mean patch files rose from `5.05` to `7.37`, test files from `0.68` to `1.45`, and generated files from `0.05` to `0.63`; empty hard baseline patches fell from `4/38` to `1/38`.

Medium and easy rows were near the ceiling. Their medians were flat to slightly positive (`+0.010309` for medium, `+0.000119` for easy), but the means fell because one or two large regressions dominated each bucket. The common miss was not a harness crash; it was a seam miss: export/compat shim, CLI registration, shared symbol, generated artifact, or required test file.

## Success-mode buckets

| mode | count | read | examples |
|---|---:|---|---|
| New full solves | 8 | baseline.reward_binary != 1 and om.reward_binary == 1 | `eicrud-keyset-pagination-cursor`, `helm-unified-manifest-stream`, `textual-richlog-follow-state`, `fd-deterministic-multi-key-sorting` |
| Baseline pathology rescues | 4 of 5 | empty/timed-out/pathological baselines rescued; wasmi was the miss | `anko-default-function-arguments`, `kgateway-consistent-hash-policy`, `oxvg-structural-selector-preservation`, `kombu-single-active-consumer-priority` |
| Hard-task partial jumps | 4 marquee; 26 hard rows improved >0.05 overall | large hard-bucket jumps from broken or incomplete baselines | `mashumaro-flattened-dataclass-fields`, `fastapi-implicit-head-options`, `kombu-single-active-consumer-priority`, `anko-default-function-arguments` |
| Cheap-or-efficient wins | 13 | strict wins/ties with lower total_tokens and tool_calls; 21 cheaper matches total | `ts-pattern-match-each`, `pebble-durability-wait-apis`, `fd-deterministic-multi-key-sorting`, `actionlint-action-pinning-lint` |
| Integration-completeness wins | 7 | curated cross-layer / fixture / golden regeneration wins | `koota-pair-relation-tracking`, `fastapi-implicit-head-options`, `yaegi-go-embed-directives`, `helm-unified-manifest-stream` |

The best examples are cross-file repairs. `kgateway-consistent-hash-policy` went from an empty baseline to API, CRD, deepcopy, plugin, translator, and fixture-test wiring. `helm-unified-manifest-stream` closed a `0.714286 → 1.0` gap by unifying manifest rendering and updating CLI goldens. `fastapi-implicit-head-options`, while not a binary solve, shows the same pattern: OM carried the HEAD/OPTIONS idea through app, routing, middleware, and OpenAPI code instead of stopping at one local route fix.

The cheap wins matter because they separate memory from raw spending. `ts-pattern-match-each`, `pebble-durability-wait-apis`, `fd-deterministic-multi-key-sorting`, and `returns-validated-error-accumulation` improved while reducing tokens and tool calls. In those rows, memory likely compressed the trajectory: it did not make the patch tiny, but it got to the right integration surface earlier.

## Regression-mode buckets

| mode | n | examples | read |
|---|---:|---|---|
| API / extension errors | 3 | `adaptix-name-mapping-aliases`, `cattrs-partial-structuring-recovery`, `igel-persist-feature-schema` | public API/export/extension seam broke or stayed hidden |
| Missed integration | 3 | `task-task-graph-export`, `go-git-worktree-merge-conflicts`, `happy-dom-deterministic-intersectionobserver` | baseline touched a companion/shared file OM skipped |
| Memory distraction / over-expansion | 6 | `dasel-html-document-format`, `optique-conditional-option-dependencies`, `ink-grid-box-layout`, `bandit-interprocedural-taint-checks` | patch widened into nearby plumbing/tests/examples without closing the contract |
| Normal model variance | 4 | `etree-xml-diff-patch`, `abs-stepped-slices`, `kcp-go-multiplexed-kcp-streams`, `onedump-dump-encryption-pipeline` | same surface, hidden edge case still failed |
| Too much context / stalled exploration | 1 | `opa-rego-rule-profiling` | search-only run emitted empty patch |
| Tooling / env | 1 | `quill-shared-toolbar-focus` | xvfb-run failed because xauth was missing; do not count as model reasoning failure |

Across the 18 largest losses, breadth mistakes dominate: `12/18` are wiring/breadth-related (`API / extension`, `missed integration`, or `over-expansion`). The two main shapes are opposites. OM sometimes stopped too narrow, as in `adaptix-name-mapping-aliases` skipping `loader_provider.py`, `overlay_schema.py`, and the baseline tests. It sometimes broadened into the wrong layer, as in `cattrs-partial-structuring-recovery` adding a large `src/cattrs/partial.py` abstraction but missing the top-level `cattrs.partial_structure` API. `opa-rego-rule-profiling` is the clean stalled-search failure: `patch_bytes=0` and `verifier_exit=skipped_empty_patch`.

`quill-shared-toolbar-focus` should stay out of model-mode conclusions. Its trace hit `xvfb-run: xauth command not found`, so it is an environment/tooling failure, not evidence that OM reasoning regressed.

## Cost and latency tradeoff

OM bought quality with more main-session iteration. Median deltas were `1,830,763` tokens, `$0.059`, `+144.2s`, `+20` turns, `+21` tool calls, and `5,025` patch bytes. The median OM patch changed `6` files and `15` hunks.

Token growth tracks iteration far more than patch breadth:

| predictor vs token delta | Pearson r | Spearman ρ |
|---|---:|---:|
| turns | 0.96 | 0.95 |
| tool_calls | 0.95 | 0.93 |
| file_count | 0.21 | 0.22 |
| hunks | 0.27 | 0.25 |
| patch_bytes | 0.09 | 0.38 |

Iteration-depth bins show the same pattern: 0-9 turn delta: 732,414 (12 rows), 10-19 turn delta: 1,597,302 (18 rows), 20-39 turn delta: 2,588,375 (24 rows), 40-99 turn delta: 7,098,020 (24 rows), 100+ turn delta: 16,719,458 (9 rows). File-count bins move less: 0-4 OM patch files: 1,653,625 (37 rows), 5-7 OM patch files: 1,825,756 (40 rows), 8-12 OM patch files: 2,308,128 (21 rows), 13+ OM patch files: 3,069,593 (15 rows). Broad patches can be cheap (`dynamodb-toolbox-lazy-recursive-schemas`: 39 files, +2 turns, -887,590 tokens), and narrow patches can be expensive (`sqlfmt-create-table-ddl-formatting`: 3 files, +80 turns, +11,599,323 tokens).

The expensive wins are still informative. `fastapi-implicit-head-options` cost +20.6M tokens but found a shared app/routing/OpenAPI/middleware seam. `yaegi-go-embed-directives` cost +17.6M tokens but added interpreter support plus embed fixtures. `helm-unified-manifest-stream` cost +11.36M tokens because it regenerated many golden outputs. The Koota rows are the warning case: high search/edit churn, no visible test loop, and modest partial gains.

## Plausible mechanism

OM likely helped in three concrete ways.

1. **Constraint persistence.** Observations and reflections kept requirements alive after long searches and test failures. That matters for tasks where one invariant must be threaded across API, runtime, generated files, fixtures, and tests.
2. **Search compression.** On some rows, reflections appear to prevent rediscovering the same seam. `ts-pattern-match-each` and `pebble-durability-wait-apis` improved while using fewer turns and tool calls.
3. **Integration checklist effect.** Hard wins often added tests, snapshots, generated files, or golden outputs. Memory seems to help the agent remember that the feature is not complete until the adjacent artifacts move too.

The same mechanism can hurt. If reflections preserve the wrong layer, OM can over-expand. If observations never force a transition from search to edit, OM can emit an empty patch. If the task only needs one small public seam, extra memory may add noise instead of signal.

## What remains uncertain

- This is one paired replay, `rep0` only; there is no variance estimate.
- The baseline was reused from `runs/ponytail-full-pilot-w2/baseline`, not freshly rerun under the same date and environment.
- Memory is confounded with budget. OM usually used more turns, tokens, tools, and wall time, so the result does not isolate memory from extra search.
- OM worker-model costs are excluded as a separate cost column. Do not present this as full-system cost accounting.
- Stale-context worker errors affected `22/113` tasks. They did not predict failure here, but they are still a real lifecycle bug.
- Hidden verifier exactness still matters: several `0.99+` near-solves missed one callback schema, nested-path, or flattening edge.
- We have event counts, but only limited semantic auditing of the actual reflection contents. A raw trace spot-check would show whether reflections named the missing seams or merely summarized local test output.

## Recommended next analyses and assets

1. **Matched-budget ablation.** Run the same model and task set with OM off but the same token/turn cap. This is the cleanest way to separate memory from budget.
2. **Multi-rep replay.** Add at least 3–5 reps for the paired set, with fresh baselines, to estimate variance and confidence intervals.
3. **Baseline-vs-OM scatter.** Plot baseline partial vs OM partial, color by difficulty, include a 45° line, and label the top wins/losses.
4. **Sorted delta waterfall.** Show per-task `Δpartial` from biggest gain to biggest loss, with hard rows highlighted.
5. **Tradeoff scatter.** Plot `Δpartial` vs `Δtokens` or `Δwall_s`; annotate cheap wins and expensive wins.
6. **Seam taxonomy table.** For regressions, list the missing seam type: export/compat, CLI registration, shared symbol, generated artifact, test/golden, hidden-edge logic.
7. **Stale-context table.** Group the 22 stale-error tasks by win/loss/tie to show the lifecycle bug is mostly orthogonal to benchmark outcome.
8. **Reflection-content audit.** Sample top wins/losses and check whether reflections explicitly mention the decisive file or only restate local errors.
9. **Cadence/pruning ablation.** Try fewer reflection cycles or a final smoke-test checklist for public APIs, CLI registrations, generated artifacts, and exported symbols.
