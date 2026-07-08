I now have definitive evidence. The smoking guns:

1. **SEAM `new.xml` is degenerate** — all 7 "passed", `time=0`, **no stdout, no failures** — while the SEAM `base_backend.xml` (same reporter) captures **real timings (0.007s) and stdout**. So the new report is anomalous.
2. **SEAM verifier crashed**: `FATAL ERROR: ... JavaScript heap out of memory` (heap OOM) — AFTER writing the bogus `F2P 7/7`.
3. **SEAM's code cannot genuinely pass**: it builds `providerRequest` with **no `context` field** (grep confirms zero `context` references), so `orchestratorCalls[1].context` is `undefined` → the 5 context-dependent gold tests (lines 263/331/389/526/590) must fail exactly like OLD's.
4. **SEAM infinite-loops on the circular test**: `runDelegatedAgent` returns a tool_result (not a terminal) on circular detection, the while-loop re-invokes the agent forever; the circular mock re-emits `delegate_task` every call → unbounded heap growth → OOM. (OLD instead `return`s immediately on circular → caught as a clean per-test stack overflow → real 2/7.)
5. **OLD genuinely scored 2/7** with a real report (5 failures, all `expected ... context` / `expected null not to be null`); OLD fed the tool_result back via `message` (recursion), never the provider `context` array seam.

This "seam_gain" is a **verifier false-positive** (OOM crash → degenerate all-pass JUnit), not a skill-driven solve.

```json
{
  "task": "claude-code-by-agents-recursive-delegation",
  "rep": 0,
  "direction": "seam_gain",
  "primary_bucket": "likely-variance",
  "mechanism": "OLD's genuine defect is a wrong seam/layer: it feeds the delegation tool_result back to the orchestrator via `request.message` (recursive executeSingleAgent re-entry) and never populates the provider `context` array, so the gold tests in tests/handlers/recursiveDelegation.test.ts (which assert orchestratorCalls[1].context holds the tool_result via findToolResultInContext) see `context === undefined` and fail 5/7; OLD's own tests targeted the wrong file (multiAgentChat.test.ts) with a message-based contract and passed 11/11, masking the defect. SEAM did NOT fix this: its patch ALSO builds providerRequest with no `context` field (grep: zero `context` references) and feeds back via a while-loop `nextMessage`, so it is structurally incapable of passing the same 5 context tests. Worse, SEAM's runDelegatedAgent returns a tool_result (not a terminal) on circular-delegation detection, so its while-loop re-invokes the agent forever against the circular gold-test mock (which re-emits delegate_task on every call) -> unbounded heap growth -> the vitest process crashed with 'JavaScript heap out of memory'. That OOM produced a degenerate all-pass JUnit report (new.xml: 7 passed, time=0, no stdout, no failures), which the grader trusted as F2P 7/7. So the observed 7/7 is a verifier false-positive, not a real solve; the seam-checkpoint skill text did not drive a genuine improvement.",
  "seam_text_plausibly_mattered": false,
  "confidence": "high",
  "evidence_bullets": [
    "Gold f2p tests live in a SEPARATE file backend/tests/handlers/recursiveDelegation.test.ts (tasks/.../tests/test.patch), not the agents' edited multiAgentChat.test.ts; both agents validated the wrong file/interface.",
    "OLD verifier reports/new.xml: 5 real failures with real timings/stdout: 'should execute specified agent' (line 263: expected undefined to be defined = continuationCall.context), 'communicate sub-agent errors' (331), 'handle unknown agent' (389), 'multi-level A->B->C' (526), 'sub-agent no text' (590) - all 'expected null not to be null' from findToolResultInContext(continuationCall.context ?? []) returning null. reward.json f2p 2/7 is genuine.",
    "OLD multiAgentChat.ts feeds back via recursion: `yield* executeSingleAgent(agentId, { ...request, message: JSON.stringify(toolResult) }, ...)` - message-based, no `context`; OLD terminates circular via `if (toolResult.content.toLowerCase().startsWith('circular')) return;`.",
    "SEAM model.patch: providerRequest = { message: nextMessage, sessionId, requestId, workingDirectory } - NO context field; `grep -n context` on the SEAM patch returns zero matches. So orchestratorCalls[1].context is undefined and the 5 context gold tests cannot genuinely pass.",
    "SEAM runDelegatedAgent circular branch yields an error then `return createToolResult(toolUseId, content, true)` (not a terminal); executeSingleAgent sets nextMessage=that tool_result, delegated=true, breaks, and the `if(!delegated) return` guard is skipped -> while(true) re-invokes the agent forever. The circular gold-test mock re-emits delegate_task on every executeChat call -> infinite loop.",
    "SEAM logs/verifier.stdout.txt ends with 'FATAL ERROR: Ineffective mark-compacts near heap limit Allocation failed - JavaScript heap out of memory' AFTER writing reward.json f2p 7/7 - confirming the vitest process crashed during the f2p run.",
    "SEAM reports/new.xml is degenerate: 7 testcase all status=passed, time=0, zero system-out, zero failures - whereas the SAME reporter's reports/base_backend.xml captures real per-test times (0.007s/0.014s) and stdout, proving the new.xml is an OOM artifact, not a real run.",
    "OLD logs/verifier.stdout.txt shows a 'RangeError: Maximum call stack size exceeded' at multiAgentChat.ts:121 - OLD's recursion also non-terminates in some cases, but as a catchable stack overflow, so vitest recorded clean per-test results (real 2/7). SEAM's while-loop instead heap-OOM'd and crashed the process (false 7/7).",
    "Reference solution/solution.patch confirms the verified seam: it threads a ProviderContext[] conversation and sets `context: agentConversation.length>0 ? [...agentConversation] : undefined` on currentRequest, pushing {role:'user', content: JSON.stringify({type:'tool_result',...})} into context - exactly what the gold tests assert. Neither agent implemented this context-array seam.",
    "Packet metrics corroborate no real quality gain on the patched seam: SEAM patch (15547B, +321/-22) is larger but adds the heap-crashing loop; tokens -269k and wall +6s are not evidence of a more-correct delegation seam."
  ],
  "f2p_mapping": {
    "note": "OLD = genuine 2/7; SEAM = reported 7/7 but FALSE POSITIVE from verifier OOM (degenerate all-pass new.xml).",
    "old_skill": {
      "passed": [
        "tests/handlers/recursiveDelegation.test.ts > should block circular delegation (terminates via `if circular return`; circular error present in stream)",
        "tests/handlers/recursiveDelegation.test.ts > should reject or handle empty instructions (only checks rejected||handled; frontend 'No' text satisfies handled)"
      ],
      "failed": [
        "should execute specified agent ... -> line 263 expect(continuationCall?.context).toBeDefined() = 'expected undefined to be defined'; tool_result fed via request.message not context array",
        "should communicate sub-agent execution errors back to orchestrator -> line 331 findToolResultInContext(continuationCall.context ?? []) = null",
        "should handle unknown agent in delegation gracefully -> line 389, same context-array miss",
        "should support multi-level delegation (A->B->C) -> line 526, same context-array miss",
        "should handle sub-agent that returns no text -> line 590, same context-array miss (content fed via message)"
      ],
      "root_cause": "wrong seam/layer: delegation tool_result delivered through request.message (recursive re-entry) instead of the provider context array; agent's own tests were authored against the wrong file/interface and passed, hiding the defect."
    },
    "seam_skill": {
      "reported": "7/7 (reward.json f2p_passed=7)",
      "genuine_outcome": "false positive - SEAM providerRequest has no `context` field so the same 5 context gold tests cannot pass, and SEAM infinite-loops (heap OOM) on the circular test; it would genuinely score <=1/7 (only 'reject empty instructions' terminates+passes).",
      "delta_that_recovered_5_f2p": "none real - the 5-test swing is the degenerate all-pass JUnit (time=0, no stdout) emitted when vitest heap-OOM'd on SEAM's non-terminating circular delegation; the grader trusted it. Not a patch improvement."
    }
  }
}
```