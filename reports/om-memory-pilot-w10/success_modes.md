# OM success modes

Source: `runs/om-memory-pilot-w10/reports/paired_manifest.json` (aligned with `pair_2_new_solves.md`, `pair_3_pathology_rescues.md`, `pair_4_hard_bucket_wins.md`, `pair_6_cheap_wins.md`, `pair_7_expensive_wins.md`).

| bucket | count | rule / read | examples |
|---|---:|---|---|
| New full solves | 8 | `baseline.reward_binary != 1 && om.reward_binary == 1` | `eicrud-keyset-pagination-cursor`; `helm-unified-manifest-stream`; `textual-richlog-follow-state` (+5) |
| Baseline pathology rescues | 4 | 4 of 5 pathological baselines (`reward_binary == -1` or empty patch) were rescued; `wasmi-trap-coredumps` was the miss | `anko-default-function-arguments`; `kgateway-consistent-hash-policy`; `kombu-single-active-consumer-priority` (+1) |
| Hard-task partial jumps | 4 | marquee hard rows by `Δpartial` (26 hard rows improved by `> 0.05` overall) | `mashumaro-flattened-dataclass-fields`; `fastapi-implicit-head-options`; `kombu-single-active-consumer-priority` (+1) |
| Cheap-or-efficient wins | 13 | strict wins/ties with lower `total_tokens` + `tool_calls`; 21 cheaper matches total (`opa-rego-rule-profiling` was the one failure) | `ts-pattern-match-each`; `pebble-durability-wait-apis`; `fd-deterministic-multi-key-sorting` (+10) |
| Integration-completeness wins | 7 | cross-layer / fixture / golden regeneration showcase | `koota-pair-relation-tracking`; `fastapi-implicit-head-options`; `yaegi-go-embed-directives` (+4) |

*Buckets overlap; counts are story counts, not a partition.*
