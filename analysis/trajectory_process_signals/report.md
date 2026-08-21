# Sequence-aware trajectory analysis of stock-Pi baseline runs

**Status:** third retrospective milestone; ordered features plus nonlinear random-forest follow-up

**Snapshot analyzed:** local `results/` tree on 2026-08-14

**Worktree:** `/home/will/evals/deep-swe-bench/.worktrees/trajectory-process-signals`

**Branch:** `analysis/trajectory-process-signals`

**Base:** `origin/master@0ad5f5345f64e6525e8dfb64a57717bbaafa09f8`

**Sequence-feature source:** `5380d2149e3281f81d0623ae6fc4777d9c8e2465`

**Random-forest source:** `f86ecad`

## Short answer

This follow-up tests a different idea from the first analysis: not just how much an agent reads, edits, or tests, but **when** it does those things.

The new measurements include:

- reads and tests before the first source-code change;
- the point in the trajectory where the first source change occurs;
- `edit` versus whole-file `write` behavior;
- code changes before and after tests;
- implementation→validation cycles and backward transitions;
- testing after the final source change.

The result is mixed but clear:

1. **The ordered features explain behavior better than the old totals.** Successful runs are more likely to end with a passing test and perform more code/test cycles.
2. **They still do not improve held-out-task prediction beyond trajectory length.** The test/phase-flow model is the closest, but is statistically tied with the length-only model.
3. **The simple “too much exploration before acting causes failure” story is not supported.** Successful runs often do more reading in absolute terms, yet reach their first source change earlier as a share of their total trajectory.
4. **A random forest does not uncover hidden nonlinear process signal.** It improves the length-only baseline, but adding test flow or all process features makes unseen-task predictions worse. On the clean 925-attempt cohort, test flow is effectively tied with length.

## Research basis

The feature design follows a review of primary trajectory-analysis work recorded in [`trajectory_analysis_research.md`](./trajectory_analysis_research.md).

The most directly relevant study, *Beyond Resolution Rates*, analyzes opening context gathering, patching in the first ten steps, and validation effort. Other applicable methods come from TraceProbe milestones, TrajEval's search/read/edit decomposition and intermediate-edit corruption, AgentLens phase coherence and temporal profiles, Graphectory phase flows and loops, and *Failure as a Process* recovery windows.

The literature shaped four decisions here:

- preserve action order rather than only totals;
- distinguish diagnosis before source changes from validation after them;
- treat `edit` and `write` separately;
- compare within tasks and hold out whole tasks, because task difficulty confounds trajectory length.

The cited studies use other agents, benchmarks, and feature definitions. Their findings are motivation, not evidence about this Pi dataset.

## Dataset

The exact config allowlist remains:

1. `baseline`
2. `baseline@1.0.0`
3. `baseline@1.1.0`

Every other config—including all Fabric, workflow, advisor, memory, skill, and prompt variants—is rejected before session parsing.

| Stage | Attempts |
|---|---:|
| Stock-Pi results | 1,005 |
| Empty-patch outcomes excluded from binary modeling | 15 |
| **Modeled attempts** | **990** |
| Successes | 463 |
| Failures | 527 |
| Tasks | 110 |
| Models | 5 |
| Thinking levels | 4 |
| Native-session input | 322,820,030 bytes |

All 990 modeled sessions contain only supported direct Pi tools: `read`, `bash`, `edit`, and `write`.

## Event definitions

### First mutation boundaries

The analysis uses two boundaries:

- **first workspace mutation:** first successful structured `edit` or `write`;
- **first source mutation:** first successful structured mutation to a supported source-file extension, excluding paths conservatively identified as tests or reproduction scripts.

The source boundary is the main proxy for committing to a fix. A `write` that creates `repro_bug.py` is diagnosis, not source implementation.

Five attempts have no observed source mutation. Sixty-two contain a shell command that may have mutated files before the first structured source change. Those 62 are marked uncertain. A separate sensitivity analysis excludes both uncertain boundaries and no-source-mutation attempts, leaving 925 attempts.

### Opening behavior

The compact opening feature group contains ten measures drawn from the research plan:

- whether a source mutation occurs;
- tool calls, reads, unique read paths, and tests before it;
- failed tests before it;
- first-source-mutation position divided by total tool calls;
- read and source-mutation shares among the first ten tool calls;
- shell-boundary uncertainty.

Tokens before first mutation and other opening measurements remain in the dataset for description but were kept out of the compact predictive group to reduce collinearity.

### `edit` versus `write`

The mutation-style group contains:

- source `edit` calls;
- source `write` calls;
- failed edit/write calls;
- whether the first source mutation is a write;
- mutation-tool switches;
- write→edit on the same target;
- repeated writes to the same target.

The extractor also records content sizes and mutations to test/reproduction targets, but these are descriptive rather than primary predictors.

### Test and phase flow

Events receive deterministic phase labels where supported:

- **exploration:** reads and searches;
- **diagnosis:** tests or test/reproduction writes before source mutation;
- **implementation:** source mutations;
- **validation:** tests after source mutation and reads of already-mutated source targets.

The compact test-flow group measures:

- tests after first mutation;
- distance and mutation count to the first post-mutation test;
- longest mutation streak without testing;
- tests and passing tests after the final mutation;
- changes after a passing test;
- pass→mutation→fail patterns;
- implementation→validation transitions;
- validation→implementation transitions.

A tool result with `isError=false` means the command exited successfully. It does not prove that the relevant hidden or feature tests passed.

## Evaluation

Four deterministic folds hold out whole tasks. Each attempt appears in one test fold, and no task appears in both training and test data for that fold.

Every fitted linear model includes the same model, thinking-level, config, token, turn, wall-time, and within-task length controls. Fixed L2 regularization is used without test-fold tuning.

The compared specifications are:

1. length and controls;
2. length plus the original aggregate counts;
3. length plus opening behavior;
4. length plus mutation style;
5. length plus test/phase flow;
6. length plus all compact ordered features;
7. length plus aggregate and ordered features.

Verifier outputs, final patch contents, reward details, and post-outcome artifacts never enter the predictors.

## Predictive results

### Held-out-task binary prediction

| Predictors | Log loss ↓ | Macro-task loss ↓ | Brier ↓ | AUROC ↑ | Average precision ↑ |
|---|---:|---:|---:|---:|---:|
| Length + controls | **0.658** | **0.670** | **0.232** | **0.648** | 0.589 |
| Original aggregate counts | 0.717 | 0.730 | 0.247 | 0.624 | 0.570 |
| Opening behavior | 0.686 | 0.681 | 0.242 | 0.626 | 0.573 |
| Edit/write style | 0.694 | 0.678 | 0.241 | 0.626 | 0.578 |
| Test and phase flow | 0.674 | 0.672 | 0.234 | 0.647 | **0.599** |
| All compact ordered features | 0.746 | 0.706 | 0.253 | 0.613 | 0.567 |
| Aggregate + ordered features | 0.806 | 0.777 | 0.270 | 0.588 | 0.551 |

### Difference from length-only

| Added feature group | Log-loss difference | Task-bootstrap 95% interval | AUROC difference | Average-precision difference |
|---|---:|---:|---:|---:|
| Original aggregate counts | +0.059 | +0.025 to +0.102 | −0.024 | −0.019 |
| Opening behavior | +0.028 | +0.006 to +0.061 | −0.022 | −0.016 |
| Edit/write style | +0.036 | +0.008 to +0.068 | −0.022 | −0.011 |
| Test and phase flow | **+0.016** | **−0.005 to +0.036** | −0.002 | **+0.010** |
| All compact ordered features | +0.088 | +0.039 to +0.140 | −0.035 | −0.022 |
| Aggregate + ordered features | +0.148 | +0.086 to +0.214 | −0.060 | −0.037 |

Lower log loss is better. Opening and mutation-style features clearly worsen probability prediction. Test/phase flow is effectively tied with length: its interval includes no difference, AUROC is unchanged, and average precision improves by 0.010.

The large combined models overfit badly despite regularization. They should not be interpreted as evidence that every sequence feature is harmful; they show that adding many correlated counters is not useful with this sample size.

### Clean-boundary sensitivity

Excluding 62 shell-uncertain attempts and five no-source-mutation attempts leaves 925 attempts.

| Added feature group | Log-loss difference | Task-bootstrap 95% interval | AUROC difference |
|---|---:|---:|---:|
| Opening behavior | +0.010 | −0.002 to +0.026 | −0.007 |
| Edit/write style | +0.020 | +0.002 to +0.040 | −0.017 |
| Test and phase flow | **+0.005** | **−0.018 to +0.025** | **+0.007** |
| All compact ordered features | +0.031 | +0.004 to +0.059 | −0.010 |
| Aggregate + ordered features | +0.084 | +0.036 to +0.141 | −0.031 |

The clean-boundary cohort reaches the same conclusion. Test flow remains tied with length and gains a small amount of AUROC, while opening and mutation style do not improve log loss.

### Supported models

For the test/phase-flow group:

| Model | Attempts | Length log loss | Test-flow log loss | Difference | Task-bootstrap 95% interval |
|---|---:|---:|---:|---:|---:|
| GPT-5.5 | 216 | 0.619 | 0.667 | +0.048 | +0.003 to +0.094 |
| GPT-5.6 Luna | 114 | 0.528 | 0.866 | +0.338 | +0.101 to +0.616 |
| GPT-5.6 Sol | 648 | 0.658 | 0.659 | +0.001 | −0.037 to +0.037 |

For Sol, test flow improves AUROC by 0.017 and average precision by 0.015 while leaving log loss unchanged. It clearly hurts Luna and modestly hurts GPT-5.5. Terra and GLM have only six attempts each and are not fitted separately.

### Partial reward

No added feature group improves partial-reward RMSE. Test flow changes RMSE by +0.00114 and MAE by +0.00146. The other compact groups also move slightly in the wrong direction.

## Random-forest follow-up

The nonlinear follow-up compares four forests on the same 990 attempts and the same four outer task folds:

1. length and controls;
2. length plus test/phase flow;
3. length plus aggregate and compact ordered features;
4. length plus every measured aggregate and ordered feature (91 numeric predictors before categorical encoding).

Inside each outer training partition, three additional task-disjoint folds select among four conservative tree settings. Selection minimizes mean per-task log loss. Final predictions average three independent 400-tree forests. The small grid varies depth, minimum leaf size, and sampled features; it is deliberately not an open-ended hyperparameter search.

Out-of-bag predictions are retained only as training diagnostics. They leave attempts out, not whole tasks, and therefore do not test transfer to a genuinely unseen task.

### Primary random-forest results

| Predictors | Log loss ↓ | Brier ↓ | AUROC ↑ | Average precision ↑ |
|---|---:|---:|---:|---:|
| Linear length baseline | 0.658 | 0.232 | 0.648 | 0.589 |
| **Forest length baseline** | **0.649** | **0.229** | **0.651** | **0.604** |
| Forest test/phase flow | 0.665 | 0.235 | 0.637 | 0.598 |
| Forest aggregate + compact ordered features | 0.670 | 0.238 | 0.620 | 0.584 |
| Forest all 91 measured features | 0.669 | 0.238 | 0.617 | 0.588 |

The forest itself helps modestly: the forest length baseline improves log loss by 0.009 and average precision by 0.015 over logistic regression. That suggests some nonlinear structure in trajectory length and the basic controls.

The process features do not add signal beyond that stronger baseline:

| Added forest features | Log-loss difference from forest length | Task-bootstrap 95% interval | AUROC difference | Average-precision difference |
|---|---:|---:|---:|---:|
| Test/phase flow | +0.016 | **+0.003 to +0.029** | −0.014 | −0.005 |
| Aggregate + compact ordered features | +0.020 | **+0.006 to +0.033** | −0.031 | −0.020 |
| All 91 measured features | +0.020 | **+0.003 to +0.035** | −0.034 | −0.015 |

All three process forests are reliably worse on wholly unseen tasks. The compact all-process forest is much better than its linear equivalent, but it still loses to the simpler forest that sees only length and controls. Giving the forest every measured feature does not recover additional signal.

### Why out-of-bag validation is insufficient here

| Forest | Mean OOB log loss | True task-held-out log loss |
|---|---:|---:|
| Length | 0.635 | **0.649** |
| Test/phase flow | **0.627** | 0.665 |
| Aggregate + compact ordered features | **0.627** | 0.670 |
| All 91 measured features | **0.627** | 0.669 |

OOB diagnostics suggest that process features help. Holding out whole tasks reverses the result. Attempts from the same task share task-specific structure, so attempt-level OOB estimates are optimistic for the question we care about.

### Clean-boundary forest sensitivity

Removing the 62 shell-uncertain attempts and five attempts without an observed source change leaves 925 attempts.

| Predictors | Log loss ↓ | AUROC ↑ | Average precision ↑ |
|---|---:|---:|---:|
| Forest length | **0.660** | **0.641** | 0.599 |
| Forest test/phase flow | 0.661 | 0.640 | **0.603** |
| Forest aggregate + compact ordered features | 0.668 | 0.615 | 0.595 |
| Forest all 91 measured features | 0.671 | 0.610 | 0.597 |

Test flow is tied with length: log-loss difference +0.001, task-bootstrap interval −0.013 to +0.014, nearly identical AUROC, and +0.003 average precision. The compact and all-measured forests are inconclusive on log loss but rank worse.

### Held-out family permutation

As a diagnostic, each feature family is jointly shuffled within every held-out task. Positive log-loss change means the model depended usefully on that family; negative means shuffling improved prediction.

In the primary all-measured forest, shuffling test-flow features improves log loss by 0.004 and shuffling mutation-style features improves it by 0.001; both task-bootstrap intervals remain below zero. Shuffling the 39 additional sequence measurements worsens log loss by 0.006, but its interval spans zero. This is consistent with weak, unstable process dependence rather than a transferable feature family.

The clean cohort weakens these effects toward zero. No process family shows stable positive held-out importance.

## Within-task descriptive results

Only 61 of 110 tasks contain both successful and failed attempts. For each feature, the analysis computes success minus failure inside those contested tasks and bootstraps whole tasks. Positive values mean the feature is higher in successful attempts.

| Measure | Mean raw difference | Mean standardized difference | Task-bootstrap 95% interval |
|---|---:|---:|---:|
| Calls before first source mutation | +2.592 | +0.088 | −0.208 to +0.364 |
| Reads before first source mutation | +2.077 | +0.247 | −0.045 to +0.509 |
| Unique paths read before first source mutation | +1.827 | +0.247 | −0.060 to +0.542 |
| Share of trajectory before first source mutation | −0.025 | **−0.304** | **−0.583 to −0.034** |
| First source mutation is `write` | −0.003 | −0.048 | −0.316 to +0.209 |
| Source `edit` calls | +1.576 | +0.243 | −0.035 to +0.530 |
| Source `write` calls | +0.081 | +0.131 | −0.113 to +0.385 |
| Tests after first source mutation | +0.671 | +0.275 | −0.064 to +0.586 |
| Passing test after final source mutation | +0.088 | **+0.299** | **+0.013 to +0.580** |
| Implementation→validation transitions | +0.561 | **+0.443** | **+0.173 to +0.714** |
| Validation→implementation transitions | +0.483 | **+0.443** | **+0.169 to +0.721** |

The key distinction is absolute versus relative exploration:

- successful attempts make more pre-mutation calls and reads on average, although those intervals include zero;
- successful attempts reach the first source mutation earlier as a fraction of their total trajectory;
- successful attempts perform more implementation/validation cycles and are more likely to end with a passing test.

This does not look like successful agents simply “read less.” It looks more like they sustain a longer productive trajectory after committing to a change.

## `edit` versus `write`

The stock-Pi sessions contain:

- 8,728 structured source `edit` calls;
- 1,094 whole-file source `write` calls;
- 2,044 write→edit events on the same target across 574 attempts.

First source mutation:

| Tool | Attempts | Successes | Raw success rate |
|---|---:|---:|---:|
| `edit` | 507 | 242 | 47.7% |
| `write` | 478 | 219 | 45.8% |
| No observed source mutation | 5 | 2 | 40.0% |

The 1.9-point raw difference between first-`edit` and first-`write` runs is small. The within-task standardized interval for “first source mutation is write” spans −0.316 to +0.209. The predictive mutation-style model also worsens log loss.

There is therefore no evidence that `edit` is intrinsically better than `write`, or vice versa. Their meaning depends on target and sequence: `write` may create a complete source file or a reproduction test; `edit` may make a focused repair or repeatedly thrash the same file.

## Test behavior

Only 30/990 attempts run any recognized test before the first source mutation, for 38 total pre-mutation tests. This behavior is too rare to estimate reliably in this cohort.

After source mutation:

- 830 attempts run at least one recognized test somewhere in the trajectory;
- 670 run a test after the final source mutation;
- 534 obtain a successful test command after the final source mutation;
- 165 contain at least one pass→mutation→fail pattern.

Raw success rates are 51.9% when a passing test follows the final source mutation and 40.8% otherwise. The within-task effect remains positive after task control. This is the clearest descriptive signal in the new feature family, although it does not improve the full predictive model enough to beat length.

Validation→implementation transitions are also higher in successful runs. A failed test followed by another change is often a healthy feedback loop, not “backtracking” in the pejorative sense.

## Interpretation

The sequence-aware result narrows the hypothesis:

- **Not supported:** failures spend more time exploring before acting; `write` is worse than `edit`; more code/test cycling indicates failure.
- **Supported descriptively:** successful runs commit earlier relative to their own length, validate more after changing code, and cycle between implementation and validation more often.
- **Not predictive with either model family:** these deterministic measurements do not improve held-out-task probability estimates over length and controls in linear or random-forest models.

This differs from some published cross-agent results that associate delayed first edits with higher agent-level resolution. The likely reasons include dataset and design differences: this analysis holds the scaffold to stock Pi, uses newer model families, compares individual attempts rather than agent-level averages, and holds out entire tasks. The disagreement is itself useful evidence that opening strategy is model/scaffold dependent rather than universal.

## Remaining limits

1. **First source mutation is a proxy for commitment.** It is not an observed internal plan decision.
2. **Shell mutation detection is conservative.** Sixty-two boundaries are flagged uncertain; other shell-writing patterns may be missed.
3. **Path purpose is heuristic.** Test and reproduction files are recognized by path patterns; unusual names may be misclassified.
4. **Test success is coarse.** `isError=false` means command success, not necessarily feature correctness.
5. **No intermediate workspace snapshots exist.** Structured edit/write arguments preserve substantial history, but arbitrary shell changes prevent complete patch reconstruction.
6. **Feature families remain correlated.** Combined models overfit; group-level comparisons are safer.
7. **The compact specifications are partly adaptive.** The research note preceded extraction, but the final compact subsets were tightened after an initial broad-feature pass overfit. Treat this as exploratory model development, not a pristine preregistered confirmation.
8. **The forest search is intentionally narrow.** Four conservative settings cannot rule out every possible nonlinear learner, but a wider search on 990 attempts would raise overfitting risk.
9. **OOB is not task-held-out evidence.** It is included to show exactly how attempt-level validation can look encouraging while unseen-task performance worsens.
10. **Only 61 tasks are contested.** Within-task effect intervals are wide for sparse behaviors.
11. **Observational data is not an intervention.** Forcing more reading or testing could have different effects.

## Recommended next step

The most useful next milestone is manual labeling, not more counters. Select a task-balanced set of stock-Pi trajectories and label:

- whether pre-mutation exploration was focused or aimless;
- whether a `write` created a reproduction/test artifact or implemented the fix;
- whether a failed test caused a useful change;
- whether a passing intermediate state was later corrupted;
- whether the final validation actually exercised the requested behavior.

Use those labels to validate a small sequence-aware detector set. The automated result says where to look—final validation and code/test cycling—but does not yet distinguish productive iteration from accidental motion.

## Reproduction

```bash
uv run python -m analysis.trajectory_process_signals.baseline_analysis \
  --results /home/will/evals/deep-swe-bench/results \
  --output analysis/trajectory_process_signals/artifacts \
  --folds 4 \
  --max-session-bytes 536870912

uv run --extra analysis python -m \
  analysis.trajectory_process_signals.random_forest_analysis \
  --outer-folds 4 \
  --inner-folds 3 \
  --tuning-trees 150 \
  --final-trees 400 \
  --permutation-repeats 8

uv run --extra analysis python -m analysis.trajectory_process_signals.render_report
```

Generated evidence:

- `artifacts/baseline_cohort.csv` — scoped result cohort and dispositions;
- `artifacts/baseline_features.csv` — aggregate and ordered features for 990 attempts;
- `artifacts/task_controlled_feature_effects.json` — within-task descriptive effects and task bootstraps;
- `artifacts/held_out_task_evaluation.json` — grouped models, model checks, and clean-boundary sensitivity;
- `artifacts/session_schema_audit.json` — parsed session coverage and boundary support;
- `artifacts/feature_summary.json` — outcome, task, model, config, and feature summaries;
- `artifacts/baseline_manifest.json` — exact config allowlist, task list, byte cap, and source revision;
- `artifacts/random_forest_evaluation.json` — nested task-held-out forests, OOB diagnostics, clean-boundary sensitivity, and held-out permutation results;
- `trajectory_analysis_research.md` — research basis and predeclared feature plan;
- `index.html` — self-contained rendered report.

## Validation record

- Full repository tests: **504 passed**.
- Focused sequence/forest contracts: **18 passed**.
- Ruff formatting/lint: passed.
- Ty type checking: passed.
- CodeGraph cycles and boundaries: passed; its declaration check reports the intentional replacement of internal renderer helpers.
- `aislop scan --changes --base origin/master`: 91/100, zero slop/security/lint/formatting errors; thirteen size/complexity advisories across the cumulative analysis branch.
- Dataset assertions and HTML-link validation are recorded with the final artifact commit.
