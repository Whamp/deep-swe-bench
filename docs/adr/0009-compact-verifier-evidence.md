# 0009: Keep compact verifier evidence in result records

## Context

The local `results/` tree reached 25.11 GiB in September 2026. Verifier artifacts accounted for 14.18 GiB. Structured CTRF and JUnit reports used 13.58 GiB, raw suite logs used 3.52 GiB, and `logs/verifier.stdout.txt` used 981.68 MiB. These categories overlap because each cell can contain more than one representation of the same test run.

The existing `result.json` files retained scores and aggregate pass counts, but they did not retain failed test names and diagnostics. Deleting all verifier data would preserve efficacy analysis while making later failure analysis much weaker.

The `results/_contaminated/om-no-executor-projection/` category used another 4.19 GiB. Those cells document a known invalid treatment where observational memory never reached the executor. They remain useful as a diagnostic population, but they do not justify retaining full sessions and verifier output on the workstation.

## Decision

Version result records independently from the frozen legacy `arm_*` names. New and migrated results use `result_schema_version: 2`. They keep every existing top-level field and add `verifier_summary` with `schema_version: 1`.

The verifier summary contains:

- aggregate CTRF counts and verifier tool identity when CTRF exists;
- every failed, skipped, pending, or otherwise non-passing test record;
- test name, status, suite, file, duration, message, and trace fields when supplied by CTRF;
- at most 16 KiB for each message or trace, split between the beginning and end, with original and retained byte counts;
- the final 32 KiB of verifier stdout when CTRF is absent or the verifier exits unsuccessfully;
- parsed cgroup memory-event counters;
- the file count and byte size of the raw evidence represented by the summary.

Future result writers prune `verifier/` and `logs/verifier.stdout.txt` by default. They preserve patches, sessions, initial context, agent logs, usage traces, and provenance. Set `DEEP_SWE_RETAIN_RAW_VERIFIER_EVIDENCE=1` before execution or verifier-only recovery to keep the full raw verifier files for a forensic run.

A writer may prune raw files only after it has atomically replaced `result.json` and reread a valid schema-v2 summary. A restart finds a compact result with leftover raw files and finishes the prune without rebuilding the summary.

Historical migration uses `scripts/compact_verifier_results.py`. Dry-run is the default. The migration compares overlapping fields in `verifier/reward.json` and `result.json`. It reports and preserves a cell when those values disagree or when it cannot parse the evidence.

Before historical cleanup, store a complete compressed snapshot outside the workstation and verify its SHA-256 digest. The September 2026 migration stores this snapshot on `endurance` under `/mnt/user/backups/AI/deep-swe-bench/`.

After result compaction, replace `results/_contaminated/om-no-executor-projection/` with `results/_contaminated/om-no-executor-projection.jsonl`. Result-cell rows contain the full compact result, cell path, quarantine provenance, patch size and SHA-256, session size and SHA-256, and raw archive URI. Category-artifact rows preserve the path, size, SHA-256, and a bounded text excerpt for files stored outside result cells. Update matching `manifest.jsonl` rows before removing the source directory.

## Operational sequence

Run the validator first:

```sh
python3 scripts/compact_verifier_results.py compact \
  --results-root /home/will/evals/deep-swe-bench/results
```

After verifying the external snapshot, apply safe cell migrations:

```sh
python3 scripts/compact_verifier_results.py compact \
  --results-root /home/will/evals/deep-swe-bench/results \
  --apply
```

The command returns a nonzero status when it preserves any invalid or unreadable cells. Review its `issues` array. Do not delete those raw files manually.

Dry-run and then apply the quarantine collapse with the exact archive URI:

```sh
python3 scripts/compact_verifier_results.py collapse-quarantine \
  --results-root /home/will/evals/deep-swe-bench/results \
  --category om-no-executor-projection \
  --archive-uri 'endurance:/mnt/user/backups/AI/deep-swe-bench/<snapshot>.tar.zst'

python3 scripts/compact_verifier_results.py collapse-quarantine \
  --results-root /home/will/evals/deep-swe-bench/results \
  --category om-no-executor-projection \
  --archive-uri 'endurance:/mnt/user/backups/AI/deep-swe-bench/<snapshot>.tar.zst' \
  --apply
```

## Consequences

Current efficacy analysis remains compatible because the legacy score, usage, config, and provenance fields stay at the top level. Failure analysis reads `verifier_summary` instead of assuming CTRF or stdout files exist.

Exact raw reconstruction now depends on the external snapshot unless a run requested forensic retention. This is deliberate. The compact result retains the information used for ordinary scoring and diagnosis, while the archive remains the recovery path for unusual investigations.

The six historical cells whose reward and result fields disagreed during the September 2026 dry-run retain their raw files until someone resolves those discrepancies.
