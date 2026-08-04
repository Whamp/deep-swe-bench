# Feedback-uptake analysis

## Status

The semantic analysis is complete.

Luna `xhigh` passed the final calibration and annotated the production corpus. GLM-5.2 `max` did not pass. The analysis uses 1,165 candidate events that no eligible production model saw during calibration. It excludes all 72 development and held-out cases from semantic rates.

The labels describe how subjects responded to detector-flagged feedback. They are not task-success estimates. Candidate windows can overlap and should not be treated as independent episodes.

## Evidence layers

1. `events/` contains 108 deterministic event packets: 12 tasks × 3 reps × 3 models.
2. `candidates/units.jsonl` contains 1,237 bounded candidate windows.
3. `calibration/` preserves the original failed 24-case calibration.
4. `calibration-v2/` preserves the first clarified-rubric round. Neither eligible protocol passed.
5. `calibration-v2-repair/` contains the one allowed repair round. It uses new examples and a fresh 24-case held-out sample.
6. `calibration-v2-repair/population/` contains 1,165 Luna annotations and a complete 1,237-case audit ledger.
7. `analysis-v2.json` contains the descriptive model and trajectory summaries used by the HTML report.

Raw facts and semantic labels remain separate:

- packet facts: `raw_result_facts`, `raw_result_signature`;
- high-recall review flags: `candidate_signals`;
- semantic labels: documents governed by `calibration-v2-repair/annotation-schema.json`.

## Calibration result

The first v2 round remained blocked. Luna was repeatable but scored 18/24 on `window_outcome`, below the declared 20/24 threshold. The repair round added explicit examples for the difference between `progressed` and `not_recovered`, then used a fresh sample that excluded every earlier calibration case.

| Protocol | Accuracy run 1 | Accuracy run 2 | Repeatability | Passed |
| --- | ---: | ---: | ---: | --- |
| Luna `xhigh` | 15/24 exact | 14/24 exact | 18/24 exact | Yes |
| GLM-5.2 `max` | 19/24 exact | 12/24 exact | 13/24 exact | No |

Luna passed every field threshold in both runs and in the repeatability comparison. The production receipt is `calibration-v2-repair/authorization.json`.

SOL helped review the rubric and human gold labels. SOL never produced production labels. Luna and GLM never received held-out gold.

## Production corpus

The production runner split the 1,165 unseen cases into 50 fixed batches. Every batch passed schema, identity, ID-order, and cross-field validation.

The audit trail records three bounded recoveries:

- one 63-character batch hash was completed only after every candidate ID matched exactly;
- one exact permutation of candidate IDs was restored to manifest order;
- one batch that repeatedly omitted a case was preserved, and the missing case was classified in a separate one-case Luna call before composition.

No repair changed a semantic label. A separate bad-ID output and two local Mise-shim failures remain preserved as rejected artifacts.

| Artifact | SHA-256 |
| --- | --- |
| Complete candidate set | `e6089bcdf90ec249cab3817c9a4da8cc25217f6bb3cb99f345ac5f774909d73d` |
| Final held-out sample | `7dbc0bcc95fb896ef549edafdd87a0710690e5d72ee0043fcf24298a6d35dfa6` |
| Production authorization | `44a34cf89be7b82031c700185448c0c553dbb63f1b20c389db31916ea4b49e85` |
| Production annotations | `00e883a06a473a98e5b391060c9aab24999d2583dd6611259552d948b352b446` |
| Complete candidate ledger | `eff14978703ed4b273c8e3d0d0fd5d82e46fa5b03e0939201ba0a99691609131` |
| Feedback analysis | `cd79eb3a215a6a446387fe54cf2bbdfa809010f123181aeeaeb731508ca0994e` |

## Main finding

The local models usually respond to visible negative feedback, but they close fewer loops.

Event-level recovery was 44.1% for GPT-5.6 SOL, 38.4% for AgentWorld, and 32.8% for ThinkingCap. Progress-or-recovery was 93.1%, 96.8%, and 96.8%, respectively. ThinkingCap validated after 55.1% of relevant changes, close to the frontier's 57.3%; AgentWorld reached 48.4%.

This supports two conclusions:

- generic “pay attention to errors” guidance is unlikely to fix the local capability gap;
- ThinkingCap does not mainly need more tests—it needs earlier tests that can overturn a bad design.

AgentWorld's malformed edit calls remain a useful narrow scaffold target. In the unseen corpus, 99 schema-invalid calls produced 76 recoveries, 21 progressions, and 2 non-recoveries. A conservative argument normalizer would save turns, but it would not repair wrong repository models.

## Rebuild and validate

Run from this report directory:

```bash
uv run python build_feedback_uptake_events.py
uv run python build_feedback_uptake_candidates.py
uv run python build_feedback_uptake_calibration_v2.py --check
uv run python build_feedback_uptake_analysis_v2.py
uv run pytest -q \
  test_trajectory_evidence.py \
  test_feedback_uptake_events.py \
  test_feedback_uptake_candidates.py \
  test_feedback_uptake_calibration.py \
  test_feedback_uptake_calibration_v2.py \
  test_feedback_uptake_analysis_v2.py
uv run python build_report.py
```

The external model calls are intentionally resumable rather than part of the deterministic rebuild:

```bash
# Re-run both final calibration protocols twice.
uv run python run_feedback_uptake_calibration_v2.py \
  --calibration-root feedback-uptake/calibration-v2-repair \
  --force

# Resume production annotation from existing valid batches.
uv run python run_feedback_uptake_population_v2.py --concurrency 1
```

Do not use `--force` for production unless intentionally replacing every batch. Both runners use the known Pi 0.83.0 executable path by default; set `PI_REAL_EXECUTABLE` when running elsewhere.
