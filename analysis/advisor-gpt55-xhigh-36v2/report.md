# pi-advisor (GPT-5.5 low exec + GPT-5.5 xhigh advisor) on 36_v2

Run: `advisor-gpt55-xhigh-36v2-r3-w8` — 108 cells (36 tasks × 3 reps), executor
`openai-codex/gpt-5.5` low, advisor `openai-codex/gpt-5.5` reasoning xhigh, both via
Codex OAuth. Baseline = plain Pi (GPT-5.5 low, no extensions/skills), same 108 cells.
Compared against reused low/baseline cells on the arm-independent 36_v2 subset.

## Headline

**pi-advisor does not beat baseline. It is strictly Pareto-dominated.**

Solves are identical (33/108) at materially higher token, cost, and wall-time cost.
The advisor changed *which* tasks solved but not *how many*. This is the same pattern
seen across every extension/skill tested so far: nothing has expanded the Pareto
frontier beyond what thinking budget alone gives on 36_v2.

## Aggregate (108 paired cells)

| metric | baseline (low) | advisor | delta |
|---|---|---|---|
| solves | 33/108 (30.6%) | 33/108 (30.6%) | **+0** |
| mean partial | 0.9675 | 0.9712 | +0.0037 (near ceiling) |
| median tokens (combined) | 608k | 918k | **+299k (+50%)** |
| median cost (combined) | $0.86 | $1.04 | **+$0.22 (+25%)** |
| median wall | 206s | 430s | **+219s (~2× slower)** |
| median patch | 13.0kB | 15.1kB | +2.0kB |
| total benchmark cost | $102.03 | $132.93 | +$30.90 |

Both partial means are ~0.97 — the low executor is already near the partial ceiling
on 36_v2, so the signal is binary solve conversion, and there the advisor is flat.

## Solve agreement (108 cells)

both solved 21 · baseline-only 12 · advisor-only 12 · neither 63.

The 12-for-12 swap is the whole story: the advisor redistributes solves rather than
adding them. It crosses the threshold on 12 tasks baseline missed and steps off 12
baseline hit. Net zero is not "advisor +0"; it is a wash between real gains and real
losses.

## Difficulty stratification (cross-model pass-rate terciles)

| bucket | base solves | adv solves | net solves | base partial | adv partial | dpartial |
|---|---|---|---|---|---|---|
| hard (36 cells) | 6/36 | 6/36 | 0 | 0.979 | 0.981 | +0.003 |
| medium (42 cells) | 11/42 | 9/42 | **−2** | 0.939 | 0.949 | +0.010 |
| easy (30 cells) | 16/30 | 18/30 | **+2** | 0.993 | 0.990 | −0.003 |

The advisor trades medium solves for easy solves — the least valuable direction. On
medium tasks it nudges partial up slightly but loses two binary solves; on easy it
gains two but partial dips. Hard is a pure wash.

## Advisor usage (this is not a "didn't activate" problem)

- advisor called in **108/108 cells**, 221 total calls (median 2/cell)
- 631,762 advisor tokens total; advisor-only cost ~$5.87 (~$0.054/cell, Codex subscription-burned not cash)
- the xhigh advisor genuinely fires on every task and still nets zero solves

## Big movers (per-rep, |Δpartial| ≥ 0.05)

Consistent losses (advisor hurts repeatedly):
- `go-git-worktree-merge-conflicts` — 3/3 reps negative (−0.21, −0.11, −0.11)
- `claude-code-by-agents-recursive-delegation` — solve lost (1.000 → 0.842)
- `participle-grammar-conflict-analysis` — bimodal (−0.31 one rep, +0.30 another)

Consistent wins (advisor helps repeatedly):
- `tengo-destructuring-bindings` — 3/3 reps positive (+0.28, +0.22, +0.13)
- `textual-kitty-key-phases` — +0.13, +0.09
- `pest-character-class-coalescing` — +0.07

These are task-specific, not a systematic capability lift. The advisor's strategic
guidance pushes the low executor toward different solution shapes; whether that
crosses the binary line is roughly coin-flip on this near-ceiling subset.

## Pareto context (36_v2)

Known non-dominated configs: low/baseline (33 @ $0.86) → low/codebase-memory-max
(34 @ $1.05) → medium/baseline (53 @ $1.69) → xhigh/baseline (71 @ $5.93).

**advisor-gpt55-xhigh (33 @ $1.04) is dominated by low/baseline** (same solves,
higher cost/tokens/wall). It does not appear on the frontier.

## Bottom line

A GPT-5.5 xhigh advisor layered on a GPT-5.5 low executor adds ~50% tokens, ~25%
cost, and ~2× wall time for **zero net solve gain**. The xhigh advisor's strategic
input redistributes which tasks cross the binary threshold but does not raise the
solve rate. Consistent with the broader project finding: on 36_v2, raising the
executor's own thinking budget (low → medium) is far more cost-effective than adding
a second model as an advisor — medium/baseline (53 solves @ $1.69) dominates this
advisor arm (33 solves @ $1.04) on every axis.

Caveat: advisor cost ($5.87 total) is Codex-subscription-burned, not cash; the
combined cost accounting treats it as real, which is the conservative choice for
Pareto placement.
