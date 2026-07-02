# GPT-5.5 medium baseline — 36_v2 comparison

Generated 2026-07-02. Subset **36_v2** (arm-independently stratified, 36 tasks ×
3 reps = 108 cells per complete config). All runs use `openai-codex/gpt-5.5`,
Codex OAuth, default 5400s agent budget, `baseline` = plain Pi (no extensions,
no skills). Difficulty terciles come from the official DeepSWE v1.1 cross-model
pass rate (`data/deepswe-v1.1-task-difficulty.tsv`).

## Headline table (complete configs, n=108 unless noted)

| config               | solves    | mean partial | median tokens | median cost | median wall | median patch |
|----------------------|-----------|--------------|---------------|-------------|-------------|--------------|
| low/baseline         | 33/108    | 0.967        | 0.61M         | $0.862      | 206s        | 13001B       |
| low/baseline-wf      | 31/108    | 0.979        | 0.65M         | $0.925      | 247s        | 13802B       |
| low/codebase-memory  | 31/108    | 0.970        | 0.77M         | $0.991      | 229s        | 13034B       |
| low/codebase-memory-max | 34/108 | 0.970        | 0.81M         | $1.049      | 247s        | 13217B       |
| low/codegraph-skill  | 28/108    | 0.962        | 0.73M         | $0.988      | 248s        | 17262B       |
| low/pi-codex-goal    | 48/108    | 0.973        | 1.73M         | $1.972      | 408s        | 20176B       |
| low/ponytail-full    | 30/108    | 0.973        | 0.90M         | $1.054      | 263s        | 12848B       |
| low/ponytail-lite    | 28/108    | 0.968        | 0.84M         | $1.068      | 256s        | 12642B       |
| low/ponytail-ultra   | 30/108    | 0.972        | 0.79M         | $1.033      | 245s        | 12514B       |
| **medium/baseline**  | **53/108**| **0.990**    | **1.53M**     | **$1.687**  | **368s**    | **19487B**   |
| medium/baseline-wf   | 13/33     | 0.990        | 1.71M         | $1.642      | 411s        | 21361B       |
| xhigh/baseline       | 36/71¹    | 0.989        | 6.78M         | $5.710      | 1122s       | 33095B       |

¹ xhigh run still in progress (71/108 cells when this was written).

## Key finding: thinking level dominates everything else tested

On the same 36_v2 tasks, simply raising the thinking budget from low to medium
beat every low-thinking extension/skill tested, including the previous best
(low/pi-codex-goal at 48/108):

| comparison (paired, same cells) | solves | mean partial Δ | median token Δ |
|---------------------------------|--------|----------------|----------------|
| low → medium baseline (108)     | 33→53  | +0.0224        | +0.94M         |
| low → xhigh baseline (71)       | 17→36  | +0.0135        | +6.04M         |
| medium → xhigh baseline (71)    | 31→36  | −0.0019        | +5.04M         |

- **medium is the efficiency sweet spot.** It captures most of xhigh's solve
  gains at roughly **¼ the tokens, ⅓ the cost, and ⅓ the wall time**.
- **xhigh's marginal returns are poor.** Going medium → xhigh adds ~5 solves on
  the 71-cell overlap but costs +5M median tokens and +$4.2 median cost per cell,
  while mean partial actually drops slightly (−0.0019).
- low → medium is the single biggest jump measured here: **+20 net solves**.

## Difficulty stratification (baseline only)

| config            | hard (n=36) | medium (n=42) | easy (n=30) |
|-------------------|-------------|---------------|-------------|
| low/baseline      | 6/36, 0.979 | 11/42, 0.939  | 16/30, 0.993|
| low/pi-codex-goal | 10/36, 0.978| 16/42, 0.973  | 22/30, 0.969|
| medium/baseline   | **12/36, 0.994** | **17/42, 0.982** | **24/30, 0.997** |
| xhigh/baseline    | 14/36, 0.990 | 5/17, 0.977  | 17/18, 0.999|

- medium lifts **all three buckets** — hard, medium, and easy.
- The biggest medium win over low/pi-codex-goal is on **medium-difficulty
  tasks** (17 vs 16 solves but partial 0.982 vs 0.973) and **easy tasks**
  (24 vs 22 solves).
- xhigh's only real edge over medium is on **hard tasks** (14 vs 12 solves).

## Cost per additional solve vs low baseline (full 108)

| config           | solves    | net new solves | extra cost | $/net-solve |
|------------------|-----------|----------------|------------|-------------|
| low/pi-codex-goal| 33→48     | +15            | $138.22    | $9.21       |
| **medium/baseline** | **33→53** | **+20**     | **$96.19** | **$4.81**   |

medium baseline is roughly **2× more cost-efficient per additional solve** than
low/pi-codex-goal and delivers 5 more net solves.

## Extension/skill verdict at low thinking (for context)

No low-thinking extension/skill beat low/baseline on solves except
low/pi-codex-goal (48/108) and low/codebase-memory-max (34/108, +1). All
Ponytail variants lost solves (28–30 vs 33) while raising tokens and cost,
confirming the earlier Ponytail audit: on a capable executor Ponytail is a
partial-progress / patch-shaping tool, not a solve-rate booster.

## Caveats

- xhigh numbers are partial (71/108); the overlap comparison is fair but the
  full-108 xhigh row is not yet final.
- medium/baseline-wf has only 33/108 cells (incomplete), shown for reference.
- All low-thinking configs and medium baseline are complete at 108/108.
- Difficulty terciles are from official DeepSWE v1.1 cross-model pass rate
  (arm-independent), so this comparison is not selected on the dependent
  variable.
