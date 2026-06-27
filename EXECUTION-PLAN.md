# Execution Plan: Rename + Migrate + Resume (qwen stopped)

**Status: FINAL — operator-approved 2026-06-27. Ready to execute.**
**Author: main agent (which has made multiple errors this session — every
load-bearing claim below is verified against the live repo).**
**Review history folded in (3 adversarial rounds, operator + subagents):**
(1) parse_usage native-session rewrite split out as RENAME-PLAN Phase 0.5 —
lands standalone, smoke-tested on one cell with a parity gate, BEFORE the
mechanical rename; (2) `baseline` vs `baseline-wf` confirmed as a real
comparison target, not a rename artifact; (3) comparison/subset view
abstraction approved for build; (4) general rep-accumulation rule added to
RENAME-PLAN §19 so future subset-expansion resumes don't re-run migrated cells;
(5) reviewer criticals #1 (settings.json worker-model leaf placement) and #2
(arm_models-absent fallback provider check) both closed.

This plan **executes the vocabulary/directory rename now**, migrates all result
data to the new tree, then resumes the qwen batch (stopped mid-run per operator
decision) and the deferred codex-spark run in the new CLI framework. The
operator's pending deepseek 4-run (Q-D) slots in AFTER the rename, in the new
layout.

**Strategy (operator decision, final):** the qwen batch was **stopped at
107/226** per operator decision (§3 documents the kill performed 2026-06-27) —
it is NOT being waited on. Both gpt-5.5 runs and `codex-spark-baseline-sub`
finished naturally earlier. `codex-spark-baseline-w2` (the original full-set
codex-spark run, genuinely paused at 45/113) migrates while paused and resumes
only when the operator chooses, in the new framework. **The freeze is already
achieved** — no live writers remain, so migration (§5) can proceed immediately
after the parse_usage standalone (Phase 0.5) lands.

Two companion docs define the *what* and *why*; this plan is the *how* and
*when*:
- `RENAME-PLAN.md` — the rename phases and target tree.
- `docs/adr/0001-directory-and-vocabulary-reorganization.md`
- `docs/adr/0002-retire-pi-jsonl-stream-capture.md`
- `CONTEXT.md`, `AGENTS.md` — vocabulary + usage-capture rules.

---

## 0. Execution gates (verify against the live repo before each step)

**This plan is execution sequencing ONLY (freeze-verify → migrate → resume).
It does NOT re-decide anything.** The *what* and *why* are settled in the
companion docs; the checks below confirm this plan is *consistent* with them,
not re-litigate them:
- `CONTEXT.md` — canonical vocabulary (config/model/thinking/task/rep/subset/
  comparison/baseline). No `arm`/`study`/`cell`.
- `RENAME-PLAN.md` — the rename phases, target tree, CLI changes, and the
  `arm→config` name map (§11). Phase 3 = code, Phase 4 = migration.
- `docs/adr/0001-directory-and-vocabulary-reorganization.md`
- `docs/adr/0002-retire-pi-jsonl-stream-capture.md`
- `AGENTS.md` — usage-capture rules (native session default; advisor exception;
  OM worker gap).

Reviewers verify, against the live repo:
1. §1 run-state claims (re-derive with §A — the qwen kill was performed
   2026-06-27; counts are now static, but re-confirm no writers revived).
2. §3 freeze is real: zero `run_batch.py`/`run.py`/`dsw-*`/sidecars, and no
   writes to `runs/` for >2 min. (The freeze was achieved by the §3 kill, not
   by waiting.)
3. §5 migration preserves `result.json` for every completed cell and the §6
   resume commands point at locations that exist post-migration.
4. §7 ordering has no step editing a file a live process reads (freeze holds
   through the rename block).
5. **RENAME-PLAN Phase 0.5 parse_usage parity gate is real:** the new
   native-session parser, run on a cell that has BOTH `pi.jsonl` AND
   `session/*.jsonl`, reproduces the old `{total_tokens, cost_usd, turns}`
   within tolerance. This is the proof the rewrite did not silently zero the
   cost column. If parity fails, the rename (Phase 1+) must not proceed.
6. **Both ADR-0001 mutation-bug paths are closed (reviewer criticals #1 #2):**
   (a) `settings.json` that carries a worker MODEL identity lands in the model
   leaf, not config-level — verify the two `observational-memory` arms' leaves
   (`Qwen` and `gpt-5.4-mini`) keep DISTINCT worker models after migration
   (RENAME-PLAN §9/§10/§11). (b) the `arm_models`-absent fallback does NOT
   trust the mutated `arms/baseline/models.json` — verify the codex-spark
   leaves materialize path-only with no `models.json` when the fallback file's
   provider disagrees with the cell's model (RENAME-PLAN §10). Both are the
   exact mutation class ADR-0001 prevents.

All items are RESOLVED. The operator approved the plan 2026-06-27 after the
qwen stop; the checks above are now execution gates, not approval gates.

---

## 1. Current run inventory (as of plan authoring)

Gathered from `ps`, `docker ps`, `find runs -name result.json`, and batch-log
headers. **Reviewers must re-derive with §A** — counts climb in real time.

### 1a. STOPPED run (was live — killed per operator decision 2026-06-27)

| Run | Model | Thinking | Process | Target | Done | Reset |
|---|---|---|---|---|---|---|
| `qwen-local-om-pilot` | `local-vllm/cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4` | high | pid `3985691` (DEAD) | 226 (113×2) | **107** | STOPPED mid-run |

PIDs and counts are now **static** — qwen was killed 2026-06-27 (§3). The
`454133` cited in earlier drafts was already dead (qwen had restarted); the
actual killed PID was `3985691` (verified live at kill time).

**qwen was the sole live writer and is now STOPPED at 107/226** (operator
decision). The kill was data-safe: the 4 in-flight cells left NO `result.json`,
so they re-run cleanly on resume (no data loss). **qwen resumes post-migration
in the new CLI framework** (§6). Its ORIGINAL CLI (old form — recorded for
resume reconstruction):
```
# qwen (no --subsample → runs all 113 tasks, 226 cells)
python3 harness/run_batch.py --arms baseline,pi-observational-memory \
  --run-name qwen-local-om-pilot \
  --model local-vllm/cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4 --thinking high \
  --runs 1 --workers 4
```

**Concurrency:** qwen's 4 workers are local-vllm (your hardware; 4 = sweet
spot, 8 = slow). The codex-spark / gpt-5.5 runs hit the remote Codex/OpenAI API
on **separate subscriptions** — disjoint resource pools, zero contention with
qwen.

Sidecars that WERE tied to qwen (now killed in §3):
- pid `3814326` — `runs/qwen-local-om-pilot/emit-progress.py` (KILLED).
- pid `3988336` — `track_run.py qwen-local-om-pilot --expected 226` (KILLED).

Note on qwen: earlier drafts called this "72-cell subset" via `--subsample
fast-iter-v1`. The LIVE cli has NO `--subsample`, so it runs all 113 tasks
(226 cells). §6 qwen resume must NOT add `--subset` or it would under-run.

### 1b. PAUSED runs (process exited cleanly with code 75)

| Run | Model | Thinking | Arm | Cells | Reset |
|---|---|---|---|---|---|
| `codex-spark-baseline-w2` | `openai-codex/gpt-5.3-codex-spark` | high | `baseline` | 45/113 | ~4 days |

**`codex-spark-baseline-w2` is the sole paused run.** It is the original
full-set (113-task) codex-spark run, started *before* the `fast-iter-v1` subset
existed. codex-spark hit its subscription limit so aggressively that the full
run would take forever; the 36-task subset (`codex-spark-baseline-sub`, now
done — §1c) was created specifically to get usable results faster.

**Operator decision: keep `codex-spark-baseline-w2` permanently paused for
now.** Its 45 existing cells migrate with the DONE runs (§1c/§5). The run is
NOT resumed until the operator chooses — and that resume happens in the NEW
directory framework, after migration (§6), not before.

Its CLI (recovered from batch-log header `running 113 cells … workers=2` +
`result.json` model/thinking): full 113 tasks (no `--subsample`), arm
`baseline`, `--workers 2`, `--thinking high`, `--pass-openai-codex-oauth`
required (`run.py:230-231` silent `sys.exit` for openai-codex without it).

### 1c. DONE/STOPPED runs (no live process; data only — safe to migrate)

Migrate: `qwen-local-om-pilot` (107, stopped mid-run — §3; resumes post-
migration §6), `advisor-glm52-full-w4` (113), `advisor-glm52-reliability-rerun`
(40), `codex55-medium-om54mini-w2` (113), `om-memory-pilot-w10` (113),
`ponytail-full-pilot-w2` (249), `ds4flash-high-wf-sub` (36),
`codex55-medium-baseline-sub` (108, finished during authoring),
`codex55-medium-wf-sub` (108, finished during authoring),
`codex-spark-baseline-sub` (36, finished during authoring), plus the 45 existing
cells of paused `codex-spark-baseline-w2` (NOT resumed — §1b/§6).

**Hidden-runs note (operator + historical-memory agent review):** the current
`runs/<free-text-name>/<arm>/<task>/rep<N>/` layout actively hides finished
work. During review the historical-memory agent could not recall
`codex55-medium-baseline-sub` (108 cells, GPT-5.5 no-OM control),
`codex55-medium-wf-sub` (108 cells, GPT-5.5 + workflow prompt), or
`ds4flash-high-wf-sub` (36 cells, DeepSeek + workflow prompt) without `find`-ing
the tree and reading `result.json` headers — 324 result cells across 3 runs
were effectively invisible. The rename (model+thinking+config in the path) is
the fix: `results/gpt-5.5/medium/baseline/` is self-describing. **Two of these
runs are the first reps of configs that matter for open analyses:**
- `codex55-medium-baseline-sub` (arm=`baseline-codex`) is the **GPT-5.5 no-OM
  control** that isolates the OM contribution in `codex55-medium-om54mini-w2`
  (which changed two variables at once: model upgrade + OM). It already exists
  and must not be lost in migration.
- `codex55-medium-wf-sub` and `ds4flash-high-wf-sub` (arm=`baseline-codex-wf`)
  are the first reps of the **`baseline` vs `baseline-wf` comparison** the
  operator confirmed as a real target (RENAME-PLAN §11/Q5). The DeepSeek leg
  pairs with the reused `baseline` cells from `ponytail-full-pilot-w2`.
The comparison/subset view abstraction (RENAME-PLAN target tree,
`results/<model>/<thinking>/comparisons/<name>/`) is what surfaces these
automatically; building it is approved (operator decision).

**Collision note (codex-spark):** `codex-spark-baseline-sub` (arm=`baseline-codex`)
and `codex-spark-baseline-w2` (arm=`baseline`) both fold to config `baseline` at
`gpt-5.3-codex-spark/high/` and share 18 `(task, rep0)` pairs (sub has 36 cells
but only 18 are tasks w2 reached). Migration resolves it by renumbering all 36
sub cells to `rep1` (keeping w2's 45 cells at `rep0`); see RENAME-PLAN §19.

**Excluded from migration** (pre-pilot smoke-test throwaways): `diag`,
`validate`, `validate-fixed`. They are 4 cells total. Excluding them resolves a
real collision: all three hold `(deepseek-v4-flash, baseline,
adaptix-name-mapping-aliases, rep0)` where `ponytail-full-pilot-w2`'s real cell
is `reward_partial=0.998` and the throwaways are `0.0` — migrating the
throwaways would overwrite the real cell. (See RENAME-PLAN §19.)

Also excluded (aborted, 0 `result.json`, would otherwise trip the "uncovered
collision → fail loud" path): `codex54mini-high-wf-sub`,
`codex54mini-xhigh-wf-sub`, `ponytail-full-pilot` (distinct from the real
`ponytail-full-pilot-w2`).

### 1d. Watcher processes

**All watcher/sidecar processes are now DEAD** (killed during authoring:
qwen's `emit-progress.py` + `track_run.py` in the §3 stop; the codex55/
codex-spark watchers were already gone once those batches finished). Confirmed:
`pgrep -af 'track_run|emit-progress'` returns nothing. The PIDs in earlier
drafts (`1800722`, `2034975`, `2034977`, `3164342`, …) are all stale.

`track_run.py`'s `done:` line must NOT be used as a go/no-go signal — it
counts `result.json` files on disk, not process exit, and produced a false
`done: 72/72` earlier this session. §3 freeze verification is the only signal.

---

## 2. The core safety constraint (must hold for every step)

> **`run.py` re-reads `arms/<config>/` and `harness/*.py` on every cell, and
> `run_batch.py` shells out to `run.py` per cell.** Therefore no file under
> `harness/` or `arms/` may be edited, renamed, or moved while any
> `run_batch.py` or `run.py` process is alive. Editing mid-batch silently
> corrupts the next cell.

Additionally: **killing `run.py` does not stop its docker container** —
`run.py` starts the container with `docker run -d ... sleep <timeout+600>` and
only removes it in a `finally` block. A SIGKILL'd `run.py` orphans the
container, which keeps running `pi` inside and will write `result.json` to the
*old* path if it finishes. So any freeze is not complete until **all `dsw-*`
containers are `docker rm -f`'d**, not just when the python processes die.

**Freeze status (FINAL plan):** the no-edit freeze on `harness/`, `arms/`,
and (for the migrate read) `runs/` is **already in effect** — qwen was stopped
2026-06-27 (§3) and all other batches finished earlier, so no `run_batch.py`/
`run.py`/`dsw-*` process is alive. `run.py`'s per-cell re-read (`run.py:124,128,
136,225,277-281,353-359` re-read `arms/`+`harness/`) is exactly why the qwen
stop was mandatory before any edit: with qwen still running, editing `arms/`
mid-batch would corrupt the next cell. The freeze holds through the entire
rename block (§5) and lifts only for resume (§6).

This is why §3 (freeze verify) precedes §5 (migrate) precedes §6 (resume).

---

## 3. Freeze achieved (qwen stopped 2026-06-27)

**The qwen batch was stopped mid-run per operator decision.** Earlier drafts
waited for qwen to finish naturally; the operator instead chose to stop it,
migrate + refactor, then resume it in the new framework (§6). The stop was
performed 2026-06-27 and is now historical fact — this section records it.

**Kill sequence executed (data-safe order):**
1. `SIGKILL` the batch process `3985691` AND its 4 in-flight `run.py` children
   (`612971 625152 718084 736419`) in one shot — BEFORE any `result.json`
   write, so the 4 in-flight cells left no partial record (they re-run cleanly
   on resume; no data loss).
2. `docker rm -f` the 4 `dsw-*` containers (orphaned `pi` processes inside).
3. Killed sidecars `emit-progress.py` (`3814326`) + `track_run.py` (`3988336`).
4. Pruned 5 stale `Exited` codex-wf containers (18h old, from the finished
   gpt-5.5 run).

**Verified post-kill state (this IS the freeze):**
- `pgrep -af 'run_batch.py|harness/run.py'` → none.
- `docker ps -a --filter name=dsw-` → none.
- `pgrep -af 'emit-progress|track_run'` → none.
- qwen `result.json` count = **107/226** (107 intact; the 4 killed in-flight
  cells had no result.json and re-run on resume).
- disk: 258G free (no ENOSPC pressure; no watchdog needed — nothing is writing).

**The earlier wait/watchdog/kill-fallback subsections are removed.** There is
no wait (qwen is stopped), no watchdog (nothing is writing), and the
kill-fallback was promoted to the primary action and already executed. §4
verifies the freeze still holds immediately before migration.

**Guard (defense in depth):** if a writer somehow revives before §5 (operator
starts a batch, a stray container restarts), re-run the §3 verification; if
non-empty, stop it with the same scoped sequence before proceeding. Migration
must never run against a live writer — `result.json` is written non-atomically
(`run.py:381`, no temp+rename), so a concurrent read can hit a truncated file.

---

## 4. Freeze verification (gate — must pass before §5)

This was already verified at the §3 stop (2026-06-27); re-run it immediately
before §5 to confirm nothing revived. Zero output from all of:
- `pgrep -af "run_batch.py|harness/run.py|emit-progress|track_run.py"`
- `docker ps --filter "name=dsw-" --format '{{.Names}}'`
- `find runs -newermt "-2 min" -type f` (no writes for 2 min)

**No per-run `done == target` check applies** — qwen is deliberately partial
(107/226, resumes post-migration per §6), not "done". The freeze gate is
purely "no live writers", not "all runs complete". (The earlier `done==target`
condition was for the wait-for-completion strategy, now superseded.) Only
after this passes does §5 begin.

---

## 5. Migration (executes the approved RENAME-PLAN)

This section is a *summary*; the authoritative steps are in `RENAME-PLAN.md`
phases. Reviewers should check this summary against that doc for consistency.

5a. **Commit docs first** (already-written, uncommitted): `CONTEXT.md`,
`AGENTS.md`, `RENAME-PLAN.md`, `docs/adr/0001`, `docs/adr/0002`. Add only these
files — leave unrelated `.pi/skills/*` changes out of this commit.

5b. **Rename `arms/` → `configs/`** with config-constant files at the top level
and model+thinking leaf dirs (`configs/<config>/<model-leaf>/<thinking>/`).
Split the mutable `models.json`/`advisor.json` into the leaf so
model+thinking becomes a first-class axis (fixes the resume-mutation bug from
ADR-0001).

5c. **Write+run `scripts/migrate_results.py`** per RENAME-PLAN Phase 4 §19
(the authoritative spec; this is a summary):
- **Run `--dry-run` first.** It reports every destination tuple, every
  collision, and every thinking-backfill inference, and writes nothing. Approve
  before the real move.
- For each surviving `result.json`, derive `(config, model-leaf, thinking)`
  via the SHARED `lib.model_leaf()` (executor-only; same function the new
  `run.py`/`run_batch.py` use — so resume paths cannot diverge from migrate
  paths). **Walker uses `os.walk(followlinks=False)`** to avoid double-counting
  the 3 symlinked `baseline/` dirs; dedup by `realpath` if in doubt.
- **`--runs <list>` scoping (optional optimization):** the walker accepts a
  `--runs` flag bounding `os.walk` to the named run roots. **Not needed under
  the FINAL plan** — the freeze is total (§3 stop), so the walker traverses all
  of `runs/` safely in one pass. The flag remains available for future partial
  migrations; if ever used against a non-frozen tree, each `result.json` read
  must be wrapped in `try/except json.JSONDecodeError → skip+log` (the file is
  written non-atomically, `run.py:381`).
- **Excluded runs:** `diag`, `validate`, `validate-fixed` (throwaways), plus
  the empty `codex54mini-high-wf-sub`, `codex54mini-xhigh-wf-sub`,
  `ponytail-full-pilot` (see RENAME-PLAN §19).
- **In-file rewrite (from RENAME-PLAN §19):** rename each cell's in-file `arm`
  -> `config` via the §11 map; set in-file `rep` to N on renumbered cells.
  Post-migrate assertion: `rec["rep"]==N` and `rec` has `config` matching the
  path segment (analyze.py:114 keys on in-file `(task,rep,arm)`, so the move
  alone is insufficient).
- **`thinking_level` backfill:** ~249 older cells lack the field (all
  `ponytail-full-pilot-w2`, after excluding the diag/validate throwaways). Use
  `DEFAULT_THINKING` (`high`) unconditionally; log every imputation to
  `migrate-thinking-audit.jsonl`. NEVER fail-loud on missing thinking_level.
  **The 249 count is a snapshot — recompute at migration time** (per RENAME-PLAN
  §19); a material divergence signals dedup failure or a new non-recording run
  and must be investigated, not silently backfilled.
- **Collisions (resolved by policy in RENAME-PLAN §19):**
  - `advisor-glm52-reliability-rerun` (40 cells) → renumbered to `rep1` under
    `deepseek-v4-flash/high/advisor/` (executor-only leaf; genuine extra reps,
    not duplicates of `advisor-glm52-full-w4`).
  - `codex-spark-baseline-sub` (36 cells) → renumbered to `rep1` under
    `gpt-5.3-codex-spark/high/baseline/` (keeps `codex-spark-baseline-w2`'s 45
    cells at `rep0`; only 18 of the 36 are tasks w2 reached, but all 36 are
    renumbered for uniformity so sub and w2 stay separate rep cohorts).
- **Do not move `pi.jsonl`** (233GB, retired by ADR-0002). Move `result.json`,
  `verifier/`, `artifacts/`, `logs/`, and native `session/`.
- **Advisor exception:** for advisor cells keep a filtered `tool-usage.jsonl`
  using `jq -c 'select(.type=="tool_execution_end" and .toolName=="advisor")'`
  (scope: `arm=pi-advisor-glm52` only); advisor LLM usage is absent from the
  session. Optional if old cells' `result.json` already carry
  `advisor_cost_usd`/`advisor_total_tokens` (the §14 run-time capture is the
  real fix going forward).

This section's prior claim that "`thinking_level` is in `result.json` (lib.py
writes it) — no guessing from logs" was WRONG and has been removed. See
RENAME-PLAN §19 for the corrected provenance.

5d. **Edit harness** per RENAME-PLAN Phase 3: `run.py`/`run_batch.py` use
`--config` (was `--arm`), output root `results/<model-leaf>/<thinking>/<config>/...`,
load config from `configs/<config>/`. **parse_usage native-session rewrite is
already landed in Phase 0.5 / step 4 of §7** (standalone, pre-rename, with its
own parity gate); §5d here only removes residual `pi.jsonl` path references from
`run.py` and is CLI/path-only on the parser side. Advisor's filtered-file
exception is per ADR-0002 + AGENTS.md.

5e. **Smoke-test one cell** on the new harness against a fast task before any
resume. Pick a task present in NO migrated run — `adaptix-name-mapping-aliases`
is in 5 old runs (validate/diag/validate-fixed×2/ponytail-full-pilot-w2) and a
resume would SKIP it, testing nothing. Machine-checkable acceptance: (a)
`result.json` lands at the exact `results/<model-leaf>/<thinking>/<config>/<task>/
rep0/` path; (b) `cost_usd > 0` AND `total_tokens > 0`; (c) `session/*.jsonl`
has >=1 `type:"message"` record; (d) NO `pi.jsonl` is created; (e) a second
`run_batch.py` invocation logs `skip`. All five must pass before §6 resume.

The `(arm→config)` name map is settled in **RENAME-PLAN §11** (all 10 `arms/`
dirs covered, including baseline, ponytail-full, ponytail-lite,
ponytail-extension, ponytail-ultra).

---

## 6. Resume commands (post-migration, new CLI)

**qwen is the PRIMARY post-migration resume target** (stopped at 107/226 per
§3). Its 107 completed cells migrate under §5; the remaining ~119 cells
(226−107; the 4 in-flight killed cells re-run from scratch) run under the new
CLI. `codex-spark-baseline-w2` is a SECONDARY, operator-deferred resume.

Resume mechanic: re-run with `--arm`→`--config`, `--run-name` removed (path now
derived from model/thinking/config), output under `results/`. `run_batch.py`
skips cells with existing `result.json`, so migrated cells are preserved and
only missing cells run.

- **`qwen-local-om-pilot` (primary resume):** full 113 tasks (no `--subset`,
  or `--subset 113_v0.txt`), `--configs baseline,observational-memory`,
  `--thinking high`, `--runs 1`, `--workers 4`, executor model
  `local-vllm/cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4`. **The OM config's worker
  model (in the leaf `settings.json`) must match the original Qwen worker** —
  Critical #1 (§9/§10 RENAME-PLAN) ensures the migrated OM leaf keeps Qwen, not
  the codex54mini worker. No `--pass-openai-codex-oauth` (local-vllm, not
  openai-codex). Expected: ~119 cells run, 107 skipped.
  ```
  python3 harness/run_batch.py --configs baseline,observational-memory \
    --model local-vllm/cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4 --thinking high \
    --runs 1 --workers 4
  ```
- **`codex-spark-baseline-w2` (secondary, operator-deferred):** full 113 tasks
  (no `--subset`), `--workers 2`, `--thinking high`, `--config baseline`,
  `--model openai-codex/gpt-5.3-codex-spark`, `--pass-openai-codex-oauth`
  required (`run.py:230-231` silent `sys.exit` without it). Runs only when the
  operator chooses; its 45 migrated cells are skipped, remaining 68 run. CLI
  recovered from batch-log header + result.json (Q-A RESOLVED).

For provenance, the finished runs' original CLIs (NOT resumed):
```
codex55-medium-baseline-sub: --arms baseline-codex --subsample fast-iter-v1 \
  --model openai-codex/gpt-5.5 --thinking medium --runs 3 --workers 8 --pass-openai-codex-oauth
codex55-medium-wf-sub: --arms baseline-codex-wf --subsample fast-iter-v1 \
  --model openai-codex/gpt-5.5 --thinking medium --runs 3 --workers 8 --pass-openai-codex-oauth
codex-spark-baseline-sub: --arms baseline-codex --subsample fast-iter-v1 \
  --model openai-codex/gpt-5.3-codex-spark --thinking high --runs 1 --workers 2 --pass-openai-codex-oauth
```

**Critical:** resume must run *after* migration so the new path holds the
migrated `result.json` files; otherwise the new CLI sees no results and re-runs
everything. **Sanity check before qwen resume:** confirm
`find results/Qwen3.6-27B-AWQ-BF16-INT4/high -name result.json | wc -l` == 107
(the migrated count); if 0, migration failed and resume would re-run all 226.

---

## 7. Ordering (strict — each gate must pass before the next)

1. **Plan approved by operator.** ✅ DONE 2026-06-27 (qwen stopped, plan
   finalized). ← The execution steps below are next.
2. **§3 freeze** — qwen stopped 2026-06-27 (the wait strategy is retired; the
   kill was the primary action). **Already executed and verified** (§3).
3. §4 freeze verify (gate; re-confirm no writers revived). No `done==target`
   check — qwen is deliberately partial.
4. **§5.0 parse_usage standalone (RENAME-PLAN Phase 0.5) — lands BEFORE the
   rename, as its own change.** Once §4 passes, no live process reads
   `harness/`, so editing `parse_usage.py` + the `pi.jsonl` write/read lines in
   `run.py` is safe. Land the native-session rewrite, run the Phase 0.5 parity
   gate (new parser on a real cell with both `pi.jsonl` AND `session/*.jsonl`,
   assert `{total_tokens, cost_usd, turns}` match within tolerance), and
   commit. This is independently revertable (`git revert`) without touching the
   directory layout. **The rename does NOT proceed until parity passes** — a
   parse_usage bug discovered after the tree move is far harder to localize.
5. §5a commit docs.
6. **§5.5 add `model_leaf()` to `harness/lib.py`** — this MUST precede migrate
   (§5c), which imports it. Safe to edit once §4 passes (no live reader).
   (Split from §5d to break the circular dependency where migrate uses
   `model_leaf` before it exists.)
7. §5b rename configs.
8. §5c migrate results.
9. §5d edit the rest of harness (`run.py`/`run_batch.py`/`analyze.py`) —
   parse_usage is already settled by step 4, so this is CLI/path only.
10. §5e smoke-test one cell (gate).
11. **§5.6 metadata backup gate (pre-resume):** `tar czf backup.tar.gz
    --exclude='*/pi.jsonl' -C . runs arms harness`. Verified size is ~94MB
    (non-`pi.jsonl` data), NOT 1.8GB — do not include `pi.jsonl` or the tarball
    becomes 233GB. Rollback post-§5d = `git checkout harness/` + restore the
    tarball to `results/`. (The old `runs/` tree is NOT a fallback after §5d,
    because the new harness reads `results/`, not `runs/`.)
12. **§6 resume `qwen-local-om-pilot` (primary):** the new CLI (§6) runs the
    ~119 missing cells under `results/Qwen3.6-27B-AWQ-BF16-INT4/high/`, skipping
    the 107 migrated. Sanity-check the migrated count == 107 first. This is the
    direct continuation of the stopped batch.
13. **§6 resume `codex-spark-baseline-w2` (secondary, operator-deferred):**
    runs only when the operator chooses, in the new `results/` tree.
    (`--pass-openai-codex-oauth` required: `run.py:230-231` silent `sys.exit`
    without it.) CLI recovered — Q-A RESOLVED.
14. **Q-D deepseek 4-run (AFTER rename — operator decision):** create the 4
    configs (`baseline`, `baseline-wf`, `observational-memory` with deepseek
    worker, new `observational-memory-wf`) directly in the new `configs/` layout
    and run 432 cells (36-task `36_v1.txt` × 3 reps × 4 configs) with the new
    `--config`/`--subset` CLI. No migration needed for these — they are born in
    the new tree.

Steps 4–11 are the rename proper and must complete atomically before any
resume. Step 4 (parse_usage) is deliberately outside that atomic block so it
can be validated and reverted independently. Step 12 (qwen resume) is the
operator's continuation of the stopped batch; step 14 (deepseek) is a separate
later campaign.

---

## 8. Risks and rollback

- **Risk:** a writer revives after the §3 stop and migration runs against a
  live writer (non-atomic `result.json` write → truncated-file read).
  **Mitigation:** §4 re-verifies the freeze immediately before §5; §3 documents
  the scoped re-stop if non-empty.
- **Risk:** qwen resume's new CLI derives the wrong path, so the 107 migrated
  cells are not found and all 226 re-run. **Mitigation:** §6 sanity-checks
  `find results/Qwen3.6-27B-AWQ-BF16-INT4/high -name result.json | wc -l` == 107
  before resume; the shared `lib.model_leaf()` (§5.5, step 6) is imported by
  both migrate and run.py so paths cannot diverge.
- **Risk:** qwen's resumed OM config picks up the wrong worker model (the
  mutation bug, ADR-0001). **Mitigation:** reviewer critical #1 (RENAME-PLAN
  §9/§10) — `settings.json` worker model lands in the LEAF, so the migrated OM
  leaf keeps Qwen, distinct from the codex54mini leaf.
- **Risk:** `thinking_level` missing in old `result.json` → wrong migration
  target. **Status: confirmed real, not speculative.** 253 cells lack the field
  (ponytail 249, diag 1, validate 1, validate-fixed 2). **Mitigation:** migrate
  uses `DEFAULT_THINKING` (`high`) unconditionally with per-cell audit logging
  (RENAME-PLAN §19) — it does NOT fail-loud. The 253/249 count is an authoring
  snapshot; migration recomputes it and investigates any material divergence
  (dedup failure / new non-recording run) before backfilling. The prior plan
  text claiming the field was "verified present" in all cells was wrong.
- **Risk:** w2's resumed `--subset`/workers differ from original, changing which
  cells run. **Status: resolved** — w2's full CLI is recovered (§6/Q-A); no
  `[UNVERIFIED]` flags remain.
- **Rollback:** the pre-resume metadata backup is a **hard §7 gate** (step 10),
  not just prose here. It is `tar czf backup.tar.gz --exclude='*/pi.jsonl'
  -C . runs arms harness` (~94MB; the earlier "1.8GB" figure was wrong — verified
  non-`pi.jsonl` data is ~94MB). If migration corrupts, rollback is
  `git checkout harness/` + restore the tarball to `results/`. `runs/` (with
  `pi.jsonl`) is NOT deleted until migration is verified, but note: once the
  harness is edited (§5d) the NEW harness reads `results/`, not `runs/`, so
  `runs/` is an archival fallback only — active resume needs `results/`.

---

## A. Inventory commands (for reviewers to re-derive §1)

```sh
# live processes
ps -eo pid,ppid,etime,cmd | grep -iE "run_batch|run\.py|emit-progress|track_run" | grep -v grep
# live containers
docker ps --filter "name=dsw-" --format '{{.Names}}\t{{.Status}}'
# per-run cell counts + model + thinking
for d in runs/*/; do r=$(basename "$d"); n=$(find "$d" -name result.json|wc -l);
  m=$(find "$d" -name result.json|head -1|xargs grep -oE '"model"[^,]*'|head -1);
  t=$(find "$d" -name result.json|head -1|xargs grep -oE '"thinking_level"[^,]*'|head -1);
  echo "$r: $n cells $m $t"; done
# paused markers (the [pause] line is the quota-pause signal)
grep -l "\[pause\]" runs/*/*.out 2>/dev/null
# true completion (per run): see is_batch_done in §3.1
```

---

## Open questions (all RESOLVED — recorded for provenance)

All questions are settled. The plan is FINAL (operator-approved 2026-06-27).

Q-A. **RESOLVED** — both codex-spark CLIs recovered from batch-log headers +
`result.json` (no `--subsample` originally; sub ran the 36-task `fast-iter-v1`
subset, w2 is the full 113). Recorded in §1b (w2) and §6 (sub, provenance).

Q-B. **RESOLVED** — RENAME-PLAN §11 now maps all 10 `arms/` dirs. The 5 that
were unmapped: `baseline` stays `baseline`; `ponytail-full`, `ponytail-lite`,
and `ponytail-ultra` stay verbatim; `ponytail-pi-extension` → `ponytail-extension`
(drops the redundant `pi-` segment).

Q-D. **RESOLVED (operator decision, 2026-06-27): run AFTER the rename —
option (b).** The 4 deepseek configs (`baseline`, `baseline-wf`,
`observational-memory` with a deepseek worker model, new `observational-memory-wf`)
are created directly in the new `configs/` layout and run 432 cells (36-task
`36_v1.txt` × 3 reps × 4 configs) with the new `--config`/`--subset` CLI. No
migration needed for these — they are born in the new tree. Sequenced as §7
step 14, after the qwen resume. (Option (a), running before rename, was
rejected: it would delay the rename and force the two new arms into the old
`arms/` layout only to migrate them again.)

Q-C. **RESOLVED — the 4 in-flight qwen cells are NOT lost; they re-run on
resume.** Under the FINAL strategy (qwen stopped, not waited on), the 4 cells
killed mid-run left no `result.json`, so the post-migration resume (§6 step 12)
re-runs them cleanly. No data loss — only recompute cost. (This supersedes the
earlier wait-for-completion framing where Q-C was withdrawn.)

**CORRECTION to prior plan text:** the claim that `thinking_level` is "NOT an
open question — it IS there (lib.py `result_record` writes it; verified)" was
FALSE. `thinking_level` is passed as a kwarg from `run.py` (not written by
`lib.py`), and 253 older cells lack it entirely. This is now handled by the
backfill policy in RENAME-PLAN §19, not by asserting the field is always
present. Verified against all 962 `result.json` as of plan authoring: exactly
253 lack the field. (qwen is now stopped, so this count is static.)
