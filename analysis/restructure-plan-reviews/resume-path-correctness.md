# Code Review — Resume & Path-Derivation Correctness (RENAME + MIGRATION PLAN)

**Reviewed:** RENAME-PLAN.md, EXECUTION-PLAN-DRAFT.md, CONTEXT.md, docs/adr/0001 — path-derivation correctness vs `harness/run.py`, `harness/run_batch.py`, `harness/lib.py`, `harness/analyze.py`, and live `runs/` data.
**Verdict:** Request changes (two CRITICAL blockers; the plan as written can trigger the "re-run every completed cell" catastrophe for advisor cells, and aborts migration on a real unhandled collision).

## Summary
The shared-`model_leaf()` mitigation in §13 is the right instinct but is underspecified on one load-bearing point: whether the **results path** carries the `+advisor` suffix. `run.py`/`run_batch.py` have no source for `advisor_model` at path-derivation time (it lives inside the config leaf — circular), so if migrate writes `+glm-5.2` into the results path and the resumed batch computes the executor-only leaf, all 153 advisor cells re-run. Separately, `diag`/`validate` cells collide with `ponytail-full-pilot-w2` on `adaptix-name-mapping-aliases` baseline rep0 — a collision §19's policy does not cover — which trips the "fail loud on any other collision" clause and aborts migration.

## Findings

### CRITICAL: Advisor `+glm-5.2` suffix in results path has no computable source at resume time → 153 advisor cells re-run
**Finding ID:** F-001
**File:** `RENAME-PLAN.md` §13/§19 (migrate) vs §14/§15 (`run.py`/`run_batch.py`); cf. `docs/adr/0001-directory-and-vocabulary-reorganization.md` (results vs configs leaf forms)
**Area:** correctness / architecture
**Issue:** The plan is internally inconsistent on whether the **results** path includes the `+advisor` suffix.
- §13 defines `model_leaf(model, advisor_model=None)` that appends `+<advisor last segment>` when `advisor_model` is set → `deepseek-v4-flash+glm-5.2`.
- §19 says migrate "derives `(config, model-leaf, thinking)` via the shared `lib.model_leaf()`" and "computes the destination `results/<model-leaf>/<thinking>/<config>/<task>/rep<N>/`" — i.e. the `model-leaf` (with advisor) is placed in the **results** path.
- migrate CAN read the advisor model: `result.json.arm_advisor.model` = `glm-5.2` (verified, `runs/advisor-glm52-full-w4/pi-advisor-glm52/.../result.json`). So migrate plausibly calls `model_leaf(model, arm_advisor.model)` → writes `results/deepseek-v4-flash+glm-5.2/high/advisor/<task>/rep0/result.json`.

But the resumed harness provably CANNOT compute the same leaf:
- `run_batch.py:24` (today) computes the existence-check path from `args.run_name` + `arm` + `task` + `rep`. After §15 it derives from `model`/`thinking`/`config`. §14 enumerates run.py's path inputs as exactly `model`/`thinking`/`config` — **no `advisor_model`**.
- The advisor model is not a CLI flag (no `--advisor-model` anywhere in §14/§15). After §9's split, `advisor.json` lives **inside** the config leaf (`configs/<config>/<leaf>/<thinking>/advisor.json`), so run.py cannot read it to find the leaf without already knowing the leaf — chicken-and-egg.

Therefore run.py/run_batch call `model_leaf(args.model)` with `advisor_model=None` → compute `results/deepseek-v4-flash/high/advisor/<task>/rep0/` (no suffix). migrate wrote to `results/deepseek-v4-flash+glm-5.2/high/advisor/<task>/rep0/`. The existence-check misses → every advisor cell re-runs (153 cells, paid API quota on deepseek-v4-flash + glm-5.2 advisor calls).

Note ADR-0001 itself keeps the two forms distinct: `configs/<config>/<exec>+<advisor>/<thinking>/...` (configs leaf has `+advisor`) vs `results/<model>/<thinking>/<config>/...` (results uses `<model>`). The plan's §19 conflates them by routing "model-leaf" into the results path.

**Expected behavior:** migrate's destination path and the resumed `run_batch` existence-check path must be byte-identical for every cell, including advisor cells.
**Why it matters:** This is the exact "silent re-run-everything catastrophe" the review targets — for the one config (advisor) where the path derivation differs by the `+glm-5.2` token.
**Suggested Fix:** State explicitly that the **results** path uses `model_leaf(model)` with `advisor_model=None` (executor-only); the `+advisor` suffix lives **only** in the `configs/<config>/` leaf dir name (matching ADR-0001's results-vs-configs split). Then migrate and run.py both call `model_leaf(model)` (no advisor) for results → byte-identical. To discover the configs leaf at run time, run.py scans `configs/<config>/*/` for a dir whose executor segment equals `model_leaf(model)` (or take an explicit `--leaf`/`--model-leaf` flag). Add a smoke-test that resumes an **advisor** cell (not just baseline, as §5e/§25 currently specify) and asserts the existence-check skips it.
**Blocking:** yes

### CRITICAL: `diag`/`validate` cells collide with `ponytail-full-pilot-w2` on `adaptix-name-mapping-aliases` baseline rep0 — unhandled by §19's collision policy → migration aborts or silently overwrites
**Finding ID:** F-002
**File:** `RENAME-PLAN.md` §19 (collision policy) vs live data: `runs/diag/baseline/adaptix-name-mapping-aliases/rep0/result.json`, `runs/validate/baseline/adaptix-name-mapping-aliases/rep0/result.json`, `runs/validate-fixed/baseline/adaptix-name-mapping-aliases/rep0/result.json`, `runs/ponytail-full-pilot-w2/baseline/adaptix-name-mapping-aliases/rep0/result.json`
**Area:** correctness / data integrity
**Issue:** Four distinct runs each have a cell at `(model=openrouter/deepseek/deepseek-v4-flash, arm→config=baseline, task=adaptix-name-mapping-aliases, rep=0)`. After thinking backfill (all are MISSING → `high`), all four map to the SAME destination:
`results/deepseek-v4-flash/high/baseline/adaptix-name-mapping-aliases/rep0/result.json`

Verified cell values:
- `diag`: `reward_partial=0.0` (diagnostic throwaway)
- `validate`: `reward_partial=0.0`
- `validate-fixed`: `reward_partial=0.0`
- `ponytail-full-pilot-w2`: `reward_partial=0.998` (the real result)

§19's collision policy resolves only two collisions (advisor reliability-rerun, codex-spark-baseline-sub). Its catch-all ("Any collision not covered by the two policies above fails loud") would trip here → migration aborts at this cell. Yet §8/§19's backfill explicitly COUNT `diag` (1) + `validate` (1) + `validate-fixed` (2) among the 253 cells to backfill, so the plan intends to migrate them — contradiction. If the dry-run's collision detector misses the run-name-drop collision for same-config cells (the two listed collisions are both cross-run-name), the move silently overwrites `ponytail-full-pilot-w2`'s real 0.998 cell with a 0.0 diagnostic cell.

**Expected behavior:** Migration does not abort on a collision the plan's own §8 says is in scope, and does not silently overwrite a real result with a diagnostic 0.0.
**Why it matters:** Either migration is blocked (so no resume at all), or the baseline `adaptix-name-mapping-aliases` result is corrupted to 0.0 — and `adaptix-name-mapping-aliases` is the exact task §5e/§25 pick for the smoke-test, so a bad cell here poisons the smoke-test too.
**Suggested Fix:** Exclude `diag`/`validate`/`validate-fixed` from migration in §2's inventory (they are diagnostic throwaways, not "worth migrating" per §2). Remove them from the §8 253-cell count. Add `adaptix-name-mapping-aliases/baseline/rep0` to the dry-run's mandatory collision list so the keep-decision (ponytail-full-pilot-w2) is explicit and auditable.
**Blocking:** yes

### HIGH: Rep renumbering (§19) does not specify rewriting the in-file `rep` field → analyze.py dedup collision → silent data loss
**Finding ID:** F-003
**File:** `RENAME-PLAN.md` §19; `harness/analyze.py:83,95` (`keyed = {(r["task"], r.get("rep", 0), r["arm"]): r for r in rows}`)
**Area:** correctness / data integrity
**Issue:** §19 renumbers `advisor-glm52-reliability-rerun` (40 cells) and `codex-spark-baseline-sub` (18 cells) to `rep1`. "Renumber" is ambiguous: does it (a) move the dir to `rep1/` only, or (b) also rewrite `result.json.rep` from `0` to `1`? §19 does not say. analyze.py keys rows by the **in-file** `r.get("rep", 0)` and the **in-file** `r["arm"]` — NOT by the directory's `repN`. Verified: today every cell's in-file `rep` already matches its path `repN` (checked all `runs/` — zero mismatches), so the invariant migrate must preserve is "in-file rep == path repN". If migrate moves the dir to `rep1/` but leaves `result.json.rep=0`, then:
- `results.jsonl` rebuild (§20) reads `rep:0` for the renumbered cell → it keys as `(task, 0, advisor)` and collides with the genuine `advisor-glm52-full-w4` rep0 cell → the `keyed` dict overwrites one → one rep is silently dropped from analysis.
- analyze.py's `load_results` globs `rep*/result.json` and keys on the in-file field, so the path `rep1/` is invisible to it.

Affects 40 + 18 = 58 renumbered cells.
**Expected behavior:** After migration, `result.json.rep` equals the `repN` of its containing directory for every cell.
**Why it matters:** Silent dropping of reps in paired analysis (the renumbered cells are the "extra reps" the policy is meant to preserve) — the exact data the reliability rerun was run to collect.
**Suggested Fix:** §19 must state explicitly: migrate rewrites `result.json["rep"] = N` for every renumbered cell (and logs it in `migrate-thinking-audit.jsonl` or a sibling audit log). Add a post-migrate assertion: for every `results/**/repN/result.json`, `rec["rep"] == N`.
**Blocking:** yes (before migration is trusted)

### HIGH: Migrated `result.json` keeps stale `arm` field with OLD names; new cells write `config` → analyze.py grouping breaks and path-config-name diverges from in-file name
**Finding ID:** F-004
**File:** `RENAME-PLAN.md` §13 (writer change) vs §19 (migrate, silent on field rewrite); `harness/analyze.py:73,83,95` (groups/keys on `r["arm"]`)
**Area:** correctness / data integrity
**Issue:** §13 changes `result_record(arm=...)` → `result_record(config=...)`, so **new** cells get a `config` key. §19 does not say migrate rewrites the existing `arm` field in moved `result.json`. So post-migration the tree holds:
- migrated cells: `"arm": "pi-advisor-glm52"` (old name), no `config` key
- new cells: `"config": "advisor"`, no `arm` key

analyze.py groups by `r["arm"]` (today) and §16 says analyze drops the "arm" column/word — but with mixed data, `r["arm"]` is `None` for every new cell (KeyError on `r["arm"]` at `analyze.py:83` `by_arm[r["arm"]]`). And the migrated advisor cells are grouped under `pi-advisor-glm52`, not `advisor` — so a comparison filtering `--configs advisor,baseline` finds zero advisor rows (they're under the old name). The path says `results/.../advisor/` but the in-file field says `pi-advisor-glm52`.
**Expected behavior:** Every migrated `result.json` carries `config` = the NEW mapped name (e.g. `advisor`, `observational-memory`, `baseline-wf`), and `arm` is either removed or kept-as-alias consistently.
**Why it matters:** Comparisons silently return empty for renamed configs; the migrate→analyze handoff is broken for every config that §11 renamed (advisor, observational-memory, baseline-wf, ponytail-extension).
**Suggested Fix:** §19 must state: migrate rewrites each `result.json` `arm`→`config` using the §11 map (and drops the legacy `arm` key, or keeps both). §20's `results.jsonl` rebuild then emits `config`. analyze.py §16 reads `config` (falling back to `arm` only if migrating incrementally).
**Blocking:** yes

### MEDIUM: Backfill's `command:` header is operator-added (not harness-written) and present in only 1 of ~25 logs; which file to read is unspecified
**Finding ID:** F-005
**File:** `RENAME-PLAN.md` §19; live logs
**Area:** correctness
**Issue:** §19 backfill says "parse that run's batch-log `command:` header line for `--thinking`". But `run_batch.py` never writes a `command:` line — its first output is `"running N cells..."` (verified, `harness/run_batch.py:97`). The `command:` header exists in exactly ONE log: `runs/ponytail-full-pilot-w2/batch-ponyext-w8.out` (operator-prepended): `command: python3 harness/run_batch.py --arms baseline,ponytail-pi-extension --run-name ponytail-full-pilot-w2 --workers 8` (no `--thinking` → default `high`). The canonical `runs/ponytail-full-pilot-w2/batch.out` has NO such header. `diag`/`validate`/`validate-fixed` have NO `.out` log at all (only `results.jsonl` + verifier logs).
So for the 249 `ponytail-full-pilot-w2` MISSING cells, the backfill works only if migrate reads `batch-ponyext-w8.out` specifically — §19 says "the run's batch-log" without naming the file. For `diag`/`validate` there is no batch log → §19's "fail-loud if no inference source" triggers → but F-002 says these collide anyway.
**Expected behavior:** A backfill mechanism that doesn't depend on an operator-manually-prepended line that the harness never emits.
**Why it matters:** If migrate reads `batch.out` (the obvious "the batch log"), it finds no `command:` → treats as "no batch log" → fail-loud → migration aborts on 249 cells. The 249-cell backfill is the bulk of the missing-thinking data.
**Suggested Fix:** Specify the exact log-file selection (e.g. "the `*.out` in the run dir whose first line starts with `command:`; else the lexically-first `batch*.out`"). Better: since `run_batch.py`'s default thinking is `high` and §19 already says "if omitted use default high", drop the log-parsing entirely and backfill all MISSING → `high` with an audit-log note "defaulted; no --thinking in any source" — the only run lacking the field that used a non-default thinking would have to be verified manually, and the data shows none do (all MISSING cells are from `--arms ...,ponytail-*` runs with no `--thinking`).
**Blocking:** no

### MEDIUM: §11 states wrong model for codex54mini leaf (`gpt-5.4-mini`); actual data is `openai-codex/gpt-5.5`
**Finding ID:** F-006
**File:** `RENAME-PLAN.md` §11; live data `runs/codex55-medium-om54mini-w2/pi-observational-memory-codex54mini/.../result.json`
**Area:** correctness / docs
**Issue:** §11: "pi-observational-memory-codex54mini folds into observational-memory as another model leaf (`openai-codex/gpt-5.4-mini` + its thinking)." Verified actual model across all 113 codex54mini cells: `openai-codex/gpt-5.5`, thinking `medium` (run name `codex55-medium-om54mini-w2`). §10 says "Materialize model leaves using `result.json` as the source of truth" — so migrate would create the leaf as `gpt-5.5` (correct) — but §11's text names `gpt-5.4-mini`. If an implementer manually creates/verifies the leaf from §11, the configs leaf dir is `gpt-5.4-mini` while migrate/run.py compute `gpt-5.5` → `configs/observational-memory/gpt-5.5/medium/` not found → config load fails on resume.
**Expected behavior:** §11 names the actual model recorded in `result.json`.
**Suggested Fix:** Correct §11 to `openai-codex/gpt-5.5` / `medium`. Note: there is no path collision from the fold — `observational-memory`'s other leaves are `deepseek-v4-flash` and `Qwen3.6-27B-AWQ-BF16-INT4` (distinct last-segments), and `gpt-5.5/medium` under `observational-memory` is distinct from `gpt-5.5/medium` under `baseline`/`baseline-wf` by the config axis.
**Blocking:** no

### MEDIUM: §14 path template uses `<model>`, not `model_leaf(model)` — implementer can use raw `--model` (with slashes) → nested wrong dirs
**Finding ID:** F-007
**File:** `RENAME-PLAN.md` §14 (run.py), §15 (run_batch.py)
**Area:** correctness / readability
**Issue:** §14: "Output root `runs/<run_name>/<arm>/<task>/rep<N>` → `results/<model>/<thinking>/<config>/<task>/rep<N>`." The literal `<model>` is ambiguous: is it the raw `--model` value (`openrouter/deepseek/deepseek-v4-flash`, containing slashes → creates `results/openrouter/deepseek/deepseek-v4-flash/high/...` nested dirs) or `model_leaf(model)` (`deepseek-v4-flash`)? §13 says model_leaf is "used by BOTH migrate and run.py/run_batch.py", so the intent is the leaf — but §14's template doesn't show the call, so an implementer working from §14 alone could pass `args.model` raw. migrate (per §19) uses `model_leaf()`. Raw-vs-leaf divergence → mismatch.
**Expected behavior:** §14/§15 templates literally show `model_leaf(model)` as the segment.
**Suggested Fix:** Write the template as `results/{model_leaf(model)}/{thinking}/{config}/{task}/rep{N}/` in §14 and §15, and show the one-line `leaf = model_leaf(args.model)` call. This is the cheapest way to guarantee migrate and harness emit the same segment.
**Blocking:** no

### MEDIUM: Q-A unresolved — wrong/missing `--subset` on resume yields incomplete or unexpected re-run scope
**Finding ID:** F-008
**File:** `EXECUTION-PLAN-DRAFT.md` §6 (Q-A `[UNVERIFIED]`), `harness/run_batch.py:90-99` (subset = task-id selection only)
**Area:** correctness / ops
**Issue:** subset is correctly a selection, not a path component (ADR-0001; verified `run_batch.py:24` path has no subset, only run_name/arm/task/rep). So a wrong `--subset` does NOT corrupt paths — but it changes which `(task, rep)` the resumed batch iterates. `codex-spark-baseline-w2` was originally `--subsample fast-iter-v1` (36 tasks). If resumed with `--subset 12`, run_batch iterates only 12 tasks → 24 never-completed tasks are never attempted (incomplete resume, no error). If resumed with `--subset 113`, it correctly expands (45 exist→skip, 68 run). The `[UNVERIFIED]` flag is acknowledged in §6 but it is a hard blocker on trusting any resume command.
**Expected behavior:** Resume commands carry the original subset (or an explicitly-approved superset).
**Suggested Fix:** Resolve Q-A from shell/tmux history before §6; until then §6 commands are templates, not executable (already noted — keep it a gate, don't relax).
**Blocking:** no (already flagged by the plan)

## What's Good
- §13's instinct to put path-segment derivation in ONE shared `model_leaf()` imported by both migrate and harness is exactly the right structural defense against path divergence — the problem is only that one input (`advisor_model`) is asymmetrically available.
- ADR-0001 keeps `results/<model>/...` (executor) distinct from `configs/<exec>+<advisor>/...` (advisor-suffixed) — the clean resolution to F-001 is already latent in the ADR; §19 just needs to honor it for the results path.
- The collision policy for advisor reliability-rerun and codex-spark-baseline-sub is correct in intent (genuine extra reps, renumber not merge) — F-003 is the missing in-file-rewrite step, not a wrong policy.
- Verified: last-`/`-segment normalization is stable and collision-free for all 4 real model strings (`deepseek-v4-flash`, `gpt-5.3-codex-spark`, `gpt-5.5`, `Qwen3.6-27B-AWQ-BF16-INT4`); no two distinct models share a leaf today. The advisor model `glm-5.2` has no `/` so its last segment is itself — the `+glm-5.2` literal is unambiguous *if* advisor_model is passed consistently.
- Verified: `arms/baseline-codex/orchestration.md` is byte-identical to `arms/baseline/orchestration.md`, so the §11 fold of `baseline-codex`→`baseline` is behaviorally safe for the constant files.
- Verified: today every cell's in-file `rep` matches its path `repN` (zero mismatches across all `runs/`) — so the renumber-rewrite requirement (F-003) preserves an existing invariant rather than inventing one.
