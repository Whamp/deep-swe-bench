# pi-observational-memory DeepSWE report assets

Deterministic assets and analysis generated from `paired_manifest.json`.

## PNG assets

- `baseline-vs-om-scatter-card.png`
- `difficulty-bucket-card.png`
- `partial-delta-waterfall-card.png`
- `quality-vs-token-tradeoff-card.png`
- `readme-style-benchmark-card.png`
- `regression-modes-card.png`
- `success-modes-card.png`

## Analysis reports

- `deep_dive_synthesis.md`
- `difficulty_causal_analysis.md`
- `initial_summary.md`
- `memory_mechanics.md`
- `pair_0_top_wins.md`
- `pair_1_top_losses.md`
- `pair_2_new_solves.md`
- `pair_3_pathology_rescues.md`
- `pair_4_hard_bucket_wins.md`
- `pair_5_medium_easy_regressions.md`
- `pair_6_cheap_wins.md`
- `pair_7_expensive_wins.md`
- `public_framing_notes.md`
- `regression_failure_modes.md`
- `resource_tradeoffs.md`
- `success_modes.md`

## Recreate assets

```bash
cd reports/om-memory-pilot-w10
python3 make_om_assets.py
```

Caveats: one rep, reused baseline, and OM worker model-call cost is not included in the main-session token/cost columns.
