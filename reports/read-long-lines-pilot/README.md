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

## Artifacts

- `index.html` — self-contained report
- `data/snapshot.json` — versioned metrics and complete pair table
- `packets/*.json` — paired trajectory packets

Packet selection is fixed before review: any binary solve flip, absolute partial
reward movement of at least `0.1`, or actual long-line preview activation. Packets
exclude raw model reasoning and raw tool payloads.
