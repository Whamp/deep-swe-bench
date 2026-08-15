# Trajectory process signals in stock-Pi baseline runs

**Status:** corrected first retrospective analysis

**Snapshot analyzed:** local `results/` tree on 2026-08-14

**Worktree:** `/home/will/evals/deep-swe-bench/.worktrees/trajectory-process-signals`

**Branch:** `analysis/trajectory-process-signals`

**Base:** `origin/master@0ad5f5345f64e6525e8dfb64a57717bbaafa09f8`

## Short answer

This analysis asks whether behavior visible inside a Pi coding session predicts final failure better than trajectory length alone.

On the corrected stock-Pi dataset, the answer is **no for the features tested here**. Adding repeated actions, rereads, test transitions, mutation activity, edit reversions, and strategy-reset language made held-out-task predictions worse overall:

- length-model log loss: **0.658**;
- process-model log loss: **0.717**;
- process minus length: **+0.059** (lower is better);
- task-bootstrap 95% interval: **+0.025 to +0.102**.

The correction matters. The earlier pilot pooled many configs, including Pi Fabric. Those results are superseded. The dataset now contains only the three repository-defined stock-Pi baseline releases, and every modeled session exposes only direct `read`, `bash`, `edit`, and `write` calls.

## Dataset definition

The exact config allowlist is:

1. `baseline`
2. `baseline@1.0.0`
3. `baseline@1.1.0`

Their config READMEs define them as stock Pi with no config-authored extension, skill, system preamble, orchestration prompt, or appended prompt. The versioned releases preserve that behavior while pinning later Pi/model leaves.

The inventory code rejects every other config before schema counting, cohort classification, or session parsing. This excludes all Fabric, workflow, advisor, memory, testing-skill, prompt, and other wrapper configs.

### Cohort construction

| Stage | Attempts |
|---|---:|
| Stock-Pi baseline results found | 1,005 |
| Verifier-complete binary outcomes | 990 |
| Empty-patch outcomes with reward `-1` | 15 |
| Terminally truncated sessions | 0 |
| Malformed sessions | 0 |
| **Modeled attempts** | **990** |

All 1,005 baseline result cells had exactly one native session. The 990 modeled sessions cover:

- **110 tasks**;
- **5 model identities**;
- **4 thinking levels**;
- **3 baseline releases**;
- **463 successes and 527 failures**;
- **322,820,030 bytes (307.9 MiB)** of native session JSONL.

Every eligible task was included. There was no reward-based task selection and no task subset after applying the baseline allowlist.

### Model support

| Model | Attempts | Tasks | Successes | Failures | Thinking levels |
|---|---:|---:|---:|---:|---|
| GPT-5.6 Sol | 648 | 110 | 335 | 313 | low, medium, high |
| GPT-5.5 | 216 | 36 | 78 | 138 | low, medium |
| GPT-5.6 Luna | 114 | 14 | 45 | 69 | low, high, max |
| GPT-5.6 Terra | 6 | 2 | 2 | 4 | low |
| GLM-5.2 | 6 | 2 | 3 | 3 | max |

Terra and GLM provide diversity but not enough observations for reliable model-specific estimates. The aggregate model controls for their labels; separate model checks are reported only for Sol, GPT-5.5, and Luna.

## Artifact and schema audit

The full results tree contained 11,488 `result.json` files. Exactly 1,005 belonged to the stock-Pi allowlist; 8,249 other canonical results were excluded before analysis. Quarantined, archived, throughput, diagnostic, and run-state trees were also excluded.

| Baseline artifact | Present | Missing | Observation |
|---|---:|---:|---|
| `result.json` | 1,005 | 0 | Required identity, outcome, length, and exit fields were present. |
| Exactly one `session/*.jsonl` | 1,005 | 0 | No result-producing-session ambiguity. |
| `artifacts/model.patch` | 1,005 | 0 | All sizes matched `result.patch_bytes`; 990 nonempty, 15 empty. |
| Verifier reward JSON | 990 | 15 | Missing only for the 15 skipped empty patches. |
| Verifier CTRF | 990 | 15 | Missing only for the 15 skipped empty patches. |
| Verifier run log | 990 | 15 | Missing only for the 15 skipped empty patches. |

Declared `resource_policy` was present for 357/1,005 baseline results. Wall time is complete, but historical declared budgets remain incomplete.

### Native session evidence

The extractor parsed the 990 modeled JSONL files directly:

- 88,301 message records;
- 39,309 assistant turns;
- 48,035 top-level tool calls;
- 48,002 matched tool results;
- 33 terminal or otherwise unresolved tool calls;
- zero orphan tool results;
- zero malformed records;
- zero mismatches against result-level turn or tool-call totals.

The observed tool calls were:

| Tool | Calls |
|---|---:|
| `bash` | 21,935 |
| `read` | 13,441 |
| `edit` | 11,009 |
| `write` | 1,650 |

All 990 modeled sessions had complete supported tool surfaces. None contained Fabric or another opaque wrapper call. Of those sessions, 830 ran at least one observable test command and 987 made at least one direct mutation.

## Measurement boundaries

These limits apply before interpreting the result.

| Signal | What is measured | What is not claimed |
|---|---|---|
| Repeated actions | Exact normalized tool name and arguments. | Semantically equivalent but textually different actions. |
| Repeated reads | Repeated normalized target paths, with exact windows tracked separately. | Whether rereading was useful or unnecessary. |
| Repeated searches | Repeated normalized `rg`, `grep`, `find`, `fd`, or `git grep` commands. | Semantically equivalent queries with different text. |
| Repeated tests | The same normalized top-level test command, with direct edits dividing mutation epochs. | Test activity inferred from prose. |
| Test transitions | Failure→pass and pass→failure from the tool result's `isError` field. | Final verifier outcomes or hidden tests. |
| Unchanged failures | Exact normalized command and exact output fingerprint. | Functional equivalence when incidental output changes. |
| Edit churn | Direct mutation counts, target revisits, failed mutations, and exact inverse edits. | True intermediate patch size or partial semantic reversion. |
| Strategy reset | Conservative assistant phrase matches such as “rethink this approach.” | A reliable internal-state label. |
| Length | Tokens, turns, wall time, and within-task robust length outliers. | A declared budget where `resource_policy` is absent. |

The JSONL files preserve direct edit arguments, but the result tree does not preserve a patch snapshot after each action. Therefore true patch-size churn remains unsupported rather than replaced with a made-up proxy.

The strict unchanged-test-failure feature fired zero times. It is too brittle for substantive interpretation in this dataset.

## Evaluation method

The primary outcome is final binary verifier reward: success (`1`) or failure (`0`). Partial reward is secondary.

Four deterministic folds hold out whole tasks. Each attempt appears in one test fold, and no task appears in both training and test data for a fold. Fold test sizes were 247–248 attempts across 26–29 tasks.

The models are:

1. **Training-fold success rate:** no trajectory features.
2. **Length + controls:** log tokens, log turns, log wall time, within-task token/turn outliers, model, thinking level, and config.
3. **Length + process + controls:** the same predictors plus the process features above.

Both fitted models use the same fixed L2 regularization. There is no tuning on held-out tasks. Verifier logs, verifier details, final patch contents, f2p/p2p measures, reward fields, and post-outcome artifacts are excluded from every predictor matrix.

## Results

### Held-out-task binary prediction

| Model | Log loss ↓ | Macro-task log loss ↓ | Brier ↓ | AUROC ↑ | Average precision ↑ |
|---|---:|---:|---:|---:|---:|
| Training-fold success rate | 0.696 | 0.689 | 0.251 | 0.440 | 0.435 |
| Length + controls | **0.658** | **0.670** | **0.232** | **0.648** | **0.589** |
| Length + process + controls | 0.717 | 0.730 | 0.247 | 0.624 | 0.570 |
| **Process minus length** | **+0.059** | **+0.060** | **+0.015** | **−0.024** | **−0.019** |

The 2,000-sample task bootstrap places the process-minus-length log-loss difference between **+0.025 and +0.102**. Because lower log loss is better, the entire interval favors the length-only model in this dataset.

### Checks within supported models

| Model | Length log loss | Process log loss | Difference | Task-bootstrap 95% interval |
|---|---:|---:|---:|---:|
| GPT-5.5 | 0.619 | 0.687 | +0.068 | +0.012 to +0.132 |
| GPT-5.6 Luna | 0.528 | 0.688 | +0.160 | +0.064 to +0.255 |
| GPT-5.6 Sol | 0.658 | 0.685 | +0.027 | −0.009 to +0.067 |

GPT-5.5 and Luna clearly favor the length-only model. Sol's interval includes no difference: its process model slightly improves AUROC (+0.002) and average precision (+0.006), but worsens log loss (+0.027) and Brier score (+0.004). There is no consistent model family in which the process feature set clearly improves the primary probability prediction.

Terra and GLM were not separately fitted because each has only six attempts across two tasks.

### Partial reward

The process model also failed to improve partial-reward prediction:

- length RMSE: **0.10145**;
- process RMSE: **0.10183**;
- difference: **+0.00038**;
- MAE difference: **+0.00052**.

The difference is small, but it does not support an improvement.

## Direct observations

In this corrected dataset, successful attempts were longer, not shorter:

- mean tokens: 2.18M for successes versus 1.28M for failures;
- mean turns: 42.5 versus 37.2;
- mean wall time: 512.7 seconds versus 389.8 seconds.

Several process counts were also higher in successes before adjustment:

- repeated normalized actions: 1.33 versus 1.05;
- repeated read targets: 4.86 versus 3.68;
- direct mutations: 12.80 versus 11.36;
- failure→pass transitions: 0.225 versus 0.146;
- exact inverse edits: 0.086 versus 0.065.

Failed direct mutations were slightly higher in failures: 0.751 versus 0.698. Strategy-reset language was rare—seven successes and seven failures contained it—and repeated searches were nearly absent.

These are descriptive differences, not independent effects. They show why a simple “more activity means overthinking means failure” interpretation does not fit this stock-Pi cohort.

## Interpretation

The corrected result is stronger than the mixed-config pilot in one respect: wrapper opacity is no longer a plausible explanation. Every modeled session uses supported direct Pi tools.

The result still does **not** prove that useful trajectory warning signs do not exist. It says that this particular aggregate feature set does not improve held-out-task prediction beyond length and basic controls. Plausible remaining explanations include:

1. useful and unproductive retries produce similar counts;
2. exact command/output matching is too brittle for repeated failure detection;
3. counts discard the order and local context that distinguish recovery from thrashing;
4. model and task coverage remain uneven;
5. a stronger sequence model or manually validated event labels may be required.

## Conclusion and next step

For 990 stock-Pi baseline attempts across 110 tasks, adding the current process features makes prediction worse overall. The result repeats within GPT-5.5 and Luna and is inconclusive for Sol.

The next useful step is not to add more wrapper configs. It is to manually label a small, task-balanced set of baseline trajectories for genuine repeated failures, abandoned approaches, and patch reversions, then test whether sequence-aware features recover those labels. Without that validation, adding more automated counters is unlikely to clarify the hypothesis.

## Validation record

- `uv run --extra test python -m pytest -q` — **497 passed**.
- Ruff formatting and lint — all checks passed.
- Ty type checking — all checks passed.
- CodeGraph — cycle and ownership-boundary checks passed. Its declaration-signature check marks the intentional public rename from the superseded `pilot.py` driver to `baseline_analysis.py`.
- `aislop scan --changes --base origin/master` — 95/100 with zero AI-slop, security, lint, or formatting errors; eight advisory function/file-size warnings.
- Dataset assertions — exactly 1,005 cohort rows and 990 feature rows, all restricted to the three allowed configs.
- HTML validation — parsed successfully and all six local evidence links resolve.

## Reproduction

From the isolated worktree:

```bash
uv run python -m analysis.trajectory_process_signals.baseline_analysis \
  --results /home/will/evals/deep-swe-bench/results \
  --output analysis/trajectory_process_signals/artifacts \
  --folds 4 \
  --max-session-bytes 536870912

uv run python -m analysis.trajectory_process_signals.render_report
```

The extractor reads the results tree without writing to it.

Generated evidence:

- `artifacts/baseline_cohort.csv` — all 1,005 stock-Pi baseline results and dispositions;
- `artifacts/baseline_features.csv` — 990 pre-verifier feature rows used for modeling;
- `artifacts/schema_audit.json` — scoped result, session, patch, and verifier availability;
- `artifacts/session_schema_audit.json` — parsed JSONL records and semantic coverage;
- `artifacts/feature_summary.json` — task, model, config, outcome, and feature summaries;
- `artifacts/held_out_task_evaluation.json` — folds, aggregate metrics, bootstrap results, and model checks;
- `artifacts/baseline_manifest.json` — exact allowlist, tasks, byte cap, and provenance;
- `index.html` — self-contained review page generated from those artifacts.
