The pi-dynamic-workflows config adapter turns the initial benchmark task into a `pi-workflow` request and forces use of the `workflow` tool.

When writing workflow scripts for this benchmark:
- Always call the `workflow` tool with `background: false` so the benchmark harness waits for the workflow result before the cell ends.
- Tag every `agent()` call with a tier: `small` for repository inventory/search, `medium` for implementation or focused test/debug analysis, and `big` for final synthesis, judgment, or cross-context decisions.
- Use bounded fan-out. Prefer a few high-signal agents over broad speculative spawning.
- Keep all implementation work and the final commit in `/app`.
