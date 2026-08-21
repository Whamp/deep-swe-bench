---
tags: [agent-evaluation, trajectory-analysis, validation, random-forest]
summary: Repeated-task agent benchmarks must hold out whole tasks; row-level OOB or cross-validation can reverse the apparent value of trajectory features.
---
# Task-Held-Out Validation for Repeated Agent Benchmarks

Predictive evaluation must split on the unit that must generalize. When a benchmark has several attempts per task, holding out attempts does not test performance on unseen tasks because the training data still contains other attempts from the same task.

## Why this matters

Task identity carries difficulty, language, repository structure, and typical trajectory shape. Row-level validation can therefore reward features that recognize familiar task structure without transferring to a new task.

Random-forest out-of-bag evaluation has this limitation. OOB excludes individual training rows for each tree; it does not automatically exclude every row sharing the same task. OOB remains useful for training diagnostics, but it is not evidence of unseen-task generalization.

The stock-Pi trajectory study demonstrated an ordering reversal:

- OOB log loss favored process-feature forests at about **0.627**, versus **0.635** for length and controls.
- Whole-task held-out evaluation favored length and controls at **0.649**.
- Test/phase flow worsened held-out log loss to **0.665**.
- Compact process features scored **0.670**.
- All 91 measured features scored **0.669**, a **+0.020** difference from length with a task-bootstrap 95% interval of **+0.003 to +0.035**.

The reversal is the result: built-in model validation can look positive while the deployment-relevant test is negative.

## Evaluation pattern

Use this structure for repeated-task agent data:

1. Partition outer folds by task ID, never by attempt.
2. Tune hyperparameters only inside each outer training partition, again using task-disjoint inner folds.
3. Select parameters using a task-balanced metric such as macro-task log loss when tasks have unequal attempt counts.
4. Fit the selected model on the full outer training partition and predict only the unseen outer tasks.
5. Average deterministic model seeds when tree randomness is material.
6. Bootstrap whole tasks, not rows, for uncertainty intervals.
7. Keep OOB scores as explicitly labeled diagnostics rather than promotion evidence.
8. Compare every richer model against the same controls-only baseline on identical folds.
9. Exclude verifier outcomes, final rewards, privileged reference-patch facts, and other post-outcome information from predictors.

## Interpretation rule

Descriptive association and transferable prediction are different claims. In the stock-Pi data, successful attempts committed earlier relative to their own trajectory and cycled between implementation and validation more often. Those behaviors remained useful places to inspect manually, but automated counts did not improve unseen-task prediction.

Model complexity is not a substitute for better measurement. When logistic regression and random forests both reject the same process features under whole-task holdout, the next useful step is usually better semantic labels or stronger task representations—not a larger hyperparameter search. ^[inferred]

## Evidence

The complete cohort, feature definitions, censoring rules, linear and forest results, and reproduction commands are in [[analysis/trajectory_process_signals/report]]. The primary-literature basis for the trajectory measures is in [[analysis/trajectory_process_signals/trajectory_analysis_research]].