# GPT-5.5 thinking-level comparison — 36_v2 (complete)

Generated 2026-07-02. Subset **36_v2** (arm-independently stratified, 36 tasks ×
3 reps = 108 cells). All runs use `openai-codex/gpt-5.5`, Codex OAuth, default
5400s agent budget, `baseline` = plain Pi (no extensions, no skills). Difficulty
terciles from official DeepSWE v1.1 cross-model pass rate.

All three thinking levels now complete at 108/108.

## Headline: thinking level is the dominant lever

| thinking | solves | mean partial | median tokens | median cost | median wall | median patch |
|----------|--------|--------------|---------------|-------------|-------------|--------------|
| low      | 33/108 (30.6%) | 0.967 | 0.61M | $0.86 | 206s | 13K |
| medium   | 53/108 (49.1%) | 0.990 | 1.53M | $1.69 | 368s | 19K |
| xhigh    | 71/108 (65.7%) | 0.991 | 6.85M | $5.93 | 1122s | 33K |

## Paired deltas (same 108 cells)

| transition | solve delta | partial Δ | median token Δ | notes |
|------------|-------------|-----------|----------------|-------|
| low → medium | +20 | +0.0224 | +0.94M | best bang-for-buck |
| medium → xhigh | +18 | +0.0014 | +5.33M | more solves, partial at ceiling |
| low → xhigh | +38 | +0.0238 | +6.18M | full range |

Partial reward is at ceiling for both medium (0.990) and xhigh (0.991). Every
gain from medium upward is **pure binary solve conversion**, not quality lift.

## Cost efficiency per additional solve

| transition | extra solves | extra cost | $/net-solve | relative |
|------------|-------------|------------|-------------|----------|
| low → medium | +20 | $96 | **$4.81** | baseline |
| low → xhigh | +38 | $556 | $14.63 | 3.0× |
| medium → xhigh | +18 | $460 | **$25.54** | 5.3× |

Each thinking step is **less efficient than the last**. medium→xhigh costs
**5.3× more per additional solve** than low→medium.

## Difficulty stratification (baseline only)

| thinking | hard (n=36) | medium (n=42) | easy (n=30) |
|----------|-------------|---------------|-------------|
| low      | 6/36, 0.979 | 11/42, 0.939 | 16/30, 0.993 |
| medium   | 12/36, 0.994 | 17/42, 0.982 | 24/30, 0.997 |
| xhigh    | 14/36, 0.990 | **29/42**, 0.987 | **28/30**, 0.999 |

xhigh's biggest gains over medium are on **medium-difficulty tasks** (17→29,
+12 solves) and easy tasks (24→28, +4). On hard tasks xhigh barely moves the
needle (12→14, +2).

## Extensions vs thinking budget (full context, all 108 cells)

No low-thinking extension matched what plain medium thinking gives for free:

| config | solves | median cost | $/net-solve vs low |
|--------|--------|-------------|---------------------|
| low/baseline | 33/108 | $0.86 | — |
| low/codebase-memory-max | 34/108 | $1.05 | (only +1) |
| low/ponytail-{full,lite,ultra} | 28–30/108 | ~$1.05 | negative |
| low/pi-codex-goal | 48/108 | $1.97 | $9.21 |
| **medium/baseline** | **53/108** | **$1.69** | **$4.81** |
| xhigh/baseline | 71/108 | $5.93 | $14.63 |

- **medium/baseline beats every low-thinking arm** including pi-codex-goal,
  at lower cost per solve.
- **xhigh/baseline beats everything** on raw solve count but at 3.5× the cost
  of medium.
- All Ponytail variants at low thinking **lost solves** vs baseline.

## Bottom line

1. **Thinking budget dominates.** The single biggest intervention available is
   raising low→medium (+20 solves at $4.81 each).
2. **medium is the efficiency sweet spot.** It captures 75% of xhigh's solve
   gain (53 vs 71) at 26% of the cost.
3. **xhigh is worth it for raw solve rate** if budget allows — it reaches
   71/108 (65.7%) — but costs 5.3× more per marginal solve than the medium step.
4. **No extension closes the thinking gap.** The best low-thinking extension
   (pi-codex-goal, 48 solves) still loses to plain medium (53 solves) at higher
   per-solve cost.
5. **Partial reward is at ceiling from medium up.** From medium onward, all
   improvement is near-miss→solve conversion, exactly the regime where memory
   and detail-persistence tools should theoretically help.
