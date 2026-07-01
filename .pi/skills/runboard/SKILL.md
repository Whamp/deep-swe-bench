---
name: runboard
description: Open a live Herdr tab tracking a harness run. Use when the user asks to open a logging tab, track a run, watch a bench, observe progress, tail a run, or get a live progress view for harness/run_batch.py or harness/run.py runs. A runboard is a tail-able one-line-per-cell `.out` file plus a Herdr tab tailing it.
---

# runboard

A **runboard** is two things: a live `.out` file that mirrors `harness/run_batch.py` native stdout, and a Herdr tab tailing it. The file has one native-style line per finished cell:

```txt
[71/113] onedump-dump-encryption-pipeline / observational-memory / rep0  ok
```

Use this style only. Do not create verbose snapshot dumps with containers, token counts, streamed text, or repeated state blocks.

Status legend: `ok` | `empty` | `timeout` | `transient` | `exit=<n>`.

## Hard preflight

1. **Verify Herdr.** Before any Herdr command:
   ```sh
   test "${HERDR_ENV:-}" = 1
   ```
   If this is not true, say you are not running inside a Herdr-managed pane and stop. Do not inspect or control Herdr from outside Herdr.

2. **Discover current IDs live.** Herdr workspace, tab, and pane IDs are not durable. Never trust remembered IDs or old `herdr-pane.id` files. Get the current workspace from the focused pane:
   ```sh
   PANE_LIST=$(herdr pane list)
   WORKSPACE=$(python3 -c 'import json,sys; panes=json.load(sys.stdin)["result"]["panes"]; print(next(p["workspace_id"] for p in panes if p.get("focused")))' <<< "$PANE_LIST")
   ```

3. **Check for an existing runboard.** Before creating a new tab, list panes in the current workspace and read likely candidates. If a pane already tails the right `runs/<run>/track.out` and shows native `[n/N]` lines, reuse it. Do not create duplicates.

## Build or verify the tracker input

`track_run.py` reads the compatibility layout:

```txt
runs/<run>/<config>/<task>/repN/result.json
```

Current benchmark results live under:

```txt
results/<model>/<thinking>/<config>/<task>/repN/result.json
```

So a runboard usually needs a compatibility tree under `runs/<run>/`.

### Preferred setup for subset or task-filtered runs

Use per-task symlinks. This avoids the common bug where a config directory contains old results for extra tasks and `track_run.py` counts unrelated cells.

```sh
cd /home/will/evals/deep-swe-bench
RUN='<short-run-name>'
MODEL_LEAF='gpt-5.5'        # e.g. deepseek-v4-flash, Qwen3.6-27B-AWQ-BF16-INT4
THINKING='low'
CONFIGS='baseline observational-memory'
TASK_FILE='subsets/12_v2.txt'   # or a temp file with exact task ids

mkdir -p "runs/$RUN"
for cfg in $CONFIGS; do
  mkdir -p "runs/$RUN/$cfg"
  while IFS= read -r task; do
    [ -n "$task" ] || continue
    ln -sfn "$PWD/results/$MODEL_LEAF/$THINKING/$cfg/$task" "runs/$RUN/$cfg/$task"
  done < "$TASK_FILE"
done
```

For full-config runs where the result leaf contains only the intended tasks, a config-level symlink is acceptable:

```sh
ln -sfn "$PWD/results/$MODEL_LEAF/$THINKING/$cfg" "runs/$RUN/$cfg"
```

Do **not** use a broad config-level symlink for one-task repairs or subset runs if that config already has other completed tasks. It will produce misleading counts like `[40/3]`.

## Start or reuse the emitter

Use `setsid + nohup`, not plain `nohup`, so the tracker survives shell cleanup. `track_run.py` writes its own pidfile next to the output file.

```sh
EXPECTED=$(( task_count * config_count * rep_count ))
OUT="runs/$RUN/track.out"
PIDFILE="runs/$RUN/track.out.pid"

if [ -f "$PIDFILE" ] && ps -p "$(cat "$PIDFILE")" >/dev/null 2>&1; then
  echo "tracker already running: $(cat "$PIDFILE")"
else
  setsid nohup python3 scripts/track_run.py "$RUN" --expected "$EXPECTED" --out "$OUT" \
    > "runs/$RUN/track.log" 2>&1 < /dev/null &
fi
```

Use `--expected` whenever possible. Auto-detection works only after results exist and can be wrong if the compatibility tree includes extra tasks.

## Open the Herdr tab

Create a tab in the live current workspace and tail the tracker:

```sh
TAB_JSON=$(herdr tab create --workspace "$WORKSPACE" --label '<short label>')
PANE=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["result"]["root_pane"]["pane_id"])' <<< "$TAB_JSON")
herdr pane run "$PANE" "cd /home/will/evals/deep-swe-bench && tail -n 60 -f runs/$RUN/track.out"
```

Do not treat saved pane IDs as authority. A saved `herdr-pane.id` is only a breadcrumb for humans; re-list panes before using it.

## Verify before reporting success

A runboard is live only after both checks pass in the current turn:

```sh
herdr pane list --workspace "$WORKSPACE" | grep -F "$PANE"
herdr pane read "$PANE" --source recent --lines 20
```

The pane read must show native `[n/N] task / config / repN  status` lines. If wrapping makes the output hard to inspect, use:

```sh
herdr pane read "$PANE" --source recent-unwrapped --lines 20
```

Do not claim a runboard is live merely because `track.out` exists, a tracker process exists, or a pane ID exists. The Herdr pane must exist now and show the right tracker content now.

Do not wait for new cells to finish just to verify a runboard. Existing native lines prove the tail and file are connected. If no cells exist yet, verify the pane shows the `running N cells:` header and the tail command is active.

## Reopening or checking old runboards

After any gap, assume old IDs may be stale.

1. Run `herdr pane list`.
2. Find candidate panes by tab label or by reading recent output.
3. Confirm the pane still shows the intended `track.out` content.
4. Only then say the old runboard is still live.

If the old pane is gone or stale, open a new tab and verify it. Do not report from memory.

## Multiple simultaneous runs

Give each active batch its own Herdr tab with a distinct label, such as `Qwen track`, `Codex track`, or `DeepSeek isolate track`. Verify each tab separately in the current turn.

## When not to use this skill

- The user wants reward/token analysis. Use `harness/analyze.py` or the analysis scripts.
- The run is a single `harness/run.py` cell. There is no per-cell batch log; tail that cell's logs only if asked.
- The user asks for deep live debugging. Ask before dumping containers, streamed text, or verbose state snapshots.
