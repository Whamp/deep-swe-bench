# testing-skills@1.1.0 vs baseline@1.1.0 — Evidence-Diversity Findings

Same-model config control (GPT-5.6 Sol, low), 113 tasks × 3 reps = 339 canonical matched pairs.
Scope: treatment advertises `testing`, `fuzzing`, `property-based-testing`. Source:
`analysis/testing-skills-1.1.0/full113-comparison.json` + 109 paired packets.

Every number below is **observed** (sourced from the artifact) unless tagged **[inference]**.

---

## 1. Honest headline

| Metric | Value |
|---|---|
| Net solves | **+18** (gains 53, losses 35, both 89, neither 162) |
| Solve-rate delta | +5.3 pp |
| Exact McNemar p | **0.069 (not significant at 0.05)** |
| Paired bootstrap 95% CI | **[0.0, 0.106] — touches zero** |
| Cost | **+33.8%** ($248.74 → $332.84) |
| Tokens | **+51.4%** (199M → 301M) |
| Turns / tool calls | +17.7% / +21.7% |

**Verdict:** a real-direction, small, *expensive* effect that is not individually
significant at n=339. Consistent across both task subsets (36_v2: +7; added_77: +11)
and across reps, so it is probably not noise — but "probably real, marginal, costly"
is the honest read, not "testing skills win."

---

## 2. What the treatment actually changes (observed behavior)

The signature is **more of the same work in the same place**, not a different strategy.

| Behavioral stage (observed on flip cells) | Gains: base→test | Losses: base→test |
|---|---|---|
| Shared ≥1 changed file (seam overlap) | 51/53 | 33/35 |
| Reads before first mutation (mean) | 8.0 → 11.2 | 6.5 → 8.7 |
| Validation cmds after first edit (mean) | 5.2 → 7.9 | 5.7 → 6.5 |
| Patch added lines (mean) | 327 → 388 | 291 → 332 |
| Cells writing a test file | test_patch cells 132 → **253** (whole set) | — |

First-consequential-divergence is overwhelmingly *"reached an overlapping
implementation seam, but the lower-scoring patch left N feature checks
unsatisfied"* — not "disjoint seam" (only 1 gain / 2 losses). **The skill does not
relocate the fix. It changes how completely the same seam is finished.**

### Flip character — near-miss boundary events
- **Gains:** baseline partial median **0.988**, median **2** feature checks missing (35/53 ≤3).
- **Losses:** testing partial median **0.984**, median **1** feature check missing (29/35 ≤3).

Both directions sit at the margin. Which side crosses to 1.0 is governed by whether
1–3 feature checks happen to be satisfied. This is *why* McNemar is marginal and the
CI touches zero.

### Grounding cells (cite as evidence; mechanisms stay general)
- **Go serialization cell (geo-shapeindex-serialization/rep0):** baseline 1/24 feature
  checks (partial 0.96), testing 24/24. Right read all three skills, wrote a fuzz
  target, +73 added lines. A thoroughness win — at **+93% tokens**.
- **TS ORM cell (drizzle-orm-window-function-builders/rep1):** baseline 126/130,
  testing 130/130. Right added a test file + 4 dialect clauses baseline missed; +63% tokens.
- **Python loss cell (textual-richlog-follow-state/rep0):** baseline 20/20 solved,
  testing 19/20 (missed one invariant). Right read only `testing`, **+69% tokens**,
  yet lost. **Counterexample:** more spend did not buy the missing guard.

---

## 3. The likely story — and why it is only partly right

> *Likely story:* testing skills make the agent write discriminative tests that catch
> missing invariants, so it solves more.

**What the evidence supports instead:** reading `testing` reframes completion from
"I changed code" to "I proved the change flips a check" (the skill's step-4
discrimination criterion: run red, then green). That loop makes the agent iterate
validation until its targeted check passes, which **correlates** with 1–3 more
feature checks going green on near-miss cells. The wins come from **completeness
via the discrimination loop**, not from test *quality* — the tests written are
overwhelmingly example/regression tests mirroring the feature contract, not the
independent-oracle discrimination proofs the skill asks for.

**Observed support:** test-file output doubled (132→253 cells) and validation
commands rose on *every* bucket including the 162 neither-solved cells (58→117 test
files there). If the mechanism were "write a sharp discriminating test," we would
not see diffuse test-writing on cells that never flip. We see diffuse test-writing.

---

## 4. Challenges to the story (each evaluated)

**C1 — "It's just more compute."** Partly. The extra spend is **diffuse**: the 162
neither-solved cells burn +50% tokens / +34% cost for zero flips; the 89 both-solved
cells burn +46% tokens / +30% for the same outcome. A pure "compute helps" story
predicts uniform uplift, but conversion is **selective** (§5), so compute spent on a
*particular activity* (validation/test-writing), not compute per se, is doing the
work. **Verdict: partial — the activity matters, not just the budget.**

**C2 — "Specialist skills (fuzz/PBT) are doing the work."** No. They are **read but
not delivered**. `fuzzing` read in 49 cells, `property-based-testing` in 53; only **7
cells produced a fuzz target** (6 on one Go task, all failed) and **0 produced a
property test**. The 12g/6l "specialist association" is confounded: those cells also
read `testing`, and the specialists produced no artifacts. **Verdict: reject — the
effect is 100% the `testing` skill.**

**C3 — "Selection effect: the agent reads the skill on tasks it would solve anyway."**
Isolated by read-state. `testing`-**read** cells (317): net **+20** at +54% tokens.
`testing`-**not-read** cells (22): net **−2** at +11% tokens. Reading the skill is
where both the cost and the gain concentrate; mere advertisement is inert-to-slightly-
harmful. **Verdict: the gain tracks acting on the skill, not pre-existing difficulty.**

**C4 — "The language split is a room-to-gain / base-rate artifact."** No. Recovery and
loss rates are both conditional on baseline state:

| Lang | recover baseline-fails | lose baseline-solves | net |
|---|---|---|---|
| TypeScript | 24/70 = **34.3%** | 8/35 = 22.9% | +16 |
| Go | 17/55 = **30.9%** | 11/47 = 23.4% | +6 |
| Python | 9/65 = **13.8%** | 14/37 = **37.8%** | **−5** |
| Rust | 0/11 = **0.0%** | 2/4 = 50% | −2 |

Python has the **most room** (65 baseline-fails) yet the **worst recovery and worst
loss rate**. If this were base-rate, Python should recover ≥ TS. It does the opposite.
**[inference]** Plausible mechanism: typed surfaces (TS/Go) give the validation loop
compiler-grade feedback that closes contract gaps; in Python the loop lacks that signal
and the longer trajectory drifts. Untested — could equally be task-type confound. Keep
as a correlation, not a causal claim.

**C5 — "Variance, not signal."** 53 gains: 23 in multi-rep-flip tasks, 30 single.
35 losses: 11 multi, 24 single. Most flips are single-rep boundary events — consistent
with near-miss variance. But 9 tasks net ≥+2 (consistent gainers) vs 5 net ≤−2, and
the direction holds across both subsets and all three reps. **Verdict: a small real
signal riding on a lot of boundary variance.**

---

## 5. Selection effects & overfitting traps

- **"Test-file count doubled" is a trap metric.** The tests are contract-mirroring
  examples, not discriminating proofs. Optimizing for *more test files* would optimize
  test volume, which the neither-solved bucket shows is pure cost.
- **Specialist association (12g/6l) is a selection artifact.** It reflects the agent's
  own judgment that a task is "testing-relevant," not the specialist content (which
  delivered nothing). Do not read it as "specialists help."
- **Language gate is memorization.** "Enable testing only for TS/Go" would overfit this
  subset and generalize poorly. The correlation is real; the *cause* is unverified.
- **Category signal is thin.** 8/9 consistent gainers are `feature_request`; 2/5
  consistent losers are the only `bugfix` tasks in the set (n=4 bugfix total). Too few
  to act on — flag only.

---

## 6. Redesign principles (broadly useful, grounded)

1. **The active ingredient is the discrimination completion criterion, not test volume.**
   The skill's value is the step-4 demand ("prove it goes red for the named reason, then
   green"). Preserve and sharpen that bound. Do not add instructions that push the agent
   to write *more* tests — it already over-writes.

2. **Add a stop condition; the skill currently has no budget bound.** The dominant cost
   failure is diffuse over-spend on cells that never flip (neither bucket: +34% for
   nothing) and on cells that would solve anyway (both bucket: +30%). The skill drives
   iteration but never says "the discriminating test is green and the suite is green —
   stop testing and finish." A completion criterion that *terminates* the testing loop
   would recover most of the $63 of non-flip spend without touching the wins.

3. **Bound the test surface to the named risk.** The skill says "smallest discriminating
   surface" but observed output is broad (the TS ORM cell wrote 286 lines / 18 files).
   Strengthen the "one discriminating test for the named contract, not a suite" demand.
   This is the single largest lever on cost.

4. **Keep the specialists model-invoked but do not force them to fire.** They correctly
   did not fire on tasks that did not need them, and when they did fire they delivered
   no artifacts. The routing is working; the problem is they pay context load
   (advertised to all 339 cells) for zero delivered value. Cheapest win: confirm their
   trigger branches are tight so they stop being read on low-relevance tasks.

5. **[inference] The validation loop converts where there is independent feedback.**
   This is general (typed surfaces, runnable oracles), not language-specific. If a
   future revision wants to raise conversion, the lever is "ensure the discrimination
   loop has an independent oracle" — not gating by ecosystem.

---

## 7. Tempting revisions to REJECT

| Revision | Why reject |
|---|---|
| "Make the agent write more tests" | Test output already 2× and the extra lands mostly on non-flip cells. More volume = more cost, not more solves. |
| "Make fuzzing/PBT fire more often" | They fired on relevant tasks and delivered **zero** artifacts. Forcing firing adds cost with no evidence of benefit. |
| "Gate the testing skill by language (TS/Go only)" | Task-memorization; the language correlation's cause is unverified (C4). Will not generalize. |
| "Lower the discrimination-proof bar to save cost" | The discrimination criterion is the *active ingredient* (§6.1). Weakening it removes the mechanism that converts near-misses. |
| "Add a 'write tests for every feature' instruction" | The agent already does this diffusely; it is the cost problem (§6.3), not the solution. |
| "Treat the 12g/6l specialist association as evidence specialists work" | Confounded selection effect (C2); specialists delivered nothing. |

---

## 8. Confound check (clean)

Provenance verified on all 678 cells: model, thinking level, config locks, `agent_exit=0`,
no timeouts. 6 resource-flagged cells (OOM) — all still solved (`reward_binary=1`), so no
outcome corruption. Cross-scope regression (broke preservation tests) is proportional
(9 gain-driver / 6 loss-driver), so the skill does **not** systematically introduce
regressions. No wall-time or memory confound on the effect.
