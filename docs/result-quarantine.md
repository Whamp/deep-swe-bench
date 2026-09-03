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
- `om-no-executor-projection.jsonl` records stock headless
  pi-observational-memory runs that folded memory without projecting it into the
  executor context during single-shot DeepSWE tasks. Result-cell rows keep the
  compact result, quarantine provenance, and patch and session digests. Artifact
  rows retain metadata and bounded excerpts for config-level notes and logs. The
  full source remains recoverable from the archive URI recorded in the ledger
  and manifest. Include this ledger in cross-approach efficacy tables only when
  the analysis explicitly studies that failure mode.

`projected-om` is not quarantined by this rule because it is the intentional
isolation treatment that injects memory content into executor-visible context.

The local `results/_contaminated/manifest.jsonl` records moved directories with
original path, quarantine path, timestamp, category, and reason. A collapsed
category also records `retention`, `compact_ledger`, and `raw_archive`.

Do not symlink quarantined data into the canonical results layout. Analysis
finds configs by globbing `results/<model>/<thinking>/<config>`, so a symlink can
silently reintroduce invalid cells.

See [ADR-0009](adr/0009-compact-verifier-evidence.md) for the archive,
compaction, and recovery rules.
