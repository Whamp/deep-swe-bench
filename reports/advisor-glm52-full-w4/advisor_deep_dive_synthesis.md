# Advisor GLM-5.2 Run — Deep-Dive Synthesis (postmortem)

**Run:** `advisor-glm52-full-w4` · **Date:** 2026-06-26 · **Author:** synthesis agent
**Headline (as reported):** mean partial 0.774 → 0.536; full solves 2 → 5; skipped-empty-patch 4 → 27; advisor called 101/113; ~536k advisor tokens.

> Read alongside the chunk reports (`failure_chunk_00..07.md`) and the six specialist reports in this directory. This document reconciles them and decides.

---

## TL;DR verdict (confidence: **HIGH**)

The headline "advisor collapsed mean partial by 0.24" is **not a clean measure of advisor efficacy.** It is dominated by two things, in this order:

1. **Executor (deepseek-v4-flash) streaming instability during the treatment run window** — `Provider finish_reason: error` killed ~31 of the worst outcomes (25 empty patches + 6 severe non-empty regressions). The advisor model (`glm-5.2`) was, by contrast, cheap and almost always stable.
2. **A non-concurrent, reused baseline.** Baseline traces date to **2026-06-24 23:37**; treatment traces to **2026-06-26 01:44** (~30 h later). The same tasks baseline solved with **zero** stream errors hit **4–8** under treatment (verified below). There is **no concurrent advisor-off control**, so advisor effects and provider-noise effects are confounded and cannot be separated from this run alone.

The pi-advisor extension is a **real but secondary** contributor: ~6–8 tasks were plausibly harmed by advisor guidance (premature-convergence / wrong-layer advice, plus 2 empty patches where advisor talk the agent into stopping). And when the executor *survived*, advisor produced **genuine, defensible signal**: 10 large wins (mostly hard bucket), +3 net full solves, ~4.7k tokens / call, $0 tracked cost.

**One-line answer to Will:** *mostly severe API/stream noise on the executor + a treatment-design confound (reused baseline), with a secondary advisor-guidance layer. Not "pi-advisor is structurally broken."*

---

## The numbers, reconciled

| Metric | Baseline (reused) | Advisor (treatment) | Read |
|---|---|---|---|
| Mean partial | 0.774 | 0.536 | collapse is real but **confounded** |
| Median partial | 0.957 | 0.788 | distribution skewed by 27 empties |
| Full solves (binary 1) | 2 | 5 | +3, small-n, genuine |
| skipped-empty-patch | 4 | 27 | **~23 of the 23 new empties are stream-error-driven** |
| Median turns | 57 | 38 | shorter because sessions died early |
| Median tokens | 3.29M | 1.91M | shorter runs ⇒ fewer tokens (artifact, not efficiency) |
| Advisor tasks with calls | — | 101/113 | 12 never called (all executor-killed) |
| Advisor tokens / call | — | ~4,095 | cheap; advisor model is not the cost driver |
| Advisor cost tracked | — | **$0.00** | zai/glm-5.2 returns no cost ⇒ accounting bug |
| Tasks with executor stream errors | low (baseline window) | 69/113 (61%) | **the dominant failure mode** |

The token/turn/cost drops are **not** advisor efficiency wins — they are the shadow of sessions dying at turns 2–25 instead of running 50–120. Treat median-token-drop as a symptom of truncation, not a benefit.

---

## Q1. What are we mostly seeing?

Four buckets, with the share of the *damage* (worst outcomes) attributed to each:

| Bucket | Share of worst outcomes | Confidence |
|---|---|---|
| **Executor stream-error storm (treatment-window provider flakiness)** | ~31 tasks (25 empty + 6 severe non-empty) | **High** |
| **Treatment-design confound (reused, non-concurrent baseline)** | inflates *all* deltas, esp. empty-patch delta | **High** |
| **Advisor guidance harm** (premature convergence, wrong layer, talk-into-stopping) | ~6–8 tasks (4–6 non-empty regressions + 2 empty) | **Medium** |
| **Ordinary model variance** (hard tasks, small deltas) | remainder of the 53 big losses | **Medium-Low** |
| **Genuine advisor wins** (counter-evidence the extension works) | 10 large + 15 small = 25 improved | **High** |

Key correction to several specialist drafts: the empty-patch explosion is **not** "the advisor extension lacks retry." It is the *executor* (`deepseek-v4-flash`) dying mid-stream. The advisor extension cannot retry a turn that the harness already ended. The advisor's own `completeSimple` calls overwhelmingly **succeeded** (101 calls, ~536k tokens, near-zero advisor-side failures).

---

## Q2. Advisor/tool-caused vs executor-stopped-early

| Cause | Tasks | Evidence |
|---|---|---|
| **Executor stopped early — stream error, no advisor call** (12) | `narwhals-rolling-window-suite`, `ink-grid-box-layout` (2 turns!), `katex-multicolumn-array-spans`, `kombu-virtual-queue-dead-lettering`, `obsidian-linter-scoped-ignore-markers`, `prometheus-transactional-reload-status`, `tomlkit-toml-table-converters`, `yjs-map-conflict-detection`, `httpx-streaming-json-iteration`, `participle-grammar-conflict-analysis`, `yaegi-go-embed-directives`, `superjson-error-stack-serialization` | All 12: `Provider finish_reason: error` before any advisor call; turns 2–13 vs baseline 50–122. Advisor never reached. |
| **Executor stopped early — stream error *after* advisor succeeded** (~13) | `httpx-multipart-response-parsing`, `kea-atomic-signal-selectors`, `mobly-grouped-test-barriers`, `task-task-graph-export`, `koota-deferred-mutation-buffer`, `kgateway-consistent-hash-policy`, `kombu-single-active-consumer-priority`, `opa-template-string-reconstruction`, `oxvg-structural-selector-preservation`, `sqlfmt-create-table-ddl-formatting`, +3 | Advisor call returns valid advice; a *later* executor turn dies. Correlation ≠ causation — but the empty patch is downstream of executor instability. |
| **Severe non-empty regression — stream error truncated mid-implementation** (6) | `pest-character-class-coalescing`, `ytt-jsonpath-query-api` (585 B vs 59 KB!), `vitest-duration-sharding`, `termenv-preserve-ansi-resets`, `opa-rego-rule-profiling`, `koota-composite-trait-aspects` | Real patches produced, reward collapses to ~0; documented stream errors during write/test; turns cut 59–85%. |
| **Advisor guidance harm — premature convergence / wrong layer** (~4–6) | `adaptix-name-mapping-aliases` (advisor said "On track" with critical files unread → agent converged; 208→44 turns), `gql-incremental-graphql-delivery`, `dateutil-rfc5545-timezone-interop`, `fastapi-deprecation-response-headers`, `go-genai-streamed-function-args` | Advisor nudged execution before recon/tests complete, or picked the wrong abstraction layer. No stream errors. |
| **Advisor guidance harm — talked the agent into stopping** (2) | `happy-dom-abort-pending-body-reads`, `kysely-window-grouping-helpers` | Empty patch, **zero** stream errors. Advisor "don't commit yet / keep reconning" language → agent stopped without editing. |
| **Ordinary variance / hard task** (~3) | `arcane-drift-detection-baselines`, `effect-sse-httpapi-streaming` | No clear advisor anti-pattern; genuinely hard. |

**Net:** of the catastrophic outcomes, **~31/37 are executor-stopped-early**, **~6–8 are advisor-amplified or advisor-caused**, and **~2 are pure advisor-induced premature stop**. The advisor *tool* (the `completeSimple` path) itself misbehaved in essentially **0** of these — its calls returned valid text.

---

## Q3. Why did skipped-empty-patch explode 4 → 27?

Decomposition of the 27 advisor-side empties (from `advisor_empty_patch_deep_dive.md`):

- **12** (44%): zero advisor calls — executor stream error killed the session at turns 2–13, before any advisor tool call could form. These are pure executor instability. *(Highest confidence.)*
- **13** (48%): advisor called and **succeeded**, then a subsequent executor turn died with `Provider finish_reason: error` → no edits ever written. The advisor call did not cause the stream error; both are downstream of the same flaky provider window.
- **2** (7%): advisor called, **no stream errors**, empty patch — genuine advisor-induced early stop (`happy-dom`, `kysely`).

**So ~25/27 empties are explained by executor stream noise in the treatment window, not by the advisor extension.** The reason the baseline only had 4 is that **the baseline ran ~30 h earlier in a stable window** — verified directly: the same `narwhals`/`ink-grid-box-layout`/`yjs-map-conflict-detection` traces show **0** stream-error events in baseline vs **4–8** in treatment. The "6.8× empty-patch increase" is largely a between-windows provider-reliability delta, not an advisor regression.

---

## Q4. Why did full solves improve 2 → 5 despite mean collapse?

Because full solves are a **small-n binary** that rewards near-perfect→perfect flips, while mean partial is dragged down by the 27 zeros.

- The 5 advisor solves: `scc-bounded-memory-spilling`, `query-persist-restored-query-state`, `geo-shapeindex-serialization`, `bandit-structured-nosec-directives`, `true-myth-iterable-collection-combinators` — all **easy/medium**, all baseline partial already **0.98–1.0**, advisor nudged the last fraction over the line.
- Baseline's 2 solves included `actionlint-action-pinning-lint`, which advisor **lost** (1.0 → 0.985). Net flips ≈ +3.
- Plus one near-solve breakthrough on a hard task: `anko-default-function-arguments` went baseline-empty → advisor 0.983 (advisor unblocked a stuck baseline).

**Interpretation (Medium confidence):** advisor has a real, repeatable effect of **finishing** tasks the baseline nearly solved, and occasionally **unblocking** a stuck hard task. That signal is genuine but lives under a pile of executor-induced zeros. It does **not** redeem the mean; it explains why solves and mean moved in opposite directions.

---

## Q5. Prioritized fixes (with minimal tests / repro)

Root-cause order. The top fix is in the **harness**, not the extension — several specialist drafts over-indexed on advisor-extension retry, which cannot recover turns the executor already terminated.

### P0 — Harness: executor turn retry on `finish_reason: error` / stream-drop (HIGH leverage)
- **Why first:** recovers ~25 empty patches + ~6 severe non-empty regressions in one change. This is where the damage concentrates.
- **What:** in pi's turn/streaming loop, treat `stopReason:"error"` / `"Stream ended without finish_reason"` as retryable (exponential backoff, 1–2 attempts, preserve partial content where possible). Auto-retry already exists for one error type and worked (4/6 recovered); extend it to `finish_reason: error`.
- **Repro/test:** pick `narwhals-rolling-window-suite` and `ink-grid-box-layout` (baseline 0 stream errors, treatment 4–8, both empty under treatment). Re-run with retry enabled → expect non-empty patches and advisor calls to appear. Assert: `grep -c '"Provider finish_reason: error"'` per trace ≤ 1 after retry, and `patch_bytes > 0`.

### P1 — Treatment design: concurrent advisor-OFF control arm (HIGH leverage on interpretation)
- **Why:** the reused baseline is the core confound; without a same-window control **no** advisor efficacy claim is defensible — in either direction.
- **What:** on every rerun, run an advisor-disabled arm in the **same window** on the **same** task set, randomized/interleaved if possible. Compare deltas only within-window.
- **Test:** harness assertion that baseline and treatment arms share a run-batch timestamp window (±1 h); reject the comparison otherwise.

### P2 — Advisor extension: make advisor failures unambiguous + 1 retry (MEDIUM)
- **Why:** real bug, cheap, removes the "agent acts on an error string" risk. Today a failed/empty advisor call returns the error message as `content` text with `error` only buried in `details`; an executor may follow "advice" that is actually a failure notice.
- **What (grounded in `index.ts`):**
  - Return `isError: true` on the `execution_failed` / `empty_response` / `model_error` paths.
  - On `response.stopReason === "error"` *with* partial content, treat as failure, do not return the partial text as advice.
  - Add **1** retry with backoff around `completeSimple` for transient errors (advisor-side only; this is a belt-and-suspenders guard, not the main fix).
  - Fix cost accounting: `advisor_cost_usd_total` is **$0** because zai returns no `cost.total`. Add a per-provider price fallback or mark `cost.total` as `null`/unknown instead of `0`.
- **Test:** unit test the `execute` paths — (a) mock `completeSimple` throwing → assert `isError===true` and text starts with "Advisor unavailable", not advice; (b) mock returning `stopReason:"error"` with text → assert not returned as advice; (c) `loadConfig` clamping (`maxUsesPerRun` to 1–10). Pure node:test, no pi imports needed (mirror `advisor-signals.ts`'s testability pattern).

### P3 — Advisor prompt/verdict semantics: kill premature convergence (MEDIUM)
- **Why:** the clearest advisor-caused harm. `adaptix` got an "On track" verdict while explicitly noting "key files not yet read" → agent implemented on incomplete recon (208→44 turns, 0.999→0).
- **What:** split the verdict. Forbid any "ready to implement" signal while the executor has not (a) read the critical files the advisor itself flagged and (b) run verification. Add to `ADVISOR_SYSTEM_PROMPT`: *"'On track' is a direction judgment, not a completion signal; never imply implementation can finish while your own action items remain un-discharged."* Optionally enforce in `detectStage` (`advisor-signals.ts`): if stage is `initial` and `verificationCommands` is empty, the advisor must emit a recon action item, not a finish.
- **Test:** golden-trace test — feed the `adaptix` transcript prefix to the advisor and assert the response does **not** permit implementation completion while flagged files are unread. Regression test on the 4–6 named tasks.

### P4 — Advisor extension: `shouldNudge` exploration coverage (LOW)
- **Why:** cheap, small upside. `shouldNudge` only fires on `hasMutation && !hasVerification` (`advisor-signals.ts`). Adding an exploration nudge (≥3 reads, no mutation, first call) would raise call rate — but most no-call tasks died before nudge could fire, so impact is marginal. Include only if P0 lands.
- **Test:** `shouldNudge([read,read,read], 0, true, 3)` returns a non-null exploration nudge.

> **Deliberately NOT recommended as P0** (ponytail): per-call token-budget estimation, multi-provider fallback chains, task-complexity gating, force-initial-call. These add machinery for problems P0–P3 already cover or that need a clean control to justify. Revisit after the rerun.

---

## Q6. What to rerun, and what not to over-interpret publicly

### Rerun (after P0 lands)
1. **The ~31 stream-error-affected tasks** (25 empty + 6 severe non-empty) with **executor turn-retry enabled**, in a fresh window. Highest value; these are where the run is most likely mis-measured.
2. **A concurrent advisor-OFF control on the same task set in the same window** (P1). Without this, the rerun still can't attribute deltas cleanly.
3. Optionally the 4–6 premature-convergence tasks after P3, to test whether verdict-semantics fix changes their outcome.

### Do NOT rerun yet
- The full 113 **before** P0 — it will reproduce the same stream-error storm and burn budget confirming what we already know.

### Do not over-interpret publicly (until a controlled rerun exists)
- **"Advisor lowers mean partial by 0.24."** Confounded by the reused baseline + provider-noise window. **Not** publishable as an advisor effect.
- **"Advisor saves ~1.5M median tokens / 40% turns."** Artifact of truncated sessions, not efficiency.
- **"Empty-patch rate 6.8× under advisor."** ~93% executor-driven; not an advisor metric.
- **Advisor cost figures.** Tracking is broken (`$0`); report token counts only.

### Defensible now (with caveats)
- **Directional:** advisor enables breakthroughs on stuck hard tasks (10 large wins, 8/10 hard bucket) and can finish near-solved easy/medium tasks (+3 solves). The advisor *model* (`glm-5.2`) is stable and cheap on the advisor side (~4.7k tokens/call, near-zero advisor-side failures).
- **Diagnostic:** executor `finish_reason: error` is the dominant reliability failure in this run and must be fixed in the harness before any advisor A/B is meaningful.

---

## Confidence ledger

| Claim | Confidence | Basis |
|---|---|---|
| Executor stream errors dominate the empty-patch explosion | **High** | 25/27 empties have documented stream errors; baseline 0 vs treatment 4–8 on same tasks; mtimes ~30 h apart |
| Reused baseline confounds every delta | **High** | symlink → `ponytail-full-pilot-w2`; different timestamps; no concurrent control |
| Advisor guidance caused ~4–6 non-empty regressions | **Medium** | named tasks, contradictory "On track" verdicts in traces; no stream errors on those |
| 2 empty patches are pure advisor-induced stops | **Medium** | happy-dom/kysely: zero stream errors, advisor "don't commit" language, no edits |
| Advisor produced genuine wins / +3 solves | **High** | top_wins list, binary flips, hard-bucket concentration |
| Advisor-side `completeSimple` calls mostly succeeded | **High** | 101 calls, 536k tokens, near-zero advisor failures in traces |
| Cost tracking is broken for zai | **High** | `advisor_cost_usd_total: 0.0`; `cost.total ?? 0` in source |

---

## Appendix — evidence commands (reproducible)

```bash
# Confound: baseline ran ~30h earlier, far fewer stream errors on the SAME tasks
for t in narwhals-rolling-window-suite ink-grid-box-layout yjs-map-conflict-detection; do
  b=$(grep -c '"Provider finish_reason: error"' runs/advisor-glm52-full-w4/baseline/$t/rep0/pi.jsonl)
  a=$(grep -c '"Provider finish_reason: error"' runs/advisor-glm52-full-w4/pi-advisor-glm52/$t/rep0/pi.jsonl)
  echo "$t  baseline=$b  treatment=$a"
done
# baseline timestamps
ls -la --time-style=long-iso runs/advisor-glm52-full-w4/baseline/narwhals-rolling-window-suite/rep0/pi.jsonl
ls -la --time-style=long-iso runs/advisor-glm52-full-w4/pi-advisor-glm52/narwhals-rolling-window-suite/rep0/pi.jsonl
```
