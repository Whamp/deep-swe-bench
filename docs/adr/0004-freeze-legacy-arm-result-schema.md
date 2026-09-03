# 0004: Freeze the legacy `arm_*` names and `/arm` mount

## Context

ADR-0001 retired "arm" from the vocabulary in favour of "config": `--arm`
became `--config`, `arms/` became `configs/`. The retirement did not reach three
load-bearing surfaces, and a 2026-07 review confirmed they still say "arm":

- `result.json` carries `arm_pi_flags`, `arm_settings`, `arm_advisor`,
  `arm_models` on every rep.
- The config dir is mounted into the agent container as `/arm:ro`, and
  `harness/run.py` / `run_omp.py` thread a variable named `arm_cfg` throughout.
- `harness/run_state.SUMMARY_PREFIXES` includes `"arm_"` so dashboard
  projections read those fields.

Renaming would be a migration over the consumed `result.json` schema
(`harness/analyze.py`, the dashboard, and every historical result), and
ADR-0002's whole thrust was that usage/accounting fields must not be silently
perturbed.

## Decision

Freeze the names, not the complete result schema. Retain the `arm_*` result
fields, the `/arm:ro` mount, and the `arm_cfg` variable indefinitely.
`CONTEXT.md`'s "_Avoid_: arm" applies to new names only. New result versions may
add fields or migrate other data as long as they preserve the legacy `arm_*`
fields and their meanings. ADR-0009 applies this rule to result schema v2.

## Considered options

- **Rename `arm_*` → `config_*` with a migration.** Rejected: touches a schema
  consumed across analyze, the dashboard, and history. The purity win is not
  worth the corruption/regression surface (cf. ADR-0002's silent-zero fear), and
  `result_record` already emits the neutral `config` field as the canonical key.
- **Rename only the in-code variable/mount, leaving the JSON keys.** Rejected:
  a half-rename splits one concept across two words (`config_cfg` in code,
  `arm_*` on disk), which is worse than a clean, documented freeze.

## Consequences

- New code and new fields use `config` / `config_cfg`; the existing `arm_*`
  surfaces are left alone.
- `CONTEXT.md`'s `config` entry points here so the "_Avoid_: arm" rule is not
  read as "rename the legacy fields."
- Result schema migrations preserve the legacy `arm_*` fields unchanged. They
  can add versioned fields and alter unrelated retention behavior.
