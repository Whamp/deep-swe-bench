---
name: runboard
description: Open a live Herdr tab tracking a harness run. Use when the user asks to open a logging tab, track a run, watch a bench, observe progress, tail a run, or get a live progress view for harness/run_batch.py or harness/run.py runs. A runboard is a tail-able one-line-per-cell `.out` file plus a Herdr tab tailing it.
---

# runboard

A **runboard** is two things: a live `.out` file that mirrors `harness/run_batch.py` native stdout (one `[n/N] task / config / repN  status` line per finished cell), and a Herdr tab tailing it. It is the only logging style the user wants for run tracking — never the verbose snapshot dumps (containers, token counts, streamed text).

## Leading rule

**Native-style lines, nothing more.** The runboard is `run_batch.py` stdout reconstructed from `result.json` — one line per cell. No multi-line snapshots. The reference log style is `runs/codex55-medium-om54mini-w2/batch-om-codex55-w2.out`:

```
[71/113] onedump-dump-encryption-pipeline / pi-observational-memory-codex54mini / rep0  ok
```

Status legend: `ok` | `empty` (skipped, no patch) | `timeout` | `transient` | `exit=<n>`.

## Process

1. **Pick the run and expected count.**
   - Run name = the `--run-name` passed to `run_batch.py` (dir lives at `runs/<run>/`).
   - Expected cells = `(#tasks) × (#configs) × (#reps)`. If unsure, `python3 -c "from harness.run_batch import all_task_ids; print(len(all_task_ids()))"` for task count, times the configs in the batch command.

2. **Start the emitter.** Use `scripts/track_run.py` — it polls `result.json` every 15s, appends only new lines (idempotent across restarts), and writes a pidfile next to the `.out`:
   ```sh
   cd /home/will/evals/deep-swe-bench
   nohup python3 scripts/track_run.py <run> --expected <N> \
     >/tmp/<run>-track.nohup 2>&1 &
   echo $! > runs/<run>/track.out.pid   # the long-lived emitter pid
   ```
   - `--expected` is optional but recommended: auto-detect only works once results exist.
   - Default output is `runs/<run>/track.out`; pass `--out` to override.

3. **Open the Herdr tab.** Create a focused tab in the project workspace and tail the `.out`:
   ```sh
   TAB=$(herdr tab create --workspace w6 --cwd "$PWD" --label '<short label>' --focus)
   PANE=$(python3 -c "import json,sys;print(json.load(sys.stdin)['result']['root_pane']['pane_id'])" <<< "$TAB")
   herdr pane run "$PANE" "cd /home/will/evals/deep-swe-bench && tail -n 60 -f runs/<run>/track.out"
   ```
   - Confirm with `herdr pane read "$PANE" --source recent --lines 40 --format text` that lines are flowing.

4. **Verify the tab actually exists and is showing content.** This is mandatory, not optional — see [§ Re-opening / verifying tabs](#re-opening--verifying-tabs) below. Do not report a runboard as live until you have, in the current turn, confirmed the pane exists in `herdr pane list --workspace w6` *and* its recent output contains native-style `[n/N]` lines.

5. **Completion criterion.** The runboard is live when the Herdr tab shows native-style `[n/N]` lines and the tail is flowing. Stop there and report done.

   **Do NOT wait for the first cells to land as a verification step.** That is a blocking action — cells can take many minutes to complete, so waiting for them stalls the rest of the session for no benefit. The emitter and tail are already proven working (the emitter appends lines as `result.json` files appear; the tail follows the file). Trust the existing code. Stop at "tab shows native-style lines and the tail is flowing."

## Re-opening / verifying tabs

**The #1 failure mode is reporting a runboard as "live" from memory without re-verifying the tab still exists.** Tabs do not survive a workspace reset, a herdr restart, or the user closing them. A pane id you recorded in a previous turn (or that lives in compacted memory) is almost always stale by the time you reference it again. *Never* claim a tab is "flowing" or "live" based on a remembered pane id.

Rules:

1. **Never trust a remembered pane/tab id.** Tab ids like `w6:pM` from earlier in the session may already be gone. Always confirm against live state.
2. **Confirm the pane exists** before reporting success:
   ```sh
   herdr pane list --workspace w6 | rg '<pane_id>'   # must print the pane
   ```
3. **Confirm the pane is showing track content**, not just that it exists:
   ```sh
   herdr pane read <pane_id> --source recent --lines 5 --format text   # must show [n/N] lines
   ```
   A pane can exist but be showing a shell prompt, an error, or the wrong file.
4. **If reopening after any gap** (a new turn, a resume, an overnight pause), assume the old tabs are gone. Re-list the workspace, find the current tabs, and only reopen a tab once you've confirmed none of the existing ones already tail the right `.out` (don't create duplicates).
5. **Don't conflate the emitter with the tab.** The `track.out` file updating on disk does not mean a Herdr tab is pointing at it. They are independent — verify the tab, not just the file.

If a tab is missing or stale, open a fresh one with the step-3 commands above and verify it in the same turn. Only then report the runboard as live.

## When NOT to use this skill

- The user wants *analysis* (reward comparison, token totals) — that is `harness/analyze.py`, not a runboard.
- The run is a single `harness/run.py` cell, not a batch — no per-cell log to tail; just `tail -f` the cell's `pi.jsonl` if asked.
- The user asks for verbose live introspection (containers, last streamed text). That is a different request; confirm before dumping snapshots, since the user has rejected that style for ordinary run tracking.

## Multiple simultaneous runs

If several runs are in flight, give each its own Herdr tab with a distinct label (e.g. `Qwen track`, `Codex track`). One emitter per run; the script writes to its own `runs/<run>/track.out`. When reporting status across several runboards, verify each tab individually in the current turn — do not batch-claim "all tabs flowing" from memory.
