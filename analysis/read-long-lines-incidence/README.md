# Read long-line incidence in baseline sessions

## Decision

Do not fund a full 36-task paired comparison for the 2,000-character line cap. In the primary clean-stock baseline scope, the cap would affect 15 of 10,325 read results (0.145%) and 12 of 648 reps (1.85%). One task, `fd-deterministic-multi-key-sorting`, accounts for 10 of the 12 activating reps.

If behavioral validation is still useful, target `fd-deterministic-multi-key-sorting` first. Add `pest-character-class-coalescing` as a high-magnitude case and `meriyah-explicit-resource-declarations` as a repository-source case. Treat `dateutil-rfc5545-timezone-interop` as workflow-dependent because its largest long lines came from agent-created files under `/tmp`.

## Primary result

The primary scope contains config identities `baseline` and `baseline@1.0.0`:

- 648 reps with 648 readable newest-root sessions
- 36 tasks
- 10,325 read results
- 15 read results with at least one line over 2,000 characters
- 12 activating reps across 3 tasks
- 42,553 source characters omitted by the cap
- 2,662 characters added by recovery notices
- 39,891 net characters removed, 0.0818% of all read-result characters

No observed long line used the `limit=1` full-line escape hatch. No read result used the old 50KB first-line censor, so the primary count has no known right-censoring from that behavior.

## Scopes

`data/primary/` is the decision scope. It includes only the generic clean-stock config identities `baseline` and `baseline@1.0.0`.

`data/model-adapter-sensitivity/` adds model-specific baseline lineages whose provider or sampling adapters leave the stock read tool in place. It contains 1,117 reps and finds one additional task, `pest-character-class-coalescing`. This scope includes the primary reps; do not add its totals to the primary totals.

`data/historical-control/` scans the prompt-bearing historical config `baseline-preamble-orchestration` separately. It covers 900 readable sessions from 918 result records and all 113 tasks. It finds four activating tasks: `fd-deterministic-multi-key-sorting`, `abs-module-cache-flags`, `obsidian-linter-auto-table-of-contents`, and `koota-deferred-mutation-buffer`. Prompt differences make this a discovery scope, not an estimate of clean-stock activation.

## Method

`scan_read_long_lines.py` reads each rep's newest non-recursive root session, matching the selection rule in `harness/parse_usage.py`. It pairs assistant `read` tool calls with `toolResult` records by tool-call id.

For every returned text line, the scanner uses JavaScript-compatible UTF-16 code-unit length. An ordinary read line of length `L > 2,000` contributes `L - 2,000` omitted characters. A read with `limit=1` is exempt because the active read implementation returns that line in full.

The active implementation was probed before the scan. It keeps the first 2,000 characters and appends this notice:

```text
[Line N shortened: showing 2,000 of L characters. Use offset=N, limit=1 to read the complete line.]
```

Net characters removed subtract the exact notice length, its separators, and the two newlines before the notice block from the omitted source characters.

The scanner records paths, line positions, and lengths. It does not copy long-line content into this report.

## Reproduce

Run from the repository root. Point `--results` at the primary checkout because ignored benchmark results are not duplicated into this worktree.

```sh
python3 analysis/read-long-lines-incidence/scan_read_long_lines.py \
  --results /home/will/evals/deep-swe-bench/results \
  --configs baseline baseline@1.0.0 \
  --out /tmp/read-long-lines-primary
```

The committed compact evidence consists of `summary.json`, `by-task.csv`, `by-model-thinking-config.csv`, and `activations.csv` for each scope. The scanner also emits rep-level and read-level CSV files when rerun.
