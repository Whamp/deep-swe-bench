# Feedback-uptake calibration

## Status

Full-population semantic annotation is **blocked**. No Luna reasoning level passed both hand-adjudicated accuracy and two-run repeatability. The gate selected no level and did not fall back to `max`.

This directory contains calibration evidence, not model efficacy results. Do not compute model rates from the purposive 24-unit sample or from deterministic candidate counts.

## Evidence layers

1. `events/` contains 108 schema-v3 deterministic packets rebuilt from exact session and result sources.
2. `candidates/units.jsonl` contains 1,237 bounded candidate windows derived from those packets.
3. `calibration/sample/units.jsonl` contains the fixed 24-unit stratified sample.
4. `calibration/gold-adjudication.json` contains manual labels for the sample.
5. `calibration/runs/<level>/run-{1,2}.json` contains two valid Luna classifications for each reasoning level.
6. `calibration/runs/evaluation.json` scores each run against gold and each pair against itself.
7. `calibration/runs/selection.json` records the fail-closed decision.

Raw facts and semantic labels never share a field:

- deterministic packet facts: `raw_result_facts`, `raw_result_signature`;
- high-recall review flags: `candidate_signals`;
- semantic labels: calibration annotation documents governed by `calibration/annotation-schema.json`.

## Fixed identities

| Artifact | Identity |
| --- | --- |
| Complete candidate set | `sha256:e6089bcdf90ec249cab3817c9a4da8cc25217f6bb3cb99f345ac5f774909d73d` |
| Calibration sample | `sha256:42ebc337026bbfdba1b132539a2815ca9eee4fb5b7f2760cb1d5f279ee28cd95` |
| Gold adjudication file | `sha256:8292d9d55315c2c81f83c0353d798f4d75138d9a032c0e881df34d85c19df1d7` |
| Annotation schema | `sha256:bfb7ceaa06e37a6579f1c917529e8fc171a0358b34505c44261328108f8009e7` |
| Calibration instructions | `sha256:3cbc6a4636794c70f3673724e93cf47576e46913b263707b3fa34c314c049f20` |

The sample contains eight units per model, covers all 12 tasks, includes strict solve, nonsolve, and timeout outcomes, and covers every deterministic signal type used in the candidate population. It is purposive calibration evidence, not a representative subset.

## Calibration result

Exact all-field unit matches out of 24:

| Luna level | Run 1 | Run 2 | Repeatability | Passed |
| --- | ---: | ---: | ---: | --- |
| `low` | 6 | 4 | 10 | No |
| `medium` | 6 | 4 | 9 | No |
| `high` | 10 | 8 | 11 | No |
| `xhigh` | 11 | 10 | 13 | No |
| `max` | 13 | 10 | 12 | No |

Observation and candidate-disposition labels were generally stable. Immediate response, bounded outcome, and revalidation labels missed the declared thresholds. Thinking level was not monotonic.

## Rebuild and validate

Run from this report directory:

```bash
uv run python build_feedback_uptake_events.py
uv run python build_feedback_uptake_candidates.py
uv run pytest -q \
  test_trajectory_evidence.py \
  test_feedback_uptake_events.py \
  test_feedback_uptake_candidates.py \
  test_feedback_uptake_calibration.py
```

To repeat the external calibration intentionally:

```bash
uv run python run_feedback_uptake_calibration.py --force
```

That command runs `openai-codex/gpt-5.6-luna` at `low`, `medium`, `high`, `xhigh`, and `max` twice each. Every run receives the same no-tool context: fixed instructions, formal schema, sample manifest, and sample units. The gold file is never attached.

## Authorization rule

Full-population annotation may begin only when `calibration/runs/selection.json` contains all of:

```json
{
  "selection_status": "passed",
  "selected_level": "<level>",
  "full_population_authorized": true,
  "fallback_used": false
}
```

The current file contains `selected_level: null` and `full_population_authorized: false`. Do not run semantic fan-out or integrate feedback-uptake rates into the report while that remains true.
