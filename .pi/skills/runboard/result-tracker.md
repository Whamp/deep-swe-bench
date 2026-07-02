# Result-only tracker reconstruction

Use this only when there is no live `runs/<run>/track.out` from
`harness/run_batch.py`. The goal is to create the compatibility layout that
`scripts/track_run.py` reads:

```txt
runs/<run>/<config>/<task>/repN/result.json
```

Current benchmark results live under:

```txt
results/<model>/<thinking>/<config>/<task>/repN/result.json
```

## Subset or task-filtered runs

Use per-task symlinks. This avoids the bug where a broad config symlink counts
old results for unrelated tasks.

```sh
cd /home/will/evals/deep-swe-bench
RUN='<short-run-name>'
MODEL_LEAF='gpt-5.5'
THINKING='low'
CONFIGS='baseline observational-memory'
TASK_FILE='subsets/12_v2.txt'
REPS=3

mkdir -p "runs/$RUN"
for cfg in $CONFIGS; do
  mkdir -p "runs/$RUN/$cfg"
  while IFS= read -r task; do
    [ -n "$task" ] || continue
    ln -sfn "$PWD/results/$MODEL_LEAF/$THINKING/$cfg/$task" "runs/$RUN/$cfg/$task"
  done < "$TASK_FILE"
done
EXPECTED=$(( $(grep -cv '^$' "$TASK_FILE") * $(wc -w <<< "$CONFIGS") * REPS ))
```

## Full-config runs

Only if the result leaf contains exactly the intended tasks, a config-level
symlink is acceptable:

```sh
ln -sfn "$PWD/results/$MODEL_LEAF/$THINKING/$cfg" "runs/$RUN/$cfg"
```

Do not use a broad config-level symlink for repairs or subsets.

## Start/reuse the emitter

Use `setsid + nohup` so the tracker survives shell cleanup. `track_run.py`
writes `track.out.pid` next to the output.

```sh
OUT="runs/$RUN/track.out"
PIDFILE="runs/$RUN/track.out.pid"

if [ -f "$PIDFILE" ] && ps -p "$(cat "$PIDFILE")" >/dev/null 2>&1; then
  echo "tracker already running: $(cat "$PIDFILE")"
else
  setsid nohup python3 scripts/track_run.py "$RUN" --expected "$EXPECTED" --out "$OUT" \
    > "runs/$RUN/track.log" 2>&1 < /dev/null &
fi
```

Then run:

```sh
scripts/open_runboard.py --run "$RUN" --label '<short label>'
```
