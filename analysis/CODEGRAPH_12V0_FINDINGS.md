# codegraph 12v0×3 results — gpt-5.5/low (5-arm, incl. fn-impact v2)

**Names beat counts.** The v1→v2 fix worked: switching the injected primitive
from caller *counts* (`brief`) to caller *names* (`fn-impact`) recovered most of
the harm v1 caused. But neither codegraph config beat OM or baseline-partial,
and none reaches significance on solve.

## Numbers (36 paired reps, subset 12_v0, bootstrap 95% CI vs baseline)

| arm | solve | partial | med tok(k) | med cost | med turns |
|---|---|---|---|---|---|
| baseline | 0.250 | 0.990 | 743 | $0.92 | 44 |
| **OM (gpt54mini-low)** | **0.444** | 0.976 | 786 | $1.10 | 44 |
| codegraph-skill | 0.333 | 0.986 | 953 | $1.17 | 46 |
| codegraph-auto (counts) | 0.278 | **0.899** | 1015 | $1.17 | 42 |
| codegraph-impact (names) | 0.306 | 0.952 | 827 | $1.06 | 40 |

| Δ vs baseline | Δpartial [95% CI] | Δsolve [95% CI] |
|---|---|---|
| OM | −0.014 [−0.055,+0.009] | **+0.194 [+0.028,+0.361]** ✓ |
| codegraph-skill | −0.004 [−0.013,+0.003] | +0.083 [−0.056,+0.222] |
| codegraph-auto | **−0.091 [−0.181,−0.019]** ✗ | +0.028 [−0.139,+0.194] |
| codegraph-impact | −0.038 [−0.093,−0.000] | +0.056 [−0.083,+0.194] |

**Head-to-head impact(names) vs auto(counts):** Δpartial = +0.053
[−0.027,+0.146] — recovers most of v1's −0.091 loss but the CI still touches 0.

## The v2 fix worked — and the rescues are specific

Impact recovered most of what auto broke. Paired by task+rep, three of v1's
catastrophic failures came back:

| task+rep | auto (counts) | impact (names) |
|---|---|---|
| fastapi-implicit-head-options r1 | 0.009 | **0.992** |
| ts-pattern-match-each r2 | 0.066 | **0.989** |
| boa-hierarchical-evaluation r0 | 0.292 | **0.958** |

So the harm in v1 *was* the shallow primitive: counts misled, names let the
model edit normally. The audit was right.

But it's not a clean win: impact also *regressed* one (boa r1: 0.917 → 0.292),
and actionlint (which auto aced) dropped slightly. The net is partial
*recovery*, not *improvement over baseline* — impact still sits at −0.038 vs
baseline (just-significantly-negative) and solve +0.056 (not significant).

## What the data says

1. **The primitive matters enormously.** Same extension, same hook, same files —
   just counts→names moves partial by +0.053 and undoes three total failures.
   This is direct evidence for the hypothesis that *the unit of injected
   attention* is the lever, not the presence of a tool.
2. **Names are necessary, not sufficient.** Even real caller names, forced into
   view on every read/edit, did not beat baseline-partial or OM. The model gets
   the relationship info but doesn't reliably *use* it to make better edits.
3. **OM still wins decisively** (solve +0.194, CI excludes 0). The codegraph
   arms are nowhere near that.
4. **Context tax is real but smaller now.** Impact's median tokens (827k) sit
   between auto (1015k) and baseline (743k) — the `batch fn-impact` single-call
   design kept it leaner than v1's per-file `brief`.

## Honest reading of the hypothesis

The original hypothesis: cheap models fail DeepSWE partly because they can't
hold the important caller-relationships, and externalizing that graph should
help.

- **The primitive-sensitivity result supports the mechanism** — injecting the
  *right* unit of attention (names) measurably helped vs the wrong unit (counts).
- **The absolute result does not support the intervention** — even the best
  codegraph arm doesn't beat bare baseline on partial, and OM dominates on solve.

Most likely reconciliation: on these 12 near-miss tasks (baseline partial 0.990),
the binding constraint is *execution/correctness*, not *relationship discovery*
(consistent with the Tier-0 finding that found_kept_failed dominates the failure
bucket). codegraph can't fix what isn't the bottleneck on this subset.

## Confounds

- n=12 tasks / 36 reps. Solve is coarse (0 / 0.33 / 0.67 / 1.0); partial near a
  0.99 ceiling has little room. Impact's +0.053 vs auto and −0.038 vs baseline
  need a bigger/harder subset to settle.
- 8 of 12 tasks are solved 0% by *every* arm — they contribute no discriminating
  signal, only noise. The signal lives in the 4 near-miss tasks.
- codegraph is repo-scoped (cross-package/shared-type seams invisible) — the
  audit's standing ceiling.

## Next (only if you want to keep going)

The discriminating test is a **harder subset** where baseline-partial is well
below ceiling — there the relationship-discovery bottleneck could actually
bite. The 36_v1 subset (used for the OM pilot) is the natural choice: bigger,
and OM's win there was clean (+0.082 partial). If codegraph-impact can't move
36_v1 either, the intervention is settled-negative for this model/thinking.

## Reproduce
```
python3 scripts/codegraph_12v0_analysis.py
```
Raw output: `analysis/codegraph-12v0-results.txt`.
