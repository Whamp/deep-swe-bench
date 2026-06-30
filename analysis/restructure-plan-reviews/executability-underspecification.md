# Adversarial Review — Executability & Underspecification

**Reviewed:** RENAME-PLAN.md + EXECUTION-PLAN-DRAFT.md (rename + migration of eval harness)
**Angle:** Every place the plan says "do X" without specifying HOW, where a reasonable executor would guess — and the guess is wrong or dangerous.
**Verdict:** Request changes — 4 CRITICAL blockers prevent safe execution

## Summary
The plan is well-researched on intent but has 4 provable execution traps that would silently corrupt data: (1) the models.json fallback reads mutated files, (2) thinking backfill is impossible for 4 cells with no batch log AND the plan contradicts itself on whether to fail, (3) the migrate step imports a function that doesn't exist until a later step, (4) the advisor filter spec is ambiguous and no script exists. Ground against live repo confirms every claim below.

## Findings

### C1: models.json fallback reads MUTATED arms/ files — produces wrong leaf content
**Finding ID:** F-001
**File:** RENAME-PLAN.md §10 (provenance rules), lines ~155-165
**Area:** correctness
**Issue:** The plan says: "only fall back to the current arms/*/models.json when those fields are absent (older cells: ponytail, om-memory-pilot-w10, codex-spark-baseline-w2, diag/validate). For those fallback cells the path-axis model is still correct; only the leaf pricing/compat metadata is inferred."

This is catastrophically wrong. Git history (commit `4e91e87`, "Add local Qwen benchmark arm config", today 2026-06-26 11:55) shows:
- `arms/baseline/models.json` was CREATED as a new file (did not exist before) containing only the Qwen model (`local-vllm/cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4`).
- `arms/pi-observational-memory/models.json` was MODIFIED from `{"providers":{"openrouter":{"baseUrl":"https://openrouter.ai/api/v1","apiKey":"$OPENROUTER_API_KEY"}}}` to the same Qwen config.

For the fallback cells:
- **codex-spark-baseline-w2** (arm=`baseline`, model=`openai-codex/gpt-5.3-codex-spark`, `arm_models: None`): The fallback would read the current `arms/baseline/models.json` (Qwen) and produce a leaf at `configs/baseline/gpt-5.3-codex-spark/high/models.json` containing Qwen provider config — wrong API format (`qwen-chat-template` vs codex), wrong cost (0 vs real), wrong contextWindow. The file DIDN'T EXIST when this cell ran (confirmed: `git show d3a9e04:arms/baseline/models.json` → "FILE DID NOT EXIST").
- **om-memory-pilot-w10** (arm=`pi-observational-memory`, model=`openrouter/deepseek/deepseek-v4-flash`, `arm_models: None`): The fallback would read the current `arms/pi-observational-memory/models.json` (Qwen) instead of the original (openrouter). The cell ran with an openrouter models.json.
- **ponytail-full-pilot-w2** (arm=`ponytail-full`, `arm_models: None`): `arms/ponytail-full/` has NO models.json at all (only `orchestration.md` + `skills/`). The fallback fails silently.

**Expected behavior:** The leaf models.json for fallback cells must either (a) not be created (the cell already ran; models.json is only needed for re-runs), or (b) be recovered from git history at the commit that preceded the cell's run.

**Why it matters:** A wrong models.json leaf means: broken re-runs (wrong API format), wrong cost_usd in future analysis, and the exact mutation bug ADR-0001 was created to prevent — now reintroduced via the fallback path. The plan acknowledges the mutation bug exists but its fallback path doesn't protect against it.

**Suggested Fix:** Replace the fallback rule with: "When `arm_models` is absent in result.json, do NOT create a models.json leaf. Instead, log to `migrate-models-audit.jsonl` with the cell path, model, and 'arm_models absent; no leaf created'. If the operator needs a models.json for re-runs, they must provide it manually." For om-memory-pilot-w10 specifically, `git show d3a9e04:arms/pi-observational-memory/models.json` recovers the original openrouter config — but the plan must specify this git-recovery step explicitly, not assume the executor will discover it.
**Blocking:** yes

### C2: Thinking backfill impossible for diag/validate/validate-fixed (no batch log) + plan contradicts itself
**Finding ID:** F-002
**File:** RENAME-PLAN.md §19, lines ~195-210
**Area:** correctness
**Issue:** The plan says to backfill thinking_level for 253 cells missing the field by "parsing that run's batch-log `command:` header line for `--thinking`." Then: "Only fail-loud if a cell lacks `thinking_level` AND its run has no batch log to infer from."

But it ALSO says (same section): "Do NOT fail-loud on these (that would abort migration at cell #1 of `diag`)."

These contradict. Verified against the repo: `runs/diag/`, `runs/validate/`, `runs/validate-fixed/` contain NO `.out` files at all (only `baseline/`, `ponytail-full/`, `results.jsonl`). There is no batch log to parse. So:
- If the executor follows "fail-loud if no batch log" → migration aborts at diag cell #1.
- If the executor follows "do not fail-loud on these" → they must guess a thinking value with no source, and the "log every imputed value" audit trail has no input to log.

The likely-wrong default: silently default to `high` without an audit entry (since there's no batch log to record as the source), or abort the migration entirely.

**Expected behavior:** The plan must specify exactly what happens for the 4 cells (diag=1, validate=1, validate-fixed=2) that have no batch log: assign `thinking_level="high"` (the harness default, `run.py:39` `DEFAULT_THINKING = "high"`), log to `migrate-thinking-audit.jsonl` with `source: "harness_default_no_batch_log"`, and proceed. Remove the contradiction.

**Why it matters:** Either migration aborts (blocking all downstream work) or 4 cells get an un-audited thinking value that could be wrong (if these were actually run with a non-default thinking level, the cells land in the wrong tree and can't be found by model+thinking queries).

**Suggested Fix:** Replace "Only fail-loud if a cell lacks thinking_level AND its run has no batch log to infer from" with: "If a run has no batch log (diag, validate, validate-fixed), assign thinking_level='high' (harness default) and log source='no_batch_log_default' to migrate-thinking-audit.jsonl. Fail-loud ONLY if a cell has a batch log with a command: header whose --thinking value conflicts with another rep of the same (model, config, task, rep)."
**Blocking:** yes

### C3: Circular dependency — migrate (§5c) needs lib.model_leaf() added in §5d
**Finding ID:** F-003
**File:** EXECUTION-PLAN-DRAFT.md §7 (ordering), RENAME-PLAN.md §13
**Area:** architecture
**Issue:** EXECUTION-PLAN §7 orders the steps as: 5b (rename configs) → 5c (migrate) → 5d (edit harness). RENAME-PLAN §13 says: "Add the single shared `model_leaf(model, advisor_model=None) -> str` normalization used by BOTH migrate_results.py and the new run.py/run_batch.py path derivation."

`migrate_results.py` (§5c) MUST import `lib.model_leaf()` to derive destination paths — but `lib.model_leaf()` is added in §5d (Phase 3 code changes), which runs AFTER §5c. Verified: `grep -n model_leaf harness/lib.py` returns nothing (exit=1); the function does not exist.

The executor would likely inline the model_leaf logic in migrate_results.py, then add a SEPARATE implementation to lib.py in §5d — defeating the plan's explicit invariant: "migrate and harness import it so they cannot diverge (the resume-re-runs-everything failure mode)." Two independently-written implementations of the same path derivation is exactly the divergence the plan says it prevents.

**Expected behavior:** `lib.model_leaf()` exists and is imported by both migrate_results.py and run.py/run_batch.py before either is used.

**Why it matters:** If the migrate script and the harness derive paths differently, migrated cells land at paths the harness doesn't check on resume → the harness re-runs every cell (the exact failure mode the plan exists to fix). This is a silent, data-doubling bug.

**Suggested Fix:** Reorder §7: move the `lib.model_leaf()` addition to BEFORE §5c. Specifically: "5b: rename configs AND add lib.model_leaf() to harness/lib.py (the function is pure, no CLI change needed yet). 5c: migrate (imports lib.model_leaf). 5d: edit run.py/run_batch.py CLI to use --config and import lib.model_leaf()." Alternatively, make §5c's migrate script define model_leaf inline AND have §5d replace it with the lib.py import — but specify this two-phase approach explicitly.
**Blocking:** yes

### C4: No advisor filter script exists; filter spec "tool_execution_end events only" is ambiguous
**Finding ID:** F-004
**File:** RENAME-PLAN.md §20, EXECUTION-PLAN-DRAFT.md §5c, docs/adr/0002
**Area:** correctness
**Issue:** The plan says: "Advisor exception: keep a filtered `tool-usage.jsonl` (`tool_execution_end` events only) for advisor cells." No filter script exists (`scripts/` contains only `track_run.py`). The advisor pi.jsonl files total 40GB across 153 cells (113 + 40). The plan treats filtering as trivial but doesn't specify the exact filter.

Verified against `runs/advisor-glm52-full-w4/pi-advisor-glm52/abs-module-cache-flags/rep0/pi.jsonl` (96MB):
- Total `tool_execution_end` events: 101 per file.
- Of those, only 1-6 have `toolName: "advisor"` (the ones carrying usage in `result.details.usage`).
- The other ~95-100 are bash/file tool calls with no usage data.

The current `parse_usage.py:61` keys on `t == "tool_execution_end" and ev.get("toolName") == "advisor"`. If the executor filters ALL `tool_execution_end` events (interpreting "tool_execution_end events only" literally), the filtered file is ~100x larger than needed (still includes bash outputs). If they filter only `toolName == "advisor"`, that's correct but the plan doesn't specify the predicate.

The likely-wrong default: `grep '"type":"tool_execution_end"'` (all events) → the "tiny" file is not tiny, or `jq 'select(.type=="tool_execution_end")'` → same. The executor may also miss that the advisor usage is nested in `.result.details.usage` (not `.result.usage` or top-level `.usage`), and write a filter that doesn't extract it.

**Expected behavior:** A precise filter spec: `jq -c 'select(.type == "tool_execution_end" and .toolName == "advisor")'` applied to each advisor cell's `pi.jsonl`, output to `tool-usage.jsonl` in the destination cell. The usage fields to preserve: `.result.details.usage.{inputTokens,outputTokens,cacheReadTokens,cacheWriteTokens,totalTokens,cost.total,provider,model}`.

**Why it matters:** A too-broad filter keeps bash tool outputs (defeating the "tiny" goal). A too-narrow or wrong-path filter loses advisor usage data permanently (the 40GB pi.jsonl is scheduled for deletion, and the session file has NO advisor usage — ADR-0002 confirms this). Once deleted, the data is unrecoverable.

**Suggested Fix:** Add to §20: "For each advisor cell, run: `jq -c 'select(.type == \"tool_execution_end\" and .toolName == \"advisor\")' < pi.jsonl > tool-usage.jsonl`. Verify each output is non-empty (advisor calls > 0) and contains `.result.details.usage` with non-zero `totalTokens`. The parse_usage rewrite reads this file alongside the session: `parse_usage(session_path=cell/"session"/"session.jsonl", advisor_path=cell/"tool-usage.jsonl" if (cell/"tool-usage.jsonl").exists() else None)`. Specify this must run BEFORE the 40GB pi.jsonl purge."
**Blocking:** yes

### H1: Multiple .out files per run — no resolution order for thinking backfill source
**Finding ID:** F-005
**File:** RENAME-PLAN.md §19
**Area:** correctness
**Issue:** The plan says "parse that run's batch-log `command:` header line for `--thinking`" — as if each run has ONE batch log. Verified: `runs/ponytail-full-pilot-w2/` has 4 `.out` files:
- `batch.out` — no `command:` header; starts with "running 20 cells" (10 tasks × 2 arms, a different smaller batch)
- `batch-ponyext-w8.out` — HAS `command:` header; "running 226 cells" (113 tasks × 2 arms); command has NO `--thinking` flag
- `batch-resume-w8.out` — no `command:` header; "running 226 cells" (resume of the above)
- `monitor.out` — empty

Only 1 of 4 has a `command:` header. The 249 cells in ponytail-full-pilot-w2 could have been produced by either the 20-cell batch (batch.out) or the 226-cell batch (batch-ponyext-w8.out). The plan doesn't specify which .out is authoritative, or how to pick when multiple exist.

The likely-wrong default: take the first .out alphabetically (`batch.out`) → no `command:` header → fail-loud or default silently.

**Expected behavior:** A resolution order: "Search all `runs/<run>/*.out` files for a `command:` header. If multiple exist, prefer the one whose cell count matches `find runs/<run> -name result.json | wc -l` (the complete run). If none have a `command:` header, default to `high` with audit logging."

**Why it matters:** Wrong thinking value → cells land in the wrong `results/<model>/<thinking>/` tree → invisible to model+thinking queries → analysis misses them or double-counts.

**Suggested Fix:** Add the resolution order above to §19. For ponytail-full-pilot-w2 specifically, note that `batch-ponyext-w8.out` is authoritative (226 cells matches the run's 249 cell count after accounting for the 20-cell pilot subset) and its command has no `--thinking` → default `high`.
**Blocking:** no (but must fix before migration runs)

### H2: §3 kill sequence assumes pid 454133 is alive — no fallback if batch already finished
**Finding ID:** F-006
**File:** EXECUTION-PLAN-DRAFT.md §3 step 1-2
**Area:** correctness
**Issue:** §3 step 1 says: "Get their PIDs from `pgrep -P 454133` WHILE 454133 is still alive." Step 2: "kill 454133." This assumes 454133 is alive at execution time.

Verified: 454133 IS alive now (etime 09:24:21), with 4 in-flight run.py children and 4 dsw-* containers. But the plan says "DRAFT — NOT APPROVED, DO NOT EXECUTE." By the time it's approved and executed, the Qwen batch may have finished (the 36-task subset × 2 arms = 72 cells; ~78 done means only ~4 remaining, could finish in ~1-2 hours).

If 454133 has exited: `pgrep -P 454133` returns nothing (children reparented to pid 1), step 2's `kill 454133` fails, and the orphaned run.py children + dsw containers are NOT killed. The plan's §4 freeze gate would then fail (containers still Up), but the plan doesn't say what to do — it just says "migration refuses to start." Deadlock.

**Expected behavior:** A fallback that works regardless of whether 454133 is alive.

**Why it matters:** Orphaned dsw containers continue running pi inside, which writes stale result.json to the OLD path (runs/) after migration has moved data to results/ → silent data split.

**Suggested Fix:** Replace §3 step 1-2 with: "1. If `kill -0 454133 2>/dev/null` succeeds (454133 alive): capture child PIDs via `pgrep -P 454133`, SIGTERM them, confirm exited, then `kill 454133`. 2. If `kill -0 454133` fails (already exited): find orphaned run.py children via `pgrep -f 'harness/run.py.*--run-name qwen-local-om-pilot'`, SIGTERM them directly. 3. Regardless of path: `docker rm -f` every live `dsw-*` container (the belt-and-suspenders that doesn't depend on knowing PIDs)."
**Blocking:** no (but must fix before execution)

### H3: codex54mini folds into observational-memory but orchestration.md DIFFERS
**Finding ID:** F-007
**File:** RENAME-PLAN.md §11, ADR-0001
**Area:** correctness
**Issue:** §11 says `pi-observational-memory-codex54mini` → "folds into `observational-memory` as another model leaf." But folding means the two arms share config-level constant files. Verified: their `orchestration.md` files DIFFER:
- `pi-observational-memory/orchestration.md`: "Observational memory is enabled for this run. Work normally as a competent engineer; do not change your behavior just because memory is present."
- `pi-observational-memory-codex54mini/orchestration.md`: Same text + "Memory workers use openai-codex/gpt-5.4-mini via the benchmark OAuth pass-through."

The extra sentence in codex54mini's orchestration.md is a config-level difference (it's in the orchestration prompt, not the model leaf). If codex54mini folds into observational-memory, its cells would use the shorter orchestration.md — losing the worker model note. The executor would pick one file and silently drop the other's content.

Additionally, `pi-observational-memory-codex54mini/settings.json` exists but `pi-observational-memory/settings.json` also exists — are they the same? The plan doesn't say. If they differ, folding silently changes the OM config for codex54mini cells.

**Expected behavior:** Either (a) the config-level files are identical (verified by diff) and the fold is safe, or (b) they differ and codex54mini must be a separate config, or (c) the differing content moves to the model leaf.

**Why it matters:** Different orchestration prompts → different agent behavior → the codex54mini reps are not comparable to observational-memory reps under the same config. The whole point of folding is that they ARE the same config with a different model.

**Suggested Fix:** `diff -rq arms/pi-observational-memory/ arms/pi-observational-memory-codex54mini/` and verify all config-level files match except models.json. If orchestration.md differs (it does), either move the worker-model note into a leaf-level file (e.g. `configs/observational-memory/<model-leaf>/<thinking>/orchestration-override.md`) or keep codex54mini as a separate config. The plan must specify which.
**Blocking:** no (but must resolve before §5b)

### H4: §5e smoke test uses a task that already has a result.json — would skip, not run
**Finding ID:** F-008
**File:** RENAME-PLAN.md §25, EXECUTION-PLAN-DRAFT.md §5e
**Area:** tests
**Issue:** RENAME-PLAN §25 says: "Smoke test: run one cell `--config baseline --model deepseek-v4-flash --thinking high --task adaptix-name-mapping-aliases` and confirm the rep lands at the new path and resume skips it on a second invocation."

But `adaptix-name-mapping-aliases` already has a result.json in the migrated tree (from ponytail-full-pilot-w2, which used `baseline` / `deepseek-v4-flash` / `high`). After migration, the result.json exists at `results/deepseek-v4-flash/high/baseline/adaptix-name-mapping-aliases/rep0/result.json`. So the FIRST invocation would SKIP it (resume = existence-check). The smoke test would never actually exercise the new harness code path (docker run, pi execution, session write, parse_usage). It would only test the skip logic.

The likely-wrong default: the executor runs it, sees "skip", declares success, and ships a harness that may have a broken run path (never tested).

**Expected behavior:** The smoke test runs a NEW cell (no existing result.json) to exercise the full path, THEN verifies skip on a second invocation.

**Why it matters:** A broken run path (wrong docker mount, wrong session-dir, broken parse_usage rewrite) would not be caught. The plan says "Confirm result.json carries correct usage and session/ lands" — but if the cell skips, no new result.json is written and nothing is verified.

**Suggested Fix:** Use a task NOT in the migrated tree, or use `--rep 99` to force a new rep. Acceptance criteria: (1) `result.json` exists at `results/<model-leaf>/<thinking>/<config>/<task>/rep99/result.json`, (2) `cost_usd > 0` AND `total_tokens > 0` in result.json, (3) `session/*.jsonl` exists and is non-empty, (4) second invocation with same args skips (exit 0, no new docker container).
**Blocking:** no (but must fix before resume)

### M1: Backup not a hard gate in §7 ordering; backup size claim wrong
**Finding ID:** F-009
**File:** EXECUTION-PLAN-DRAFT.md §7 (ordering), §8 (risks)
**Area:** correctness
**Issue:** §8 says "before §5c, the 1.8GB metadata backup... is written to a tarball." But §7's ordered steps have NO backup step — it goes 5a → 5b → 5c → 5d → 5e. The executor might skip the backup because it's only in §8 (risks prose), not in the ordered gate sequence.

Also, the backup size claim is wrong. Verified: `find runs -type f ! -name pi.jsonl -exec du -ch {} +` = 81M (not 1.8GB). The `du -sh --exclude='pi.jsonl' runs/` shows 2.3G but that includes directory metadata overhead from the 233GB of pi.jsonl files.

**Expected behavior:** Backup is an explicit ordered step (a gate) between §5b and §5c, with a verify command.

**Why it matters:** If migrate has a bug (e.g., the models.json fallback bug from C1), rollback requires the backup. Without it, the only fallback is the un-migrated runs/ tree — which still has the mutated arms/ files. The plan says "runs/ is not deleted until migration is verified" but doesn't say what happens to configs/ (renamed from arms/) if rollback is needed.

**Suggested Fix:** Add to §7 between steps 5 and 6: "5b.5: Create backup: `tar czf backup-pre-migrate-$(date +%Y%m%d).tar.gz --exclude='pi.jsonl' runs/ configs/ harness/ scripts/`. Verify: `tar tzf backup-*.tar.gz | wc -l` > 10000 and `du -sh backup-*.tar.gz` is ~81M (not ~233GB — if it's ~233GB, the exclude failed and you're backing up pi.jsonl). Gate: do not proceed to §5c until backup verified."
**Blocking:** no

### M2: parse_usage rewrite doesn't specify the new function signature for dual-source reading
**Finding ID:** F-010
**File:** RENAME-PLAN.md §14, docs/adr/0002
**Area:** correctness
**Issue:** The plan says parse_usage is "rewritten" to read main-agent usage from the native session (`type:"message"` records), AND additionally read the filtered `tool-usage.jsonl` for advisor usage. The current `parse_stream(*, path=None, text=None)` takes a SINGLE path. The rewrite needs to accept TWO paths (session + filtered tool-usage), but the plan doesn't specify the new signature.

`run.py:350` currently calls `parse_usage.parse_stream(path=cell / "pi.jsonl")`. The plan says to change this to read the session, but doesn't specify: (a) the new function name/signature, (b) how run.py decides whether to also pass the advisor file (auto-detect? config flag? file existence check?), (c) what happens for non-advisor configs (no filtered file exists).

The likely-wrong default: the executor writes a new function with a different name, leaves the old `parse_stream` for backward compat, and run.py calls the wrong one. Or: the executor passes the session path but forgets the advisor path, and advisor runs get zero advisor usage (the `except Exception: raw=""` removal makes this fail-loud, but the plan says to remove that fallback — so a missing advisor file would crash run.py for advisor configs).

**Expected behavior:** A specified signature and calling convention.

**Suggested Fix:** Specify: "`parse_usage(*, session_path: Path, advisor_path: Path | None = None) -> dict`. run.py always calls with `session_path=cell/"session"/"session.jsonl"`. For advisor configs, also passes `advisor_path=cell/"tool-usage.jsonl"` (checked via `(cell/"tool-usage.jsonl").exists()`). Non-advisor configs pass `advisor_path=None` and skip advisor parsing. The old `parse_stream` function is DELETED, not kept for backward compat."
**Blocking:** no

### M3: ponytail configs have no models.json; leaf content unspecified
**Finding ID:** F-011
**File:** RENAME-PLAN.md §9-10
**Area:** correctness
**Issue:** The plan says to "Materialize model leaves" with models.json content from result.json's arm_models or arms/*/models.json fallback. But arms/ponytail-full/, arms/ponytail-lite/, arms/ponytail-pi-extension/, arms/ponytail-ultra/ have NO models.json (verified: only baseline, pi-advisor-glm52, pi-observational-memory have models.json). ponytail-full-pilot-w2 cells have `arm_models: None`. So there's no source for the leaf models.json.

The plan doesn't specify what happens. The executor would either (a) create an empty models.json, (b) error, or (c) skip the leaf. None specified.

**Expected behavior:** Configs without a models.json at the arm level never had one — they use pi's default built-in provider config. The leaf dir is created (for the thinking axis) but contains no models.json.

**Suggested Fix:** Add to §10: "If neither `arm_models` in result.json nor `arms/<config>/models.json` exists (e.g. ponytail-* configs), create the leaf directory but do NOT create a models.json file. These configs use pi's default provider config. Log to migrate-models-audit.jsonl: source='no_models_json_config_uses_pi_default'."
**Blocking:** no

## What's Good
- The collision detection policy (§19) is well-specified with concrete examples and resolution rules for both known collisions.
- The freeze gate (§4) with three independent checks (processes, containers, file writes) is sound.
- The "result.json as source of truth, never arms/*/models.json" principle is correct in intent — the execution gap is in the fallback path, not the principle.
- The `--dry-run` mandate for migrate is the right safety pattern.
- The silent-zero fallback removal in parse_usage (§14) is correctly identified as a corruption vector.
- The kill-before-freeze-before-migrate-before-resume ordering principle is correct — the specific PID-dependent implementation is the gap.
