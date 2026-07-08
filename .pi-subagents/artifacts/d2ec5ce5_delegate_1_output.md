# happy-dom deterministic IntersectionObserver rep1 loss review

## Bucket

- **Primary bucket: under-implementation / async polling regression in the CodeGraph patch.** CodeGraph’s solution implemented a one-shot queued callback path and did not continue checking observed targets after the initial delivery, so a threshold-change test timed out.
- **Secondary: CodeGraph overhead/over-exploration, but not wrong-file/wrong-layer.** Both runs changed only `packages/happy-dom/src/intersection-observer/IIntersectionObserverInit.ts` and `packages/happy-dom/src/intersection-observer/IntersectionObserver.ts`; CodeGraph spent far more tokens/cost and added structural checks, but stayed in the right files.

## Evidence bullets

- **Outcome delta:** clean Pi solved fully (`reward_binary=1`, `f2p=14/14`, `p2p=9/9`), while CodeGraph lost one challenge test (`reward_binary=0`, `f2p=13/14`, `p2p=9/9`, partial `0.9565`). This is not an existing-test regression; p2p stayed green.
- **Verifier failure:** CodeGraph failed `[f2p] IntersectionObserver > observe() > Detects threshold crossings in subsequent async delivery cycles` with `Test timed out in 500ms` (`new.xml`/`ctrf.json`; packet’s verifier tail was blank).
- **Patch driver:** baseline added a persistent `#timer`/`#schedule()` loop that delivers queued records, re-checks intersections, then reschedules. CodeGraph added `#isQueued`/`#queueCallback()` and calls it only from `observe()`; the timer drains existing `#records` but does **not** re-run `#checkForIntersections()` or reschedule another polling cycle.
- **Why that maps to the failed test:** CodeGraph checks intersections during `observe()` and `takeRecords()`, but not in later async cycles. After the initial callback, geometry changes that cross thresholds are never discovered unless `takeRecords()` is called, so the hidden async-threshold test waits until timeout.
- **Trajectory signal:** CodeGraph used six `codegraph` commands and read extra context (`ResizeObserver.ts`, `BrowserWindow.ts`), with the same 31 turns/33 tool calls but +269,827 tokens and +$0.187 cost. The extra structural exploration/checking did not catch the missing behavioral polling loop.
- **Patch-size signal:** CodeGraph’s patch was larger (`357` changed lines / `11,991` bytes vs baseline `298` / `10,841`) but not broader. Extra machinery (`previousThresholdIndex`, `#getWindow()`, duck-typed `#isElement()`, frozen `thresholds`) was adjacent, not the root failure.
- **Classification:** not variance: the loss has a concrete deterministic verifier timeout and a direct implementation gap. Not wrong-layer/wrong-file. Best explanation is **under-implementation caused by implementation-choice divergence**, with mild CodeGraph-induced over-exploration/overhead.