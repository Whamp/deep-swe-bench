# Trajectory process signals: first retrospective milestone

**Status:** feasibility pilot, not a final hypothesis test

**Snapshot analyzed:** local `results/` tree on 2026-08-14

**Worktree:** `/home/will/evals/deep-swe-bench/.worktrees/trajectory-process-signals`

**Branch:** `analysis/trajectory-process-signals`

**Base:** `origin/master@0ad5f5345f64e6525e8dfb64a57717bbaafa09f8`
**Fallback:** `origin/main` and local `main` did not exist; `origin/master` is the remote default.

## Verdict

The corpus can support a leakage-resistant trajectory analysis, but the current feature definitions are not ready for a full-corpus claim. The bounded 12-task pilot parsed 985 valid reps and held out whole tasks. Under the predeclared fixed model, adding process features made prediction worse than the same controls plus length alone: log loss increased by **0.156**, AUROC fell by **0.030**, and partial-reward RMSE increased by **0.010**. A task bootstrap put the process-minus-length log-loss delta at **+0.038 to +0.278**.

That result is measured, but it is not a general rejection of the hypothesis. The pilot pooled 17 models and 86 configs, 19% of reps had incomplete or opaque semantic tool coverage, true patch-state history was unavailable, and the strict unchanged-test-failure signal never fired. The right next step is to repair observability and run a direct-tool, config-balanced sensitivity analysis before expanding beyond the pilot.

## Question and scope

The source hypothesis asks whether event-semantic process signals predict final verifier failure beyond tokens, turns, task, model, thinking level, and config. This milestone does four things:

1. audits the schemas and missingness in the current result tree;
2. defines censoring and exclusion rules before modeling;
3. implements a read-only native-session extractor for a minimal feature set;
4. checks the pipeline on a deterministic, resource-bounded task pilot.

It does **not** parse all native sessions, estimate causal effects, rank models or configs, or modify the hypothesis note. The analysis read raw results from `/home/will/evals/deep-swe-bench/results`; it wrote only derived files under this worktree.

## Current corpus audit

The hypothesis note's corpus counts are stale relative to this snapshot. The current tree contains **12,089** native `session/*.jsonl` files and **11,488** `result.json` files, not 13,311 and roughly 13,039. Result quarantine and archival explain part of the difference; this analysis does not infer where every removed file went.

### Result and session locations

| Location/disposition | `result.json` | Native sessions |
|---|---:|---:|
| Canonical result tree | 9,254 | 9,621 attached |
| Quarantined under `_contaminated` | 2,119 | 2,339 |
| Archived | 108 | 108 |
| Throughput diagnostics | 6 | 14 |
| Other diagnostics | 1 | 0 |
| Canonical root without a matching canonical result | — | 7 |
| **Total** | **11,488** | **12,089** |

Only exact paths of the form `results/<model-leaf>/<thinking>/<config>/<task>/repN/result.json` enter the canonical audit. Quarantined, archived, diagnostic, throughput, and structured run-state trees never enter the modeling cohort.

### Canonical artifact availability

| Artifact/schema | Present | Missing | Measured shape |
|---|---:|---:|---|
| `result.json` | 9,254 | 0 | All loaded as JSON objects. Core identity, outcome, token, turn, wall-time, and exit fields were present in every row. |
| Exactly one native session | 8,969 | 285 | 267 cells had 2–10 sessions; 18 had none. |
| `artifacts/model.patch` | 9,243 | 11 | 9,048 non-empty unified diffs; 195 empty files. Every present file size matched `result.patch_bytes`. |
| Verifier reward JSON | 9,003 | 251 | All 9,003 carried `reward`, `partial`, f2p/p2p ratios, and passed/total counts. |
| Verifier CTRF | 9,003 | 251 | 9,002 at `verifier/ctrf.json`, one at `verifier/reports/new-ctrf.json`; all summaries carried tests/passed/failed/skipped/pending/other integer counts. |
| Verifier run log | 9,050 | 204 | Presence only; logs are never predictors. |

`reward_binary` was `1` for 2,946 canonical rows, `0` for 6,054, and `-1` for 254. f2p/p2p fields were numeric for the 9,000 verifier-complete rows and null for 254 rows. Declared `resource_policy` existed for only 1,652/9,254 rows (17.9%), so historical budget control is incomplete.

## Cohort and censoring taxonomy

The taxonomy is mutually exclusive and ordered. It distinguishes valid agent failures from incomplete or invalid outcomes.

| Primary disposition | N | Analytical treatment |
|---|---:|---|
| **Eligible verifier-complete rep** | **8,694** | Primary cohort before task sampling: 2,839 successes and 5,855 agent failures. |
| Agent timeout | 63 | Censored; never relabeled as agent failure. |
| Agent infrastructure error | 11 | Excluded; nonzero/non-timeout agent exit. |
| Ambiguous multiple sessions | 267 | Excluded until the result-producing session can be identified without guessing. |
| Missing session | 18 | Excluded; outcome exists but process predictors do not. |
| Verifier timeout after a normal agent exit | 21 | Censored as verifier failure, not agent failure. |
| Verifier skipped an empty patch | 180 | Recorded as an agent no-patch failure, but excluded from the primary binary model because final verifier reward is `-1`, not binary. |

The pilot adds two content-level rules after session parsing:

- an explicit terminal `length`, `max_tokens`, `max_output_tokens`, or `output_limit` stop is **terminal output truncation** and is censored;
- malformed JSONL records are excluded rather than silently skipped for modeling.

The pilot found two terminal output truncations and no malformed records. A `stopReason: error` inside a session is not automatically called truncation or infrastructure failure because agents can continue after such a turn.

## Feature semantics

All predictors come from agent-time native session events or non-outcome result controls. Verifier logs, CTRF, reward details, f2p/p2p, and final patch contents never enter a predictor matrix.

| Signal | Operational definition | Boundary |
|---|---|---|
| Repeated normalized tool actions | Top-level tool name plus canonical JSON arguments; `/app/` and `./` paths align; command whitespace aligns. | Nested operations inside `fabric_exec`, workflow, advisor, or similar calls remain opaque. |
| Repeated reads | Repeated normalized path for top-level `read`. | Different windows of the same file count as a repeated target, while exact action repeats are tracked separately. |
| Repeated searches | Repeated exact top-level grep/find/search action or normalized bash command invoking `rg`, `grep`, `git grep`, `find`, or `fd`. | It does not infer semantically equivalent but textually different queries. |
| Repeated tests without observed edits | Same normalized top-level bash test command repeated in the same successful direct-mutation epoch. | “No edit” means no observed successful `edit`, `write`, or `apply_patch`; bash and nested mutations are not visible. |
| Unchanged repeated failures | Same normalized test command, `isError=true`, and exact normalized output fingerprint within one mutation epoch. | Strict by design; it fired zero times in this pilot. |
| Failure→pass / pass→failure | Adjacent observable outcomes for the same normalized test command, using tool-result `isError`. | No verifier results and no text-only test inference. |
| Edit churn | Successful direct mutation count, repeated mutation targets, failed mutations, and exact inverse `oldText`/`newText` edits. | True intermediate patch size, line churn, and semantic reversion are unsupported because no patch snapshots exist. |
| Strategy reset | Assistant-only phrase matches such as “start over,” “rethink this approach,” “different approach,” “backtrack,” or “abandon this strategy.” | Linguistic and conservative; it is not a state transition oracle. |
| Within-task length outliers | Robust z-scores of log tokens and log turns within each selected task. | These belong to the length baseline, not the process increment. |

## Deterministic pilot

Tasks were ordered by `blake2b-64(task)` without consulting reward values. The first 12 tasks contributed every initially eligible rep. The preflight estimated **370,898,888 bytes** of session input, below the explicit **536,870,912-byte** cap. It selected 987 reps; two terminal truncations left **985** modeling reps.

The cohort spans 12 tasks, 17 models, 6 thinking levels, 86 configs, and four languages. It contains 301 successes and 684 failures.

| Task | Reps | Successes |
|---|---:|---:|
| `wasmi-trap-coredumps` | 34 | 0 |
| `abs-module-cache-flags` | 42 | 17 |
| `httpx-streaming-json-iteration` | 47 | 25 |
| `koota-deferred-mutation-buffer` | 25 | 2 |
| `kcp-go-multiplexed-kcp-streams` | 14 | 8 |
| `go-genai-streamed-function-args` | 15 | 9 |
| `superjson-error-stack-serialization` | 253 | 48 |
| `kombu-virtual-queue-dead-lettering` | 13 | 2 |
| `meriyah-explicit-resource-declarations` | 164 | 33 |
| `dynamodb-toolbox-conditional-attribute-requirements` | 177 | 29 |
| `happy-dom-deterministic-intersectionobserver` | 166 | 107 |
| `prometheus-typed-label-sorting` | 35 | 21 |

### Session schema and signal support

The parser saw 51,995 assistant turns and 56,530 top-level tool calls. Result-level turn and tool-call totals matched parsed totals for every retained rep. Forty-nine calls lacked a matching result; no orphan results appeared.

- 798/985 reps (81.0%) had fully supported top-level tool surfaces.
- 117/985 (11.9%) had mixed supported and opaque tools.
- 70/985 (7.1%) had only opaque semantic tool calls.
- 793/985 (80.5%) had at least one observable top-level test command.
- 912/985 (92.6%) had at least one successful direct mutation.

## Blockers to a substantive corpus claim

These blockers apply before interpreting model deltas.

1. **Nested tool semantics are config-dependent.** `fabric_exec`, workflow, AST, goal, and other wrappers hide reads, searches, tests, or mutations behind a top-level call. Config controls do not restore missing within-trajectory events.
2. **No intermediate patch state exists.** The extractor can measure direct mutation attempts and exact inverse edits, but not true patch churn, partial reversion, or workspace state after bash mutations.
3. **The unchanged-failure oracle is too strict for this corpus.** It produced zero events. Test output often changes timing, ordering, or incidental text even when the failure is functionally unchanged.
4. **Historical budgets are mostly absent.** `resource_policy` exists in only 17.9% of canonical results. Wall time is complete, but it is exposure, not a declared budget.
5. **Task fixed effects and held-out-task prediction are not simultaneously estimable.** The predictive analysis controls task by holding out whole tasks and by unsupervised within-task length normalization. It intentionally does not one-hot task identity because a new task has no learned fixed effect.
6. **The pilot is heterogeneous and unbalanced.** It pools 17 models and 86 configs; one task contributes 253 reps while another contributes 13. Categorical controls help, but they do not prove stable effects across model/config families.
7. **Partial reward is viable but preservation-heavy.** All 985 pilot reps have partial reward, yet high partial scores can coexist with failure on feature tests. It remains secondary.

## Measured pilot observations

### Raw, unadjusted feature differences

Failures were longer on average: 2.57M versus 2.01M tokens and 56.8 versus 43.1 turns. They also had more repeated exact actions (2.96 versus 1.95), repeated read targets (5.36 versus 3.25), direct mutations (14.28 versus 10.52), and failed direct mutations (1.07 versus 0.44).

Strategy-reset language appeared in 109/684 failures (15.9%) and 5/301 successes (1.7%). Repeated searches appeared in 24 failures and no successes. These are unadjusted associations, not independent effects.

The transition pattern did not match the simple prediction. Failures averaged 0.338 observable failure→pass transitions versus 0.213 for successes; pass→failure transitions were also higher in failures (0.069 versus 0.043). Longer failed trajectories have more opportunities for both transitions, and productive recovery can occur before a different hidden test still fails.

### Held-out-task evaluation

Four deterministic folds held out whole tasks. Both fitted models used the same model, thinking-level, and config controls. The length model used log tokens, log turns, log wall time, and within-task token/turn outliers. The process model added the event features above. Both used fixed L2 regularization with no test-fold tuning.

| Model | Log loss ↓ | Macro-task log loss ↓ | Brier ↓ | AUROC ↑ | Average precision ↑ |
|---|---:|---:|---:|---:|---:|
| Fold-train prevalence | 0.644 | 0.657 | 0.224 | 0.354 | 0.254 |
| Length + controls | 0.671 | 0.666 | 0.222 | 0.643 | 0.415 |
| Length + process + controls | 0.826 | 0.741 | 0.249 | 0.613 | 0.384 |
| **Process minus length** | **+0.156** | **+0.074** | **+0.027** | **−0.030** | **−0.031** |

The 2,000-sample task bootstrap estimated the process-minus-length log-loss delta at **+0.038 to +0.278**. Lower is better, so the complete interval favors the length-only specification within this pilot.

For partial reward, the length model reached RMSE 0.119 and MAE 0.063. Adding process features worsened RMSE by 0.010 and MAE by 0.012. The fold-train prevalence baseline had RMSE 0.118.

## Interpretation

This pilot gives no support to the current process-feature model. It instead satisfies a pilot-level falsification direction: the added features did not improve held-out-task prediction beyond length and controls.

The result does not show that trajectory process carries no information. The raw differences show signal, but the current representation is sparse, length-correlated, and unevenly observable across configs. The fixed pooled model may be learning tool-surface identity and task-specific opportunity counts rather than portable failure dynamics. The zero unchanged-failure count is an operationalization failure, not evidence that repeated unchanged failures never occur.

The strongest conclusion is methodological: **do not run or interpret the full corpus yet**. Fix semantic coverage and test-transition normalization first.

## Recommended next step

Run one narrower sensitivity milestone before expanding task count:

1. restrict the primary sensitivity cohort to direct-tool reps with `semantic_event_coverage == 1.0`;
2. stratify or interact by major model/config family, with minimum cell counts declared before fitting;
3. manually label a deterministic sample of repeated test outputs, then replace exact output hashes with a validated failure-signature normalizer;
4. add nested operation extraction only where the native tool result exposes a structured trace; otherwise keep the signal unsupported;
5. rerun the same 12 held-out tasks and require stable improvement in both micro and macro-task log loss before moving to a 36-task pilot.

A 36-task pilot would read roughly three times this milestone's 371 MB if task density is similar. The full canonical session set is about 3.6 GB, but its cost is not justified until the feature observability blockers are closed.

## Reproduction

From the worktree:

```bash
uv run pytest -q tests/test_trajectory_process_signals.py
uv run python -m analysis.trajectory_process_signals.pilot \
  --results /home/will/evals/deep-swe-bench/results \
  --output analysis/trajectory_process_signals/artifacts \
  --pilot-tasks 12 \
  --folds 4 \
  --max-session-bytes 536870912
```

### Validation record

- `uv run --extra test python -m pytest -q` — **495 passed**.
- `ruff format --check analysis/trajectory_process_signals tests/test_trajectory_process_signals.py` — all files formatted.
- `ruff check analysis/trajectory_process_signals tests/test_trajectory_process_signals.py` — all checks passed.
- `uvx ty check analysis/trajectory_process_signals tests/test_trajectory_process_signals.py` — all checks passed.
- `codegraph check --staged --cycles --signatures` — cycles, signatures, and boundaries passed.
- `aislop scan --changes` — 96/100, zero AI-slop, security, lint, or formatting errors; seven advisory function/file-size warnings.
- Deterministic pilot rerun — 987 pre-parse reps, 985 modeling reps, 370,898,888 session bytes.
- Tailnet report check — `http://100.112.72.93:8790/` returned HTTP 200 with the expected 9,664-byte page.

Derived artifacts:

- `artifacts/pilot_manifest.json` — worktree, branch, base, task selection, byte cap, and outputs
- `artifacts/schema_audit.json` — full result/session/verifier/patch audit
- `artifacts/cohort_audit.csv` — one row per canonical result and its disposition
- `artifacts/session_schema_audit.json` — pilot JSONL/tool schema and observability
- `artifacts/pilot_features.csv` — compact per-rep outcomes, controls, and extracted features
- `artifacts/feature_summary.json` — measured feature distributions and support boundaries
- `artifacts/held_out_task_evaluation.json` — folds, model specification, and metrics

## Evidence ledgers

### CodeGraph evidence

- Rebuilt the structural index and narrowed the seam to `harness/cell_trajectory.py`.
- `brief` identified `_parse_session_trajectory`, `_content_text`, usage parsing, and test-summary loading as the stable native-session semantics.
- `deps` showed no static imports for the parser; this analysis therefore uses a standalone parser rather than coupling to dashboard page construction.

### Source-read interpretation

- `harness/cell_trajectory.py` joins assistant tool calls to `toolResult` messages by call ID and reads usage from final native-session messages.
- ADR-0002 establishes native sessions as the executor usage source and warns that secondary model usage is separate.
- ADR-0001 and ADR-0005 define the canonical cell path and rep/cell distinction.
- `docs/result-quarantine.md` requires `_contaminated` results to stay out of normal efficacy analysis.

### Proof commands

The final validation record appears in the branch commit and closing summary. CodeGraph structural checks are scouting evidence only; pytest, Ruff, Ty, the deterministic pilot rerun, and artifact consistency checks provide behavioral evidence.
