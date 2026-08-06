# Result quarantine policy

Some result directories are intentionally moved out of the normal
`results/<model>/<thinking>/<config>/...` layout so broad analyses do not include
invalid or diagnostic runs by accident.

Local quarantine root:

```text
results/_contaminated/
```

Categories:

- `harness-failure/` — invalid because harness/config plumbing was broken.
  Current examples include the old
  `pi-recursive-compromised-readonly-tools-20260702` run, where recursive child
  read-only `grep`/`find` tools lacked working `rg`/`fd` binaries. Confirmed
  execution also moves a result-less cell containing partial attempt artifacts
  under `harness-failure/incomplete-cell-attempts/` before retrying it. This
  prevents native sessions and provider usage from separate attempts being
  combined into one canonical result.
- `om-no-executor-projection/` — stock headless pi-observational-memory runs
  that recorded/folded observations and reflections but did not project OM
  content into the executor context during single-shot DeepSWE task execution.
  These runs remain useful for failure-mode and mechanism analysis, but should
  not appear in cross-approach efficacy tables unless explicitly labeled.

`projected-om` is not quarantined by this rule because it is the intentional
isolation treatment that injects memory content into executor-visible context.

The local `results/_contaminated/manifest.jsonl` records moved directories with
original path, quarantine path, timestamp, category, and reason.
