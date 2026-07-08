# OMP vs Pi harness — 36_v2 (gpt-5.5 low)

Re-run of the harness-vs-harness comparison on the larger, arm-independently-stratified
**36_v2** subset (108 cells/arm), to test whether the 12_v2 findings hold.

## Headline

The **token-efficiency story holds robustly**; the **solve-rate story did not**.
On 36_v2 OMP produces equivalent quality at 2.2× cost — the 12_v2 solve gap was
small-sample noise, the token-inefficiency gap is a real systematic harness property.

| metric (median/cell, 108 paired) | Pi `baseline` | OMP `baseline-omp` | ratio |
|---|--:|--:|--:|
| solves | 33 | 36 | OMP +3 |
| mean_partial | 0.9675 | 0.9694 | tied |
| cost | $0.8617 | $1.8697 | **2.17×** |
| total_tokens | 608,190 | 2,133,626 | **3.50×** |
| cacheRead_tokens (sum) | 70.9M | 248.6M | **3.50×** |
| assistant_turns (sum) | 4,291 | 6,096 | 1.42× |
| tool_calls (sum) | 4,193 | 6,337 | 1.51× |
| tool_result_bytes (sum) | 9.76M | 16.68M | 1.71× |
| wall (median) | 206s | 297s | 1.44× |
| total cost | $102.03 | $226.93 | 2.22× |

Per-turn harness overhead is constant at **7968 tokens/turn** (one outlier, langchain-request-coalescing at 10685, koota at 8233) — identical to 12_v2.

## 12_v2 vs 36_v2 — does the story hold?

| metric | 12_v2 (36 cells) | 36_v2 (108 cells) | verdict |
|---|---|---|---|
| solves Pi/OMP | 11 / 9 (−2) | 33 / 36 (+3) | **flipped** (noise) |
| mean_partial | 0.974 / 0.954 | 0.968 / 0.969 | tied on both, but sign flipped |
| turns ratio | 1.37× | 1.42× | holds |
| tool_calls ratio | 1.43× | 1.51× | holds |
| tool_failures ratio | 1.08× | 1.24× | holds |
| cacheRead ratio | 3.20× | 3.50× | holds |
| input ratio | 1.67× | 1.64× | holds |
| tool_result_bytes ratio | 1.73× | 1.71× | holds |
| overhead tok/turn | 7968 | 7968 | identical |

Every efficiency ratio is within ~10% of the 12_v2 value. The harness tax (7968 tokens
of system-prompt + tool-defs re-cached every turn) is byte-identical.

## Tool mix (sum over 108 cells)

| tool | Pi | OMP | delta |
|---|--:|--:|--:|
| read | 1134 | 2218 | +1084 |
| edit | 1014 | 1496 | +482 |
| grep | 0 | 477 | +477 |
| glob | 0 | 169 | +169 |
| write | 129 | 170 | +41 |
| bash | 1916 | 1807 | −109 |

OMP explores far more (≈2× reads, plus grep/glob that Pi doesn't use at all) and edits
more, while running bash slightly *less*. Pi relies on bash for discovery (`rg`/`find`-
style); OMP has dedicated read/grep/glob tools and leans on them.

## Solve agreement (108 paired cells)

both 26 · Pi-only 7 · OMP-only 10 · neither 65 → net OMP +3.

The two harnesses disagree on 17 cells (7 + 10) — neither is a strict superset. With 3
reps the ±3 net is within sampling noise.

## Crash

Exactly one `reward_binary=-1` cell, and it is the **same** one as 12_v2:
`mobly-grouped-test-barriers rep0` — `verifier_exit=timeout`, 22592B patch. The isolated
re-run during the 12_v2 audit confirmed this is a **genuine OMP-patch deadlock** (hangs
on `test_synchronized_context_in_group_teardown`), not transient infra. It reproduced
identically here.

## Pareto frontier placement

OMP (36 solves @ median $1.87) is **strictly Pareto-dominated** by `medium/baseline`
(53 solves @ median $1.69 — more solves for less money). Even within the low-thinking
tier, OMP's +2 solves over `codebase-memory-max` (34 @ $1.05) come at 1.78× the cost.

## Conclusion

- **Robust:** OMP is a systematically more expensive harness — ~3.5× tokens, ~2.2× cost,
  ~1.4× turns and wall — driven by a constant 7968 tok/turn wrapper, more exploratory
  tool use (read/grep/glob), and larger accumulating tool-output history. This is a
  harness property, not a model/cache/failure artifact, and it reproduced within 10%.
- **Not robust:** the 12_v2 solve-rate gap (OMP −2) did not hold; on the stratified 36_v2
  sample solves are tied (+3, within noise) and partial is tied. The honest take is
  *equivalent quality at 2.2× cost*, i.e. Pareto-dominated.
- The mobly deadlock is reproducible harness-specific behavior (a fair −1).

## Reproduce

```
python3 analysis/harness-forensics/run_analysis.py \
    --a baseline --label-a Pi --b baseline-omp --label-b OMP \
    --root results/gpt-5.5/low --subset 36_v2 --out analysis/omp-vs-pi-36v2
```
Outputs in `summaries/`: `all_cells.json`, `per_pair.json`, `workflow_args.json`.
