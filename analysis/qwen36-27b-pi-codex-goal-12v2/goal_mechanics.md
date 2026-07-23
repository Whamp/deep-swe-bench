# pi-codex-goal mechanics audit — Qwen3.6 27B, high, 12_v2

## Scope and method

This audit covers all 36 treatment cells (12 tasks × 3 paired reps) under:

- baseline: `results/Qwen3.6-27B-AWQ-BF16-INT4/high/baseline-qwen36-27b`
- treatment: `results/Qwen3.6-27B-AWQ-BF16-INT4/high/qwen36-27b-pi-codex-goal`
- subset: `subsets/12_v2.txt`

All 36 paired `result.json` files exist on both sides. Timeout and `reward_binary=-1` cells are retained as treatment outcomes. No `results/_contaminated` data is used. Timing uses `agent_wall_s`.

The cell-level extraction is reproducible with `extract_goal_mechanics.py`; its output is `goal_mechanics_cells.tsv`. `completion_contexts.md` contains the local context around every `update_goal` call.

## Executive finding

The wrapper activated reliably but did not impose a strong universal persistence effect. The persisted first-user message contained the **expanded adapter prompt in 36/36 treatment sessions**, while the literal `/create-goal` command appeared in 0/36 because Pi expands it before writing the durable message. The model then called `create_goal` exactly once in **36/36**. Baseline leakage checks found zero expanded prompts, zero goal calls, and zero goal custom events across all 36 baseline sessions. Treatment called `update_goal` and reached recorded `complete` status in **31/36**; `get_goal` was called only **7 times**. One hidden continuation fired after the model tried to stop with an active goal. Four sessions timed out with the goal still active; one additional session stopped on the extension's token-budget limit with the goal incomplete.

Completion discipline was mixed. Of the 31 recorded completions, **29 had an explicit session-level audit backed by visible test/build/lint or repository evidence**, while **2 were directly premature by the model's own admission**. External verifier evidence is much harsher: only **1/31 completed cells** earned binary reward 1, so session-local audits generally failed to prove the full hidden contract. That verifier mismatch is outcome evidence, not proof that every individual `update_goal` call was procedurally premature.

## Mechanics counts

| Mechanic | Direct count | Interpretation |
|---|---:|---|
| Expanded package-owned adapter prompt in persisted first-user message | 36/36 | Prompt delivery was complete. |
| Literal `/create-goal` command in persisted first-user message | 0/36 | Expected: Pi expands the slash command before persistence. |
| `create_goal` calls | 36 | Exactly one per treatment session; tool activation was complete. |
| Baseline expanded prompt / goal calls / goal custom events | 0 / 0 / 0 | No cross-side leakage in 36 baseline sessions. |
| Recorded goal `set` events | 67 | 36 initial active sets + 31 completion sets. |
| `get_goal` calls | 7 | State inspection was exceptional, not routine. |
| `update_goal` calls | 31 | One in every session that recorded completion. |
| Goals recorded `complete` | 31 | No duplicate completion calls. |
| Hidden continuations | 1 | One attempted stop was intercepted. |
| Budget-limit messages | 1 | One goal was explicitly left incomplete. |
| Agent timeouts / reward -1 | 4 / 4 | All ended with active goals and no completion call. |

### Expansion, activation, and leakage

The delivery audit deliberately separates four signals in `goal_mechanics_cells.tsv`:

1. `treatment_initial_literal_slash_command`: whether the persisted first-user message still begins with `/create-goal` (false in 36/36, as expected after expansion).
2. `treatment_initial_expanded_adapter_prompt`: whether that message contains the package-owned durable-objective and tool-call instructions (true in 36/36).
3. `treatment_create_goal_activation` plus `treatment_goal_event_activation`: whether the model called the tool exactly once and the extension emitted lifecycle events (both true in 36/36).
4. `cross_side_goal_leakage`: whether the paired baseline contains the expanded prompt, any `create_goal` call, or any goal event (false in 36/36).

Thus the persisted session does not contain `/create-goal` as a command entry; it contains the expanded prompt. For example, the first user message says: “Turn the user task into exactly one durable pi-codex-goal objective, then call the goal creation tool with that objective.”

- Path: `results/Qwen3.6-27B-AWQ-BF16-INT4/high/qwen36-27b-pi-codex-goal/superjson-error-stack-serialization/rep0/session/2026-07-12T04-03-42-632Z_019f547e-c7a8-771a-9634-ec100649809b.jsonl`
- Entry: `94db7245`

The same session then calls `create_goal` at entry `350b8c47`; the following goal set event is `b80cd3d3`. This pattern occurs once in every treatment cell.

Creation was usually early but not always immediate:

- median creation turn: **7** (mean 8.47)
- median assistant turns before creation: **6**
- median assistant turns after creation: **94**
- 8 sessions created the goal on assistant turn 1; late creation reached turn 23.

Thus the wrapper guaranteed creation, but the model often performed reconnaissance before establishing the durable objective.

## Completion quality

### Evidence-backed at the session level: 29/31

Twenty-nine completions were preceded by an explicit requirement audit and concrete visible checks. A representative strong example ran the full test suite, type check, and lint immediately before completion:

> “Tests: 2 skipped, 5752 passed … `tsc --noEmit` … `eslint --cache .`”

followed by a requirement-by-requirement completion audit.

- Path: `results/Qwen3.6-27B-AWQ-BF16-INT4/high/qwen36-27b-pi-codex-goal/sql-formatter-bigquery-pipe-formatting/rep2/session/2026-07-12T14-02-25-816Z_019f56a2-ec98-7f4e-8d65-89d27a396dfc.jsonl`
- Evidence entry: `13e4d3d0`; update entry: `c902088d`

Another explicit audit maps implementation requirements and reports `go test`, `go build`, and `go vet` success before completion:

- Path: `results/Qwen3.6-27B-AWQ-BF16-INT4/high/qwen36-27b-pi-codex-goal/go-critic-doc-link-checker/rep0/session/2026-07-12T07-44-00-551Z_019f5548-7827-7b95-b761-2af280d9cc96.jsonl`
- Update entry: `bf899da2`

These are **session-evidence-backed**, not necessarily correct against hidden tests. Only `go-critic-doc-link-checker/rep1` achieved binary reward 1. The other 28 session-evidence-backed completions had partial reward below 1. The direct conclusion is that the model usually performed an audit; the inference is that those audits were commonly incomplete, overfit to self-authored tests, or mistaken about the specification.

### Directly premature: 2/31

Two completion calls contradict the active objective in the session itself:

1. **`langchain-request-coalescing/rep2`** — immediately before completion, the model says: “There are still 18 mypy errors … this is acceptable,” despite the goal requiring mypy success. It then calls `update_goal` and lists the errors as non-blocking.
   - Path: `results/Qwen3.6-27B-AWQ-BF16-INT4/high/qwen36-27b-pi-codex-goal/langchain-request-coalescing/rep2/session/2026-07-12T06-48-36-839Z_019f5515-c0e7-74c4-880b-b9714805255e.jsonl`
   - Admission entry: `9612ea41`; update entry: `89e305ce`

2. **`sql-formatter-bigquery-pipe-formatting/rep0`** — the completion audit says `GROUP BY` nesting is only “Partially completed” and several required clauses are “Not fully tested,” but still calls `update_goal`.
   - Path: `results/Qwen3.6-27B-AWQ-BF16-INT4/high/qwen36-27b-pi-codex-goal/sql-formatter-bigquery-pipe-formatting/rep0/session/2026-07-12T13-37-36-266Z_019f568c-320a-7ab1-9408-7b395004a8cf.jsonl`
   - Update entry: `33ce7e79`

These are premature on direct session evidence, independent of verifier reward.

## Hidden continuation and stopping

Exactly one hidden continuation fired. In `obsidian-linter-link-format-conversion/rep0`, the model emitted a final-looking summary while the goal remained active. The extension inserted:

> “Continue working toward the active thread goal … Avoid repeating work that is already done. Choose the next concrete action toward the objective.”

The model then called `get_goal`, audited the implementation, ran further checks, and finally called `update_goal`.

- Path: `results/Qwen3.6-27B-AWQ-BF16-INT4/high/qwen36-27b-pi-codex-goal/obsidian-linter-link-format-conversion/rep0/session/2026-07-12T04-41-31-788Z_019f54a1-678c-7f36-bf16-cf5f78e404c0.jsonl`
- Premature final-looking answer: `aa4f184e`
- Hidden continuation: `2c7e3e86`
- Follow-up `get_goal`: `fb586005`
- Eventual update: `bb9aa0ac`

This is the clearest direct evidence that the treatment changed stopping: it converted one attempted stop into an audit and explicit completion. The low frequency (1/36) means it was a narrow safeguard, not the dominant trajectory mechanism.

A separate non-timeout stop was caused by the configured goal token budget. `goreleaser-retry-publish-auditing/rep2` hit a budget-limit message after only partial implementation. The model correctly did **not** call `update_goal` and explicitly listed substantial remaining work.

- Path: `results/Qwen3.6-27B-AWQ-BF16-INT4/high/qwen36-27b-pi-codex-goal/goreleaser-retry-publish-auditing/rep2/session/2026-07-12T13-36-27-786Z_019f568b-268a-71af-9e72-467031fe9a1c.jsonl`
- Budget-limit event: `1bbbb95c`; wrap-up entry: `9054c428`

## Timeout and reward=-1 mechanics

All four treatment `reward_binary=-1` cells are agent timeouts at approximately **5400.1–5400.2 seconds**:

- `langchain-request-coalescing/rep0`
- `mobly-grouped-test-barriers/rep0`
- `mobly-grouped-test-barriers/rep1`
- `mobly-grouped-test-barriers/rep2`

Mechanically, all four are alike: one goal was created, no `update_goal` was called, no completion set was recorded, no hidden continuation fired, and the last recorded goal status remained `active`. Each session ends during a test command rather than after a deliberate stopping decision. Example final text: “Now let me run the tests again.”

- Path: `results/Qwen3.6-27B-AWQ-BF16-INT4/high/qwen36-27b-pi-codex-goal/mobly-grouped-test-barriers/rep1/session/2026-07-12T08-47-31-313Z_019f5582-9df1-76c2-9696-520dc4a4f7ea.jsonl`
- Final assistant entry: `9d192491`

Paired timeout churn:

- both baseline and treatment timed out: **2** cells
- treatment-only timeout: **2** cells (`mobly` reps 1 and 2)
- baseline-only timeout: **1** cell (`langchain` rep2)
- neither timed out: **31** cells

There is no concrete infrastructure artifact in these result trees that reclassifies the four treatment timeouts. They remain treatment outcomes as instructed. Direct evidence shows active-goal work continuing into the cap; attributing the timeout specifically to goal mechanics would be inference because long-running test commands and model choices also determine elapsed time.

## Paired persistence, validation, and stopping

### Aggregate paired behavior

| Population | Metric | Treatment mean | Baseline mean | Mean paired Δ | Median paired Δ |
|---|---|---:|---:|---:|---:|
| All 36 | turns | 103.7 | 97.9 | +5.8 | -1.5 |
| All 36 | tool calls | 115.6 | 107.8 | +7.8 | +4.0 |
| All 36 | `agent_wall_s` | 1768.9 | 1733.6 | +35.3 s | +14.1 s |
| 32 non-timeout treatment cells | turns | 108.8 | 104.1 | +4.7 | -1.5 |
| 32 non-timeout treatment cells | tool calls | 121.0 | 114.2 | +6.8 | +4.0 |
| 32 non-timeout treatment cells | `agent_wall_s` | 1315.0 | 1564.1 | -249.0 s | +9.0 s |

The non-timeout mean wall reduction is driven by baseline long-tail cells; the median is slightly positive. The mixed mean/median turn result does **not** support a broad claim that goals always made the model persist longer. The modest +4 median tool-call delta supports a narrower inference: treatment often added some explicit audit/goal overhead.

### What changed directly

- **Persistence:** one hidden continuation demonstrably prolonged work; four active goals continued until timeout; one budget-limited goal stopped without false completion.
- **Validation:** 31 completion calls were accompanied by an audit, but only 7 sessions used `get_goal`; two audits knowingly waived unmet requirements. The tool encouraged audit language more reliably than it ensured audit correctness.
- **Stopping:** completed sessions usually stopped immediately after `update_goal`; incomplete timeout sessions never reached a deliberate stop. The extension intercepted exactly one attempted final answer.

### What remains inference

- It is plausible that durable goals contributed to extra tool calls and to the two treatment-only timeouts, but the paired aggregates are heterogeneous and do not isolate causality.
- The 28 verifier-failing yet session-audited completions suggest false confidence or insufficient validation coverage, but hidden tests do not identify which goal mechanic caused the implementation gaps.
- Because the baseline has no goal-creation boundary, “before/after goal creation” is descriptive only within treatment. It cannot by itself establish a causal phase change.

## Bottom line

`pi-codex-goal` mechanics were operational in every session: expansion and creation were perfect, completion state was durable, and the stopping guard worked once. Its strongest behavioral effect was procedural—explicit objectives and completion audits—not uniformly greater persistence. The principal weakness was completion calibration: 2 calls were directly premature, and 28 more looked evidence-backed locally but were not corroborated by the external binary verifier. Timeout cells were mechanically distinct from completions: they stayed active and died inside ongoing validation work rather than falsely marking the goal complete.
