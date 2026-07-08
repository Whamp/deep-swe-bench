# GPT-5.5 xhigh pi-codex-goal — 36_v2 analysis

**Run:** `pi-codex-goal-gpt55-xhigh-36v2-r3-w12` (108 cells: 36 tasks × 3 reps)
**Date:** 2026-07-03

## Headline

Adding the pi-codex-goal extension to **xhigh** thinking is **strictly dominated**
by plain xhigh baseline: fewer solves, lower partial reward, more tokens, more cost.
The Pareto frontier is unchanged.

## Metrics (36_v2, 108 cells each)

| config | solves | rate | mean_partial | med_tokens | med_cost | total_cost |
|--------|-------:|-----:|-------------:|-----------:|---------:|-----------:|
| low/baseline | 33 | 30.6% | 0.9675 | 0.61M | $0.86 | $102 |
| low/codebase-memory-max | 34 | 31.5% | 0.9701 | 0.81M | $1.05 | $126 |
| low/pi-codex-goal | 48 | 44.4% | 0.9735 | 1.73M | $1.97 | $240 |
| medium/baseline | 53 | 49.1% | 0.9899 | 1.53M | $1.69 | $198 |
| **xhigh/baseline** | **71** | **65.7%** | 0.9913 | 6.85M | $5.93 | $658 |
| **xhigh/pi-codex-goal** | **68** | **63.0%** | 0.9786 | 8.57M | $6.76 | $798 |

## Paired analysis (108 paired cells, same task+rep)

| transition | count |
|------------|------:|
| both solved | 57 |
| baseline-only | 14 |
| goal-only | 11 |
| neither | 26 |
| **net solve delta** | **−3** |

- mean Δpartial: **−0.0126** (slight quality drag)
- 38/108 cells moved at all

### Difficulty stratification

| bucket | n | baseline solves | goal solves | Δ | mean Δpartial |
|--------|--:|----------------:|------------:|---:|--------------:|
| hard | 36 | 14 | 9 | **−5** | −0.0162 |
| medium | 42 | 29 | 30 | +1 | −0.0192 |
| easy | 30 | 28 | 29 | +1 | +0.0008 |

The losses concentrate on **hard tasks (−5 solves)**. On hard tasks the model is
already near its limit; the goal-persistence overhead (more tokens, longer
sessions) doesn't convert anything and slightly hurts.

## Pareto frontier (36_v2, unchanged)

Only four configs are non-dominated:

```
low/baseline          33 solves @ $0.86
low/codebase-memory   34 solves @ $1.05
medium/baseline       53 solves @ $1.69
xhigh/baseline        71 solves @ $5.93
```

xhigh/pi-codex-goal (68 @ $6.76) is **dominated by xhigh/baseline**.
low/pi-codex-goal (48 @ $1.97) is **dominated by medium/baseline**.

## Interpretation

pi-codex-goal helps at **low** thinking (+15 solves: 33→48) but that gain is
itself dominated by simply raising thinking to medium (53 solves @ $1.69, which
beats low+goal's 48 @ $1.97 while costing less). At **xhigh**, where the model is
already strong, the extension is pure overhead: −3 solves, −0.013 partial,
+25% tokens, +14% cost.

This reinforces the project's central finding: **thinking budget dominates as
the single biggest intervention, and no extension or skill tested so far has
expanded the Pareto frontier beyond what thinking budget alone gives.**

## Cost per solve vs low/baseline

- low→medium: $4.81 / net solve (best bang-for-buck)
- low→xhigh: $14.63 / net solve
- medium→xhigh: $25.54 / net solve
- xhigh+goal is **negative** (loses solves while costing more) — worse than free.
