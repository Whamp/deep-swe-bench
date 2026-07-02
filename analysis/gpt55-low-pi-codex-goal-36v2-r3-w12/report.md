# GPT-5.5 low pi-codex-goal analysis — 36_v2 × 3 reps

Run: `results/gpt-5.5/low/pi-codex-goal`  
Tracker: `runs/pi-codex-goal-gpt55-low-36v2-r3-w12-rpc/track.out`  
Baseline: `results/gpt-5.5/low/baseline` on the same 36_v2 task/rep cells.

## Completion

- Paired cells analyzed: 108/108.
- Missing pairs: 0.
- Goal config timeouts: 0.
- Goal empty-patch/skipped verifier cells: 0.

## Verdict

`pi-codex-goal` substantially improved binary solves on this neutral 36-task slice, with a small positive mean-partial delta, while costing materially more.

- Solves: baseline 33/108 → pi-codex-goal 48/108 (+15).
- Mean partial: baseline 0.967469 → pi-codex-goal 0.973495 (+0.006026).
- Mean f2p delta: +0.052144.
- Mean p2p delta: +0.001026.
- Median combined tokens: baseline 608,190 → pi-codex-goal 1,732,978.
- Median combined cost: baseline $0.862 → pi-codex-goal $1.972.
- Total paired cost: baseline $102.03 → pi-codex-goal $240.25.
- Median wall: baseline 206.1s → pi-codex-goal 407.9s.

Paired uncertainty:

- Mean Δpartial: +0.006026.
- Bootstrap 95% CI: [-0.014109, +0.024521].
- Wilcoxon p: 0.053985658942171465.
- Solve flips: 24 positive vs 9 negative; binomial p: 0.013530986849218607.

## Effort / trajectory

| metric | baseline median | pi-codex-goal median | paired median delta |
|---|---:|---:|---:|
| combined tokens | 608,190 | 1,732,978 | +1,037,925 |
| combined cost | $0.862 | $1.972 | $+1.137 |
| wall time | 206.1s | 407.9s | +188.8s |
| turns | 38.0 | 61.0 | +20.5 |
| tool calls | 37.0 | 60.0 | +21.0 |
| patch bytes | 13,001 | 20,176 | +6,830 |

The goal package did not add separately-metered worker calls in `result.json`; `combined_* == total_*` for these cells. The cost increase is from the main executor trajectory.

## Task-level movement

Top task-level partial gains:

| task | baseline_solves | goal_solves | delta_solves | delta_mean_partial | delta_mean_cost |
|---|---|---|---|---|---|
| tengo-destructuring-bindings | 0 | 1 | 1 | 0.3214 | $2.049 |
| claude-code-by-agents-recursive-delegation | 2 | 3 | 1 | 0.0526 | $1.082 |
| textual-kitty-key-phases | 0 | 0 | 0 | 0.0458 | $1.293 |
| go-git-worktree-merge-conflicts | 0 | 0 | 0 | 0.0351 | $1.589 |
| eicrud-keyset-pagination-cursor | 0 | 2 | 2 | 0.0293 | $2.437 |
| updo-policy-alerting | 0 | 1 | 1 | 0.0190 | $1.043 |
| superjson-error-stack-serialization | 0 | 1 | 1 | 0.0136 | $0.620 |
| vulture-persistent-analysis-cache | 1 | 0 | -1 | 0.0136 | $0.771 |

Top task-level partial losses:

| task | baseline_solves | goal_solves | delta_solves | delta_mean_partial | delta_mean_cost |
|---|---|---|---|---|---|
| etree-xml-diff-patch | 0 | 0 | 0 | -0.2488 | $0.526 |
| katex-multicolumn-array-spans | 0 | 0 | 0 | -0.0486 | $0.681 |
| go-critic-doc-link-checker | 2 | 1 | -1 | -0.0351 | $0.523 |
| fastapi-deprecation-response-headers | 2 | 0 | -2 | -0.0111 | $1.367 |
| fd-deterministic-multi-key-sorting | 0 | 0 | 0 | -0.0066 | $0.820 |
| pest-character-class-coalescing | 0 | 1 | 1 | -0.0047 | $1.355 |
| koota-query-predicates | 0 | 0 | 0 | -0.0031 | $2.282 |
| meriyah-explicit-resource-declarations | 0 | 0 | 0 | -0.0001 | $1.450 |

Solve gains: updo-policy-alerting, superjson-error-stack-serialization, pest-character-class-coalescing, dateutil-rfc5545-timezone-interop, mashumaro-flattened-dataclass-fields, eicrud-keyset-pagination-cursor, claude-code-by-agents-recursive-delegation, mobly-grouped-test-barriers, tengo-destructuring-bindings, scc-bounded-memory-spilling, dynamodb-toolbox-conditional-attribute-requirements, adaptix-name-mapping-aliases, yjs-map-conflict-detection, actionlint-action-pinning-lint, sql-formatter-bigquery-pipe-formatting, psd-tools-blend-range-api.

Solve losses: vulture-persistent-analysis-cache, go-critic-doc-link-checker, fastapi-deprecation-response-headers.

## Interpretation

The durable-goal wrapper produced the clearest solve-rate lift we have seen so far on GPT-5.5 low 36_v2, but it did so by making the executor work much longer. The binary solve signal is stronger than the partial-reward signal: many cells were already near the partial ceiling, so extra completion discipline can convert threshold failures into full solves without moving mean partial very much.

Because this run is complete and mechanically clean, it is valid as a positive-but-expensive result for `pi-codex-goal` on GPT-5.5 low 36_v2. Before scaling, the next useful question is qualitative: inspect gained-solve and lost-solve traces to see whether goal continuation helped by forcing final verification/closure, or whether the win is mostly extra time/turns/cost.
