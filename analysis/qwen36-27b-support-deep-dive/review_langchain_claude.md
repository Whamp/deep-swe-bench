# Qwen3.6-27B support deep dive: LangChain coalescing and Claude recursive delegation

## Review

- **Correct:** All three Claude patches preserved the pre-existing suite: `p2p_passed=31/31` in each `result.json`. LangChain rep1 preserved `232/232` pre-existing tests and passed `46/50` feature tests (`langchain-request-coalescing/rep1/result.json`).
- **Correct:** The model consistently recognized several explicit contract details: the LangChain public types and `Runnable.with_coalesce`; Claude's `delegate_task`, `tool_use_id`, unknown-agent, sub-agent-error, no-output, and circular cases. The patches and model-authored tests name these cases.
- **Blocker (critical):** Both timed-out LangChain implementations contain a broken concurrency lifecycle that blocks the verifier. Rep0 reaches `test_concurrent_invoke_coalescing` and fails, then stops making progress at `test_sequential_calls_not_coalesced`; rep2 stops during the second basic test, `test_invoke_returns_correct_result` (`langchain-request-coalescing/rep0/verifier/new.log`, `rep2/verifier/new.log`). Both verifier and agent hit timeout, so these are not merely slow verifier runs (`rep0/result.json`, `rep2/result.json`: `agent_exit="timeout"`, `verifier_exit="timeout"`, about 5,400 seconds each).
- **Blocker (high):** Every Claude patch missed the actual integration contract exercised by the verifier. All seven feature tests fail in every repetition while all 31 old tests pass (`claude-code-by-agents-recursive-delegation/rep{0,1,2}/verifier/ctrf.json` and `reward.json`). The repeated failures that expected the provider/agent to be called more than once show that the delegating agent was never successfully resumed through the tested public flow.
- **Note (high):** Scope was excessive in five of six patches. LangChain added 1,160, 2,347, and 1,090 lines respectively; Claude added net 1,186, 893, and 1,167 lines. This expansion increased the number of invented state machines/interfaces while leaving the central integration behavior unproved (`artifacts/model.patch`, measured with `git apply --numstat`).

## Sources and method

Read-only analysis covered:

- `results/Qwen3.6-27B-AWQ-BF16-INT4/high/baseline-qwen36-27b/{langchain-request-coalescing,claude-code-by-agents-recursive-delegation}/rep{0,1,2}/result.json`
- each repetition's newest `session/*.jsonl`
- each `artifacts/model.patch`
- verifier `new.log`, `ctrf.json`, `reward.json`, and captured verifier stdout where present
- `initial_context/user_prompt.txt`, which is the captured `/task/instruction.md`

The feature verifier source itself is not present in this checkout. Test names, assertions, and outcomes are available in the captured CTRF/XML/log artifacts. Conclusions below label deductions from those observations as **Inference**.

## Outcome matrix

| Task / rep | Patch | Agent / verifier | Feature result | Existing result |
|---|---:|---|---:|---:|
| LangChain rep0 | 42,134 B; +1,160 lines | timeout / timeout | unscored; log fails concurrent invoke and then stalls | unscored |
| LangChain rep1 | 79,435 B; +2,347 lines | 0 / 0 | 46/50 (92%) | 232/232 |
| LangChain rep2 | 41,902 B; +1,090 lines | timeout / timeout | unscored; stalls in second test | unscored |
| Claude rep0 | 58,779 B; +1,224/-100 | 0 / 0 | 0/7 | 31/31 |
| Claude rep1 | 33,121 B; +938/-45 | 0 / 0 | 0/7 | 31/31 |
| Claude rep2 | 39,530 B; +1,168/-1 | 0 / 0 | 0/7 | 31/31 |

## LangChain request coalescing

### Evidence

1. The requested interface is precise: one backend shared across invoke/stream/batch families; input-only canonical keys; replay from the start; fresh execution after completion; callback start/end for joiners; transparent transform/event/graph behavior; cancellation and stat reset on clear (`langchain-request-coalescing/rep0/initial_context/user_prompt.txt`).
2. The model chose a new deep implementation module in every repetition and a small `Runnable` entry point:
   - rep0: `libs/core/langchain_core/runnables/coalesce.py` +1,091; `base.py` +58; `runnables/__init__.py` +11.
   - rep1: `coalesce.py` +1,403; `base.py` +65; model-authored `test_coalesce.py` +865.
   - rep2: `coalesce.py` +1,029; `base.py` +50; no tests.
3. Rep0's patch defines `RunnableCoalesced` and repeats `batch_as_completed` three times and `abatch_as_completed` twice in the same added module (`rep0/artifacts/model.patch`, `coalesce.py` additions around the batch-as-completed methods). This is direct evidence of edit accretion rather than a settled design.
4. The three implementations do not even settle the required backend abstraction consistently: rep0 and rep1 use a `Protocol`; rep2 uses an `ABC`; rep1 invents `_RegistrationResult`, sync/async registration-result objects, four join-handle classes, and a wrapper not visibly inheriting the normal runnable binding base (`rep1/artifacts/model.patch`, `coalesce.py` class declarations).
5. Rep0 and rep2 wrote no tests. Rep1 wrote 865 lines of tests but still missed four verifier cases. Rep1 nevertheless achieved 46/50 and all 232 regressions, proving that a mostly working solution was available without a timeout (`rep1/result.json`, `verifier/reports/new.xml`).
6. Rep0's verifier output is decisive: basic invoke passes; concurrent invoke fails; different inputs passes; then the sequential-call test never completes before verifier timeout (`rep0/verifier/new.log`). Rep2 passes only wrapper construction and then hangs in ordinary invoke (`rep2/verifier/new.log`).
7. Both timeout rows spent the full 5,400-second agent budget and then also timed out in verification. The model did not reach a controlled stop (`rep0/result.json`, `rep2/result.json`).

### Inference

- **Orientation fork:** The model correctly located the public API seam (`Runnable` plus `runnables/__init__.py`) but treated the task as “implement every method now,” not “first prove one shared lifecycle.” The size and divergent helper taxonomies support this; there is no evidence of a minimal state-transition spec before editing.
  - **Do differently:** First write a six-transition table for one key: absent → owner; active → joiner; owner result/error → wake all and remove; clear → cancel all and reset; plus stream chunk append/replay. State exactly which lock protects which fields and how sync and async callers share the same entry.
- **Design fork:** The model rewrote too broadly. A 1,000–1,400-line module, duplicate method definitions in rep0, and rep1's numerous registration/join wrapper interfaces are disproportionate to the public contract. This complexity obscured ownership cleanup and cross-method sharing.
  - **Do differently:** Use one backend entry type and one explicit owner/join result. Keep canonicalization, lifecycle, and replay in the backend; keep `Runnable` methods thin. Do not invent result protocols unless a failing test requires them.
- **Concurrency-bounding fork:** Rep0/rep2 failed to guarantee “complete exactly once and delete active entry in `finally`.” The verifier hangs immediately after or during basic ownership tests. This is the characteristic externally observed failure of a waiter/entry left unresolved. The exact internal lock path cannot be proven without executing the patch, so the precise deadlock site remains unverified.
  - **Do differently:** Put backend completion/removal in `try/except/finally`; never wait while holding the registry lock; use bounded test waits (`Future.result(timeout=...)`, `asyncio.wait_for`) and assert `is_active(key) == false` after success, error, cancellation, and clear.
- **Edit fork:** Rep0's repeated definitions show patch-on-patch editing without deleting superseded code. Rep1 added an 865-line test file after constructing the implementation rather than driving it from small contract probes. Rep2 omitted tests entirely.
  - **Do differently:** Add tests in this order: two simultaneous invokes execute once; sequential invokes execute twice; thrown owner error wakes joiner and permits retry; sync owner + async joiner; stream late join replay; clear cancellation. Implement only enough for each test.
- **Validation fork:** The two timeout runs did not use a short, bounded concurrency probe before full validation. The first hidden concurrent/basic test exposed a hang that should have been caught in seconds. Rep1's own large test suite was not sufficient because four contract tests remained red.
  - **Do differently:** Run the smallest concurrency tests with a 10–30 second process timeout after every lifecycle change; then the task verifier subset; then full core tests. Record all four rep1 failure names before further edits rather than stopping at 46/50.
- **Stopping fork:** Rep0/rep2 continued until the harness killed them. Rep1 stopped and committed despite a binary failure (46/50). This is validation of the wrong stopping condition: “my authored tests/full regressions pass” rather than “all requested behavior passes and no call can block indefinitely.”
  - **Do differently:** Stop adding features once the patch exceeds a predefined budget; revert to the last green lifecycle. Do not declare completion while any feature test fails or any concurrency test lacks a timeout.

### Specific diagnosis requested

- **Rewrote too broadly:** yes, strongly supported in all LangChain reps.
- **Invented interfaces:** yes, especially rep1's registration and join-handle hierarchy; these are internal inventions not requested by the contract.
- **Failed to bound concurrency:** yes in rep0/rep2 as an observed verifier hang; rep1 was bounded enough to finish but still incomplete.
- **Validated the wrong thing:** yes. Rep0/rep2 lacked model tests; rep1's 865-line authored suite did not cover the four remaining verifier failures.

## Claude recursive delegation

### Evidence

1. Every repetition has the exact same score: feature `0/7`, existing `31/31`, partial `31/38 = 0.8157894736842105` (`claude-code-by-agents-recursive-delegation/rep{0,1,2}/result.json`). Thus 0.8158 is not partial feature success; it is entirely regression credit.
2. The seven failures are identical in every rep (`verifier/ctrf.json`):
   - circular delegation: expected an observed callback/spy call;
   - sub-agent error: expected more than one agent/provider call;
   - specified-agent execution: expected delegated behavior/output truthy;
   - no-text sub-agent: expected more than one call;
   - unknown agent: expected more than one call;
   - empty instructions: expected handled/rejected behavior truthy;
   - A→B→C: delegated instruction observed as `undefined`, expected `"Return OK"`.
3. Rep0 modified both `backend/handlers/chat.ts` and `backend/handlers/multiAgentChat.ts`, added `backend/handlers/delegation.ts`, and added 562 lines of tests. Its continuation branch in `multiAgentChat.ts` is keyed on a newly handled `ProviderResponse` with `response.type === "tool_use"` and `toolName === "delegate_task"` (`rep0/artifacts/model.patch`, `executeSingleAgent` hunk around old line 173).
4. Rep1 focused on `multiAgentChat.ts`, but also changed provider interfaces and implemented sub-agent execution through a new delegation helper described in its session as “runs sub-agent via HTTP.” It rewrote/truncated portions of `multiAgentChat.test.ts` during the trajectory, then validated its own helper and handler tests (`rep1/session/...jsonl`, final command sequence; `rep1/artifacts/model.patch`).
5. Rep2 integrated only `backend/handlers/chat.ts`, despite the instruction explicitly naming the multi-agent chat flow. It implemented recursion internally in a 463-line helper and added 528 lines of helper tests, but did not modify `multiAgentChat.ts` (`rep2/artifacts/model.patch`).
6. The model's final local validations were self-authored suites: rep0 ran `delegation.test.ts` and `multiAgentChat.test.ts`; rep1 ran those same files/full old suite; rep2 ran only `delegation.test.ts` at the end. The external feature suite subsequently failed all seven scenarios.
7. All repetitions committed and reported completion. Rep0's final summary asserted “supports recursive delegation”; rep2's commit made the same claim. The verifier directly contradicts those claims.

### Inference

- **Orientation fork:** The models did not establish the single public execution seam used by existing multi-agent requests and tests. Rep2 chose the wrong handler outright. Rep0 tried both handlers, and rep1 chose the named handler, but all three relied on a newly assumed representation of delegation rather than proving the real provider event shape and continuation call.
  - **Do differently:** Trace one existing `handleMultiAgentChatRequest` request end-to-end: request parser → agent registry lookup → provider factory → `executeChat` yielded event types → SSE serialization. Capture a real/mock provider `delegate_task` event from existing provider code before designing interception.
- **Design fork:** The patches invented large standalone delegation APIs instead of extending the existing execution loop. Rep1 additionally bypassed the provider/registry execution seam with a new HTTP-style sub-agent runner. This explains how helper tests can pass while verifier spies on the normal provider path see only one call.
  - **Do differently:** Keep delegation inside the existing `executeSingleAgent` recursion/loop. Resolve the target through the existing registry and invoke it through the same provider abstraction the top-level agent uses. Pass an explicit `chain: readonly string[]` context; do not introduce a second HTTP execution mechanism.
- **Continuation fork (root failure):** The common observable failure is failure to re-invoke the delegating agent through the tested path. Five tests report only one call where more than one is required. Even where a tool result object is built, the real delegating conversation does not receive it in a second normal execution.
  - **Do differently:** After the sub-agent finishes, append exactly one serialized tool-result message to the delegator's provider conversation and call that same delegator provider again. Assert call 1 receives original instructions, delegated call receives `instructions`, and continuation call receives JSON containing exactly `type`, `is_error`, `content`, `tool_use_id`.
- **Recursion fork:** The model claimed recursive support but did not propagate delegated instructions correctly through the tested A→B→C path (`undefined` instead of `"Return OK"`). Global/request maps and reference-counted scope machinery in reps 0/2 add cleanup risk and do not substitute for explicit recursion context.
  - **Do differently:** Implement `runAgent(agentId, prompt, chain)` recursively. Before descent, reject `chain.includes(agentId)`; on descent use `[...chain, agentId]`; impose a documented maximum depth as a safety backstop; always unwind via lexical `try/finally`. Unit-test A→B→C prompts and A→B→A cycle through the public handler, not helper functions.
- **Edit fork:** Rep0 touched five product/test files and both chat flows; rep1 altered provider types and rewrote an existing test file; rep2 built almost 1,000 lines of helper plus tests around the wrong handler. These are three different broad implementations with the same external zero.
  - **Do differently:** First add one failing public-handler integration test using the existing provider mock. Make success delegation pass with a small loop change, then add unknown/error/circular cases one at a time. Avoid changing provider interfaces until an actual provider payload proves a missing field.
- **Validation fork:** Validation asserted helper behavior and handcrafted event shapes, not the public integration seam. Passing 31 old tests only proves no regression; the identical 0/7 feature result proves none of the requested behavior was exercised successfully.
  - **Do differently:** Mirror each contract row as a black-box `handleMultiAgentChatRequest` test and assert provider call sequence, registry target, delegated prompt, streamed error policy, tool-use/result ID equality, and continuation payload. Run the external verifier before declaring done.
- **Stopping fork:** All three runs treated green self-authored tests and a commit as completion despite never observing the requested flow. Rep1 spent 76 turns/5.65M tokens, including repeated TypeScript narrowing and test-file repair, without returning to the integration premise.
  - **Do differently:** Stop after the first black-box delegation test remains red; inspect the yielded provider event and public handler rather than adding helper cases. Require at least one end-to-end captured stream showing tool_use → sub-agent text → matching tool_result → delegator continuation.

### Specific diagnosis requested

- **Rewrote too broadly:** yes in all Claude reps; rep0 is especially broad across both handlers, while rep2 is broad around the wrong handler.
- **Invented interfaces:** yes. The new delegation modules and, in rep1, provider-type/HTTP execution path were not grounded in the verified public flow.
- **Failed to bound recursion:** yes as a support/design deficiency. Circular bookkeeping was added, but the actual A→B→C contract failed and there was no externally proved recursion/depth boundary.
- **Validated the wrong thing:** decisively yes. All authored/old tests passed while every feature test failed.

## Checkable support mechanisms

1. **Seam map gate:** Before editing, require a short artifact naming the public request handler, registry lookup function, provider method, actual yielded delegation event shape, and stream serializer. Check it against file/line links.
2. **Contract-matrix tests:** Generate one black-box test per sentence-level contract. For Claude, assert exact call order and arguments through `handleMultiAgentChatRequest`. For LangChain, assert execution count, result/error propagation, callback counts, active state, and stats.
3. **Concurrency watchdog:** Wrap every coalescing concurrency test in a 10-second outer process timeout and every waiter in a 1-second future timeout. On failure dump thread/task stacks and backend active keys. This would have converted both 5,400-second LangChain timeouts into local, actionable failures.
4. **Lifecycle invariants:** Add reusable assertions: no lock held while waiting; every owner resolves every waiter exactly once; active entry removed after success/error/cancel; clear cancels waiters and zeros stats; a subsequent identical call executes fresh.
5. **Real payload fixture:** Derive the Claude `delegate_task` fixture from the provider implementation's emitted object, not a model-invented `ProviderResponse`. Fail test compilation when the provider shape changes.
6. **Public-flow spy:** Spy on existing registry/provider creation and require calls `[delegator, sub-agent, delegator]`; verify prompts `[original, delegated instructions, tool_result JSON]`. Add A→B→C and A→B→A variants.
7. **Patch-size tripwire:** Warn at >400 new product lines or >3 product files for either task; require a written reason and a smaller alternative. Duplicate method-name detection would have caught LangChain rep0's repeated batch-as-completed definitions.
8. **Feature-verifier stopping rule:** Completion requires all feature tests, not merely old tests or authored tests. Record F2P and P2P separately so Claude's 0.8158 cannot be mistaken for feature progress.
9. **Bounded recursion context:** Require an immutable chain plus maximum depth and tests proving cleanup after errors. Prohibit process-global cycle state unless concurrent request isolation is demonstrated.
10. **Evidence-based final summary:** Auto-compare completion claims against verifier output. Claims such as “supports recursive delegation” must include a passing black-box test name and captured provider call sequence.

## Residual risks

- The exact internal deadlock statement in LangChain reps 0/2 is not proven because the verifier source/worktree is absent and this review was read-only. The externally visible stall locations and lifecycle symptoms are proven.
- The precise provider event-shape mismatch in Claude is inferred from patch branches plus the uniform one-call failures. What is proven is that no patch re-entered the tested execution path successfully.
- LangChain rep1's four failing feature test names were not available in the already-read excerpts; only the aggregate 46/50 result is asserted here.

```acceptance-report
{
  "criteriaSatisfied": [
    {
      "id": "criterion-1",
      "status": "satisfied",
      "evidence": "Concrete severity-ranked findings cite all six result.json files, verifier logs/CTRF, session JSONL command sequences, and model.patch paths; evidence is separated from inference."
    }
  ],
  "changedFiles": [
    ".pi-subagents/artifacts/outputs/ed8ad123/analysis/qwen36-27b-support-deep-dive/review_langchain_claude.md"
  ],
  "testsAddedOrUpdated": [],
  "commandsRun": [
    {
      "command": "find/ls/read result, session, patch, prompt, and verifier artifacts for both tasks across rep0-rep2",
      "result": "passed",
      "summary": "Located three completed repetitions per task and read the newest session and requested evidence classes."
    },
    {
      "command": "git apply --numstat <each artifacts/model.patch>",
      "result": "passed",
      "summary": "Measured exact per-file patch breadth for all six trajectories without applying patches."
    },
    {
      "command": "jq verifier reward/CTRF and session tool-call records",
      "result": "passed",
      "summary": "Confirmed Claude 0/7 F2P and 31/31 P2P in every row, enumerated all seven failures, and reconstructed validation/commit commands."
    }
  ],
  "validationOutput": [
    "LangChain rep0: agent timeout + verifier timeout; concurrent invoke failed, later sequential test stalled.",
    "LangChain rep1: 46/50 F2P, 232/232 P2P, partial 0.9858156028368794.",
    "LangChain rep2: agent timeout + verifier timeout; verifier stalled during basic invoke.",
    "Claude reps 0-2: each 0/7 F2P, 31/31 P2P, partial 0.8157894736842105."
  ],
  "residualRisks": [
    "Exact LangChain deadlock statement remains unverified without the task verifier source or executable patched worktree.",
    "Exact Claude provider event-shape mismatch is inferred; failure to resume the tested delegator flow is directly evidenced.",
    "Repository-wide staged state was not mutated or rechecked; no files were staged by this read-only reviewer."
  ],
  "noStagedFiles": true,
  "diffSummary": "Review artifact only; no product or test files edited. Analyzed patches range from ~33 KB to ~79 KB and identify concurrency lifecycle and integration-seam failures.",
  "reviewFindings": [
    "blocker: langchain-request-coalescing/rep0 and rep2 verifier/new.log - generated coalescing lifecycle hangs verifier after basic/concurrent calls.",
    "blocker: claude-code-by-agents-recursive-delegation/rep0-rep2 verifier/ctrf.json - all seven feature tests fail; delegator is not resumed through tested public flow.",
    "high: all artifacts/model.patch files - implementation breadth and invented helper interfaces outpaced end-to-end validation."
  ],
  "manualNotes": "Read-only trajectory review. The output report is the only file written, as required by the runtime output contract."
}
```
