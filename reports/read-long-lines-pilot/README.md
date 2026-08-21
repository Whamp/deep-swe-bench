# Read-long-lines staged pilot report

This report compares stock Pi with `read-long-lines@1.0.0` on matched DeepSWE
cells. The current snapshot includes four completed model leaves:

- `gpt-5.6-sol/low`
- `gpt-5.6-terra/low`
- `gpt-5.6-luna/low`
- `deepseek-v4-flash-0731/low`

Each leaf contains two tasks, two configs, and three reps: 24 matched pairs and
48 trajectories. GLM-5.2 is deferred until its quota-paused baseline and
extension plans finish.

## Rebuild

Run from the repository root and point `--results-root` at the canonical result
tree:

```bash
uv run python reports/read-long-lines-pilot/build_read_long_lines_report.py \
  --results-root /home/will/evals/deep-swe-bench/results \
  --models sol terra luna flash
```

After GLM-5.2 completes, regenerate with:

```bash
uv run python reports/read-long-lines-pilot/build_read_long_lines_report.py \
  --results-root /home/will/evals/deep-swe-bench/results \
  --models sol terra luna flash glm
```

The builder rejects missing pairs, model/thinking mismatches, provenance drift,
unexpected Pi flags, baseline/treatment settings differences, config-authored
prompt text, or missing extension registration telemetry.

## Primary estimands

The report answers activation efficiency at two narrow boundaries:

1. **Activated read result.** Extension telemetry identifies the exact read and
   reconstructs the unshortened result from omitted characters minus inserted
   notice overhead. A paired baseline result is treated as an independent exact
   match only when normalized path, offset, and limit all agree.
2. **Exploration through first mutation.** Native assistant-message usage is
   summed from session start through the assistant message containing the first
   `edit` or `write` call. That message is included because its provider request
   and generated tool call consume tokens before the mutation executes. Input,
   cache-read, output, reasoning, total tokens, and cost remain separately
   available in the snapshot.

Whole-session usage is retained only as a downstream sensitivity metric because
implementation and validation divergence can dwarf a small read-result change.
The current five-pair activated cohort was manually checked for source-mutating
shell commands before the `edit`/`write` boundary; none were found. Repeat that
check when adding a new model cohort.

## Artifacts

- `index.html` — self-contained report
- `data/snapshot.json` — versioned metrics and complete pair table
- `packets/*.json` — paired trajectory packets

Packet selection is fixed before review: any binary solve flip, absolute partial
reward movement of at least `0.1`, or actual long-line preview activation. Packets
exclude raw model reasoning and raw tool payloads.
