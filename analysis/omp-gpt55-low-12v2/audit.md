# OMP 12_v2 run — infrastructure audit (first OMP run)

Premise: this was our first run of the OMP ("Oh My Pi", v16.3.5) harness, so we
assumed our infrastructure was probably wrong and audited accordingly. Run:
`gpt55-low-baseline-omp-12v2-r3-w12` (36 cells = 12 tasks × 3 reps), executor
`openai-codex/gpt-5.5` low, compared against the Pi harness `baseline`.

## Verdict

**The infrastructure is correct. We did not mess it up.** Every plausible infra fault
was checked and ruled out. OMP's underperformance vs Pi is genuine harness behavior,
not a setup mistake. The one anomalous cell is a genuine OMP patch defect, confirmed
by an isolated verifier re-run.

## Checks passed (infra verified correct)

| # | check | result |
|---|---|---|
| 1 | model in **all 36 cells** (not just smoke) | ✅ `openai-codex/gpt-5.5` + `provider:openai-codex` + `api:openai-codex-responses` everywhere — no fuzzy-selected Azure model (the risk `docs/omp-gpt55-low-baseline.md` warned about) |
| 2 | all 6 tools present & functional | ✅ bash 545, read 672, edit 480, grep 130, glob 52, write 51 calls across cells |
| 3 | task prompt delivered | ✅ same instruction as Pi (OMP: raw text; Pi: `<file>`-wrapped — minor format diff, not a fault) |
| 4 | token accounting | ✅ identical schema to Pi; session sums == result.json (no double-counting); 3× gap is **systematic across all 12 tasks** (1.8×–5.3×, median 3.1×), not an outlier or measurement bug |
| 5 | agent health | ✅ 0 timeouts, 0 empty patches; all 36 `omp.stderr.txt` empty (0 bytes) |
| 6 | verifier parity | ✅ same f2p/p2p/apply_failed scoring; identical p2p regressions |

## The one anomaly — investigated to a verdict

`mobly-grouped-test-barriers/rep0`: `reward_binary=-1`, `verifier_exit=timeout`,
empty verifier log. mobly was OMP's biggest per-task loss (0.661 vs Pi 0.983), and no
other config times out on mobly — so it warranted a decisive test.

Two hypotheses:
- **A (our fault):** `--workers 12` batch contention starved the verifier → unfair -1.
- **B (OMP's fault):** OMP's patch genuinely makes the suite hang.

**Decisive test:** re-ran the verifier for this one cell **in isolation** (no
contention, generous timeout). Result: it reached 75% of the test suite normally, then
**hung for 12+ minutes on a single test, `test_synchronized_context_in_group_teardown`**
(a synchronization/barrier test — this is the mobly "grouped test barriers" task).

→ **Hypothesis B confirmed. OMP's rep0 patch contains a deadlock.** The verifier never
completes because a test blocks forever. The `-1` is therefore a fair (if harsh) score
for a hanging solution, **not** an infrastructure fault. OMP's other two mobly reps
(0.993, 0.991) actually beat Pi's (0.979, 0.977) — so this is a genuine per-rep defect,
not a systematic OMP inability on the task.

## What the audit changed about the headline

Nothing. OMP is still Pareto-dominated by the Pi harness (9 vs 11 solves at ~3× tokens).
The audit confirms the token gap is real (systematic across all tasks) and the mobly
"loss" is a genuine OMP deadlock, not an infra artifact. The original `report.md`
conclusion stands.

## Methodological caveat worth flagging (not an infra bug)

The harness scores a full-suite hang as `reward=-1`/`partial=0.0`. OMP's mobly rep0
passed 75% of tests before hanging but gets the same 0.0 as a cell that passes nothing.
This is **consistent across all arms** (Pi would get -1 for a hang too), so it is not
unfair to OMP specifically — but a per-test-timeout verifier would give partial credit
and change this cell's number. This is a verifier-design observation, not something we
broke.

## Recommendations before future OMP runs

1. The infra is sound — no config/image/prompt/accounting fixes needed.
2. Keep the existing smoke contract (it correctly pinned model/provider/api/tools).
3. Watch `--workers` vs verifier-heavy tasks: mobly's suite is slow (~8–10 min even when
   it doesn't hang), so high concurrency can approach the 35-min verifier cap on
   legitimate runs. This run had 0 contention-induced timeouts, but it's a risk at
   higher worker counts.
