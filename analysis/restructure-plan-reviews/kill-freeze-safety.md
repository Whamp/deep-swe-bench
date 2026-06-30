# Adversarial Review — Kill/Freeze Safety

**Reviewed:** EXECUTION-PLAN-DRAFT.md §3 (kill) / §4 (freeze gate) / §5 (migrate), against live harness state + `harness/run.py`, `harness/run_batch.py`, `runs/qwen-local-om-pilot/emit-progress.py`, `runs/qwen-local-om-pilot/watch-and-full-w4.sh`, `scripts/track_run.py`, `harness/analyze.py`.
**Verdict:** Request changes — the kill sequence as written does NOT stop the 4 in-flight `run.py` children, and the freeze gate has a timing hole that lets stale `result.json` pass through to migration.

## Summary

The plan's core safety claim (§2) is correct in spirit: `run.py` re-reads `arms/` + `harness/*.py` per cell, and a SIGKILL'd `run.py` orphans its `docker run -d` container. But the kill sequence (§3 step 2) looks up the run.py children with `pgrep -P 454133` **after** killing 454133 — at which point the children are reparented to pid 1 and `pgrep -P` returns empty. The 4 run.py children survive, get their containers `rm -f`'d out from under them, fall through `sh()`'s silent error-swallowing, and write a **degenerate `result.json` (patch_bytes=0, verifier skipped)** to the OLD path. The §4 freeze gate's `pgrep` catches them *if checked immediately*, but a surviving child can linger ~95 min in the verifier stage and then exit — after which the gate passes with a stale `result.json` on disk that migration moves and resume silently skips.

## Findings

### CRITICAL: §3 step 2 `pgrep -P 454133` is a no-op after step 1 kills 454133 — the 4 run.py children survive and write stale result.json
**Finding ID:** F-001
**File:** `EXECUTION-PLAN-DRAFT.md` §3 steps 1–2; `harness/run_batch.py` (no signal handler); `harness/run.py:56` (`sh()`), `:381` (result.json write)
**Area:** correctness / data integrity
**Issue:**
`run_batch.py` installs **no signal handler** (`grep signal harness/run_batch.py` → nothing; Python default SIGTERM disposition = `SIG_DFL` = 0, confirmed via `signal.getsignal(SIGTERM)`). SIGTERM kills it immediately without running the `with ThreadPoolExecutor` `__exit__` (`shutdown(wait=True)`). The 4 in-flight `run.py` children — PIDs `3206793, 3210907, 3236648, 3239788` (confirmed `pgrep -P 454133` right now) — are **reparented to pid 1** (confirmed: `pgrep -P 1` returns adopted children). The plan's step 2 then runs `pgrep -P 454133` to find them — which returns **empty** because 454133 is no longer their parent. Step 2 kills nothing.

The 4 surviving run.py children then:
1. Are blocked in `proc.wait()` on `docker exec` (`run.py:176`).
2. Step 3 `docker rm -f`'s their containers → the exec dies → `proc.wait()` returns.
3. run.py proceeds: `git add/commit` and `pre_artifacts.sh` via `docker exec cname` → all fail (container gone), but `sh()` (`run.py:56`) returns `CompletedProcess` **without checking returncode** — errors swallowed silently.
4. `patch_bytes = 0` (no patch file) → verifier stage skipped (`status["verifier_exit"] = "skipped_empty_patch"`).
5. **`run.py:381` writes `result.json`** to the OLD path (`runs/qwen-local-om-pilot/<arm>/<task>/rep0/result.json`) with `patch_bytes=0`, `verifier_exit="skipped_empty_patch"`.
6. `run.py:383` appends to `results.jsonl`.

The 4 in-flight cells currently have **no result.json** (confirmed: `find` for them is empty). If the kill works, resume re-runs them. If the kill fails (this finding), they get a degenerate result.json → `run_batch.py:39` (`if result.exists() and not args.force: return skipped`) **skips them on resume** — 4 corrupt cells migrate as "done", never re-run.

**Expected behavior:** All 4 run.py children are dead before any container is removed, so no result.json is ever written for the in-flight cells.
**Why it matters:** Silent data corruption — 4 cells marked complete with empty patches, indistinguishable from real results after migration. The comparison's baseline-vs-OM signal is poisoned.
**Suggested Fix:** Capture child PIDs **before** killing run_batch; kill run_batch + all children **atomically** in one `kill` call:
```sh
# BEFORE any kill:
CHILDREN=$(pgrep -P 454133)          # 3206793 3210907 3236648 3239788
kill -9 454133 $CHILDREN               # atomic: stops spawning + kills workers
docker rm -f $(docker ps -q --filter name=dsw-)
```
Killing run_batch first is correct (it submits all futures upfront, `run_batch.py:90`; killing one child while batch lives → the freed worker spawns a replacement). But the child PIDs must be captured first. SIGKILL (not SIGTERM) for determinism — neither runs `finally` anyway (see F-003).
**Blocking:** yes

### CRITICAL: §4 freeze gate passes if a surviving run.py child finishes and exits before the gate is checked — stale result.json is invisible to all three checks
**Finding ID:** F-002
**File:** `EXECUTION-PLAN-DRAFT.md` §4; `harness/run.py:336-344` (verifier stage)
**Area:** correctness / data integrity
**Issue:**
Even if F-001 is the root cause, the §4 gate is an insufficient backstop for the case where a surviving run.py child **completes and exits** before the gate runs. The verifier stage (`run.py:336-344`) runs `docker run --rm --network none <verifier_image>` with timeout `verifier_timeout_s + 300`. For these tasks `timeout_sec = 5400` (task.toml), so a surviving child can run **up to ~95 minutes** in the verifier with **zero writes to `runs/`** (image build + `--rm` verifier container writes only to docker, not `runs/`).

Timeline of the unsafe path:
- t=0: kill 454133 (F-001: children survive)
- t=0: step 3 `docker rm -f` removes the 4 dsw-* containers
- t=0..95min: surviving run.py children run verifier stage (no `runs/` writes)
- t=done: each writes `result.json` + `results.jsonl`, then exits
- Gate check: `pgrep` empty (run.py exited), `docker ps` empty (dsw-* rm'd in step 3; verifier was `--rm` unnamed — **not matched by `--filter name=dsw-`**), `find -newermt "-2 min"` empty (if >2min since write) → **gate passes with stale result.json on disk**.

The 2-minute `find` cannot detect a `result.json` written >2 min ago. The `pgrep` cannot detect a process that already exited. The `docker ps --filter name=dsw-` does not catch the unnamed `--rm` verifier container.
**Expected behavior:** The gate must detect that new `result.json` files appeared for the 4 in-flight cells since the kill.
**Why it matters:** This is the path by which F-001's corruption becomes silent — the gate green-lights migration of corrupt files.
**Suggested Fix:** Two additions to the plan:
1. **Snapshot before kill:** record `find runs/qwen-local-om-pilot -name result.json | sort` before §3. After §4 passes, diff against a fresh `find` — if any **new** result.json appeared, abort migration (a writer survived and finished).
2. **Explicitly delete** any `result.json`/`results.jsonl` entry for the 4 known in-flight cells (`python-statemachine-state-data-scoping`, `textual-kitty-key-phases` × {baseline, pi-observational-memory} × rep0) after the kill, before the gate — these cells must have no result.json so resume re-runs them.
**Blocking:** yes

### HIGH: §4 presents the 2-min `find` as co-equal with pgrep/docker — but a surviving run.py in verifier image-build (≤1800s) has no writes, so `find` passes while the process is alive
**Finding ID:** F-003
**File:** `EXECUTION-PLAN-DRAFT.md` §4; `harness/run.py:100-106` (`ensure_verifier_image`, build_timeout 1800s); task.toml `build_timeout_sec=1800`
**Area:** correctness
**Issue:**
The three §4 checks are listed as equivalent gates. But `ensure_verifier_image` can spend up to 1800s building with no writes to `runs/`. The `find -newermt "-2 min"` check passes during this window. Only the `pgrep` check catches the alive run.py. An operator who treats the 2-min `find` as sufficient (or who checks it first and sees it empty) could miss a live process.
**Expected behavior:** The gate's primary signal is process/container absence, held over time — not a one-shot file-mtime snapshot.
**Why it matters:** Operator misreading of the gate leads to premature migration.
**Suggested Fix:** Plan §4 should state: pgrep+docker empty is the **primary** gate; hold that empty for the full 2-min window (re-check pgrep after the 2-min wait, not just `find`). The `find` is a secondary catch for non-run.py writers (emit-progress, track_run — both killed in §3, so `find` should also be empty).
**Blocking:** no (but needed for a trustworthy gate)

### HIGH: §3 uses SIGTERM ("if ignored, SIGKILL") — Python never ignores SIGTERM; finally never runs; step 3 is mandatory not a fallback
**Finding ID:** F-004
**File:** `EXECUTION-PLAN-DRAFT.md` §3 step 1 + `[UNVERIFIED]` note; `harness/run.py` (no signal handler), `harness/run_batch.py` (no signal handler)
**Area:** correctness / readability
**Issue:**
The plan's §3 `[UNVERIFIED]` asks "whether kill (SIGTERM) lets run.py reach its finally (docker rm -f cname)". Answer: **NO.** Python's default SIGTERM disposition is `SIG_DFL` (confirmed: `signal.getsignal(SIGTERM) == 0`) — the process terminates immediately via the C default, **`finally` blocks do not run**, and neither `run_batch.py` nor `run.py` install a handler. So SIGTERM and SIGKILL are equivalent here: neither runs cleanup. Step 3 (`docker rm -f`) is **mandatory**, not a fallback. The "if ignored, SIGKILL" phrasing is misleading — Python does not ignore SIGTERM.
**Expected behavior:** Plan states definitively: SIGKILL both; finally does not run; step 3 is mandatory.
**Why it matters:** An operator may expect SIGTERM to trigger graceful container cleanup and skip step 3, leaving orphaned containers.
**Suggested Fix:** Replace §3 step 1 with `kill -9 454133` (and F-001's atomic kill). Remove the `[UNVERIFIED]` note — it's resolved (NO). State: "Neither run_batch nor run.py catches signals; SIGKILL is used because finally/docker-rm-f will not run — step 3 is mandatory."

### MEDIUM: §3 does not verify `watch-and-full-w4.sh` is stopped — it can launch a new run_batch for the full benchmark
**Finding ID:** F-005
**File:** `EXECUTION-PLAN-DRAFT.md` §3; `runs/qwen-local-om-pilot/watch-and-full-w4.sh:64-79` (launches `run_batch.py --run-name qwen-local-om-full-w4`)
**Area:** correctness / operational risk
**Issue:**
`watch-and-full-w4.sh` is an orchestrator that, after the pilot completes cleanly, launches a **second** `run_batch.py` for `qwen-local-om-full-w4`. It is **not currently running** (confirmed: `pgrep -af watch-and-full` → only my own grep; tmux `deep-swe-bench` has 1 idle bash pane). It is also **self-guarding**: if the pilot's run_batch is gone, it breaks its watch loop, attempts validation (fails: <20 results), and exits 1 without launching the full run (`watch-and-full-w4.sh:42-60`). So the re-launch risk is low *right now*. But the plan never verifies it's stopped, and if the user re-runs it from tmux during migration, it could spawn a new run_batch that writes to `runs/qwen-local-om-full-w4/` mid-migration.
**Expected behavior:** The plan explicitly kills/verifies no `watch-and-full-w4.sh` process and warns not to re-run it during migration.
**Why it matters:** A second batch writing during migration re-introduces the exact race the freeze is meant to prevent.
**Suggested Fix:** Add to §3: `pkill -f watch-and-full-w4.sh` (if running). Add to §4 gate: `pgrep -af watch-and-full-w4.sh` must be empty. Note in §6 that the watch script must not be re-run until migration is verified.

### MEDIUM: No re-check of the freeze gate during migration — a late writer races with `mv`
**Finding ID:** F-006
**File:** `EXECUTION-PLAN-DRAFT.md` §4→§5 boundary; `harness/run.py:381-384`
**Area:** correctness
**Issue:**
§4 is checked once, before §5. If any writer survives F-001 and writes `result.json` after the gate passes but during migration, the migration's `mv` of the cell dir races with the write. On Linux, `mv` (rename) of a dir with an open writer can cause the write to land in the **new** path (bind-mount dentry follows rename) or fail with ENOENT — nondeterministic. There is no mid-migration re-check.
**Expected behavior:** Migration refuses to start if any `runs/` file is newer than the gate-check timestamp; or the migration script re-checks pgrep/docker before each batch of moves.
**Why it matters:** A single late write corrupts a migrated cell silently.
**Suggested Fix:** The migration script (`scripts/migrate_results.py`, not yet written — confirmed absent) should: (a) re-run the §4 gate checks at start; (b) record `find runs -name result.json` before and after migration, fail-loud if the set changed; (c) optionally `flock` a sentinel file that writers would need — though killing all writers (F-001) makes this belt-and-suspenders.

### MEDIUM: Paused runs are safe, but only because `shutdown(wait=True)` blocks exit — a KILL during that wait orphans children (the Qwen scenario)
**Finding ID:** F-007
**File:** `harness/run_batch.py:89-107` (pause path); `EXECUTION-PLAN-DRAFT.md` §1b
**Area:** correctness (clarification for the review question)
**Issue:** (Not a defect in paused runs — confirming the review prompt's Q3.)
`ThreadPoolExecutor.cancel()` (`run_batch.py:101`) only prevents **not-yet-started** futures; already-running cells continue. BUT the `with ThreadPoolExecutor` block's `__exit__` calls `shutdown(wait=True)`, which **blocks until all running futures finish** before the process can exit with code 75. So a paused run_batch only exits after all in-flight cells complete — by exit time, no run.py children are alive. This is why the codex55 paused runs (§1b) are safe: they truly have no live processes. **However**, the Qwen kill does NOT use the pause path — it `kill`s run_batch directly, bypassing `shutdown(wait=True)`, which orphans the in-flight children (F-001). The plan correctly treats paused runs as safe (§1b: "already exited"), but should note that the kill path (§3) does NOT benefit from `shutdown(wait=True)` and must manually kill the children.
**Expected behavior:** N/A (clarification).
**Why it matters:** Prevents the operator from assuming "kill ≈ pause" — they have opposite child-survival semantics.
**Suggested Fix:** Add a note to §3: "Unlike the exit-75 pause path (which waits for in-flight cells via `shutdown(wait=True)` before exiting), a `kill` of run_batch does NOT wait — children are orphaned immediately. This is why step 2 must explicitly kill them."
**Blocking:** no

### LOW: 5 Exited dsw-* containers from the paused codex-wf run exist (exit 137) — plan's "do not touch Exited" is correct but unstated rationale
**Finding ID:** F-008
**File:** `docker ps -a --filter name=dsw-` (5 Exited baseline-codex-wf containers, 5h old, exit 137)
**Area:** operational
**Issue:** These are stopped (not writing), belong to a paused codex run. `docker rm -f` on them is harmless cleanup. The plan says "do not touch" without explaining why (they're not a write risk; removing them is fine but unnecessary).
**Suggested Fix:** Note they're stopped codex-wf leftovers, safe to ignore; `docker rm -f` won't match them anyway if the plan filters by `Up` status.
**Blocking:** no

## Answers to the 6 review questions

1. **Does killing 454133 stop its 4 run.py children?** NO. They reparent to pid 1 and keep running. They WILL write a degenerate result.json to the OLD path after step 3 removes their containers (F-001). This is the P0.
2. **Does `docker rm -f` catch all containers? Could a child respawn one? Could watch-and-full-w4.sh re-launch?** docker rm -f catches all 4 live dsw-* containers. A run.py child does NOT respawn a dsw-* container (it does one `docker run -d --name dsw-*` per cell at start; after rm it goes to `docker run --rm` unnamed verifier). watch-and-full-w4.sh is NOT running and is self-guarding (exits 1 if pilot incomplete) — but the plan doesn't verify it's stopped (F-005).
3. **Does cancel() stop already-running cells?** NO — only prevents new ones. BUT `shutdown(wait=True)` in the `with`-exit blocks until running cells finish, so a *paused* (exit-75) run_batch has no live children when it exits. The KILL path bypasses this — that's the Qwen bug (F-001, F-007).
4. **Is 2 min sufficient? What's safer?** NO — a surviving run.py in verifier stage (≤95min, no writes) makes `find` useless. Safer: pgrep+docker empty **held** for 2 min (re-check after wait), plus a before/after result.json snapshot to catch already-finished writers (F-002, F-003).
5. **Race in kill order?** YES — killing batch first (correct, to stop spawning) then `pgrep -P batch` (broken, reparented) leaves children alive → they write result.json after containers are rm -f'd. Fix: capture PIDs before kill, kill atomically (F-001).
6. **Does anything else write result.json or into runs/?** Only `run.py` writes `result.json` (run.py:381) and `results.jsonl` (run.py:383). run_batch writes batch-logs/*.log. analyze.py reads only. track_run.py writes track.out/.pid. emit-progress.py writes .out. watch-and-full-w4.sh writes logs (via tee) and launches run_batch (indirect). **Killing all run.py processes is necessary and sufficient to freeze result.json writes.**

## What's Good
- §2 correctly identifies the two real hazards (run.py re-reads harness per cell; SIGKILL'd run.py orphans its `docker run -d` container). The architectural understanding is sound.
- The §4 gate's combination of pgrep + docker + find is the right *shape* — it just needs the PID-capture fix (F-001) and the snapshot diff (F-002) to be trustworthy.
- Paused runs (§1b) are correctly assessed as safe — confirmed via `shutdown(wait=True)` semantics (F-007).
- The plan correctly orders kill → freeze → migrate → resume and treats §4 as a hard gate.
- The plan correctly accepts losing the 4 in-flight cells (they have no result.json yet — confirmed) IF the kill actually prevents them from writing one.
- No cron/systemd timer re-launches the batch (confirmed: `crontab -l` and `systemctl --user list-timers` empty).
