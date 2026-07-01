# Codegraph × OM stacking — 12_v0 × 3, gpt-5.5/low

**Question:** Does stacking an explicit relationship tool (codegraph) on top of
observational memory close the edge-attention gap that OM's prose-captured
relationships couldn't reach (the Tier-0 SYNTHESIS prediction)?

**Answer: No. Stacking is strictly worse than OM alone on this subset.**

8 arms, full factorial {none/skill/counts/names} × {no-OM/+OM}, n=36 paired reps.

## Per-arm

| arm | OM | solve | partial | med $ | med tok |
|---|---|---|---|---|---|
| baseline | — | 0.250 | 0.990 | 0.92 | 743k |
| **OM-alone** | +OM | **0.444** | 0.976 | 1.10 | 786k |
| codegraph-skill | — | 0.333 | 0.986 | 1.17 | 953k |
| codegraph-auto (counts) | — | 0.278 | 0.899 | 1.17 | 1015k |
| codegraph-impact (names) | — | 0.306 | 0.952 | 1.06 | 827k |
| codegraph-skill-om | +OM | 0.278 | 0.941 | 1.39 | 1004k |
| codegraph-auto-om | +OM | 0.306 | 0.947 | 1.46 | 1124k |
| codegraph-impact-om | +OM | 0.306 | 0.929 | 1.40 | 1014k |

## Does codegraph add to OM? (stacked vs OM-alone)

| stacked | Δpartial | 95% CI | Δsolve | 95% CI |
|---|---|---|---|---|
| skill+OM | −0.034 | [−0.111, +0.031] | −0.167 | [−0.333, +0.000] |
| counts+OM | −0.028 | [−0.074, −0.001] * | −0.139 | [−0.306, +0.028] |
| names+OM | −0.046 | [−0.105, −0.004] * | −0.139 | [−0.278, +0.000] |

**Every stacked arm is below OM-alone on both metrics.** counts+OM and
names+OM are significantly worse on partial. codegraph adds cost
(+$0.30/cell, +27% tokens) and subtracts performance.

## The one positive: OM rescues the counts regression

auto+OM vs auto: Δpartial +0.048 (CI [−0.006, +0.126]). The two catastrophic
v1 failures (shallow counts injection) are fully rescued by adding OM:

| task | rep | auto | auto+OM |
|---|---|---|---|
| fastapi-implicit-head-options | r1 | 0.01 | **0.91** |
| ts-pattern-match-each | r2 | 0.07 | **0.99** |
| boa-hierarchical-evaluation | r0 | 0.29 | 0.29 |
| boa-hierarchical-evaluation | r1 | 0.92 | 0.88 |

OM's attention-maintenance recovers the cells where counts injection derailed
the agent — but cannot save boa (broken across all codegraph arms) and the
recovery only brings counts+OM back to *below baseline-partial*, not above.

## Why (the mechanism)

- **Baseline partial is 0.990 — ceiling.** These 12 tasks are near-misses:
  ~99% of tests pass, the discriminator is solve rate (binary, coarse at
  n=3 reps). Partial has almost no upward headroom, so any context injection
  can only push partial *down* by introducing drift.
- **The binding constraint on these tasks is execution/correctness, not
  relationship discovery.** OM helps because it maintains attention on the
  task. codegraph hurts because it adds relationship info the agent didn't
  need and dilutes OM's signal — it's pure context bloat against a saturated
  near-miss.
- **This is consistent with the Tier-0 SYNTHESIS:** OM captures the
  relationship graph in prose but the executor doesn't act on it. Adding an
  *explicit* relationship tool doesn't change that — the executor still isn't
  bottlenecked on relationships here.

## Verdict

The SYNTHESIS prediction — "an explicit relationship tool plausibly closes
the edge gap that OM's prose can't" — is **falsified on 12_v0 for
gpt-5.5/low.** Stacking codegraph on OM is net-negative: worse partial,
worse-or-equal solve, +27% cost. OM-alone remains the best arm.

This does *not* settle the broader attention hypothesis — only this
model/thinking/subset/intervention. The ceiling effect here is severe.

## Next test (unchanged, now reinforced)

Re-run the full 8-arm factorial on **36_v1**, where baseline-partial is well
below ceiling and OM-alone's win was clean (+0.082 partial, +8 solves/113).
If codegraph+OM can't beat OM-alone *there*, the intervention is
settled-negative for gpt-5.5/low and the conclusion is that the binding
constraint on DeepSWE tasks is execution/correctness, not relationship
discovery — even with a real graph tool and even stacked with memory.

Cost estimate for 36_v1 × 3 × 8 arms: ~$1050 at ~$1.10/cell median.

## Reproduce

```
python3 scripts/codegraph_om_12v0_analysis.py
```
