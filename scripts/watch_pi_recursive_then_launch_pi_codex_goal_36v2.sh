#!/usr/bin/env bash
# Wait for the active pi-recursive 12_v2 batch to finish 36/36, then launch
# pi-codex-goal on 36_v2 with 3 reps. Intended to be started with nohup/setsid.
set -Eeuo pipefail

ROOT="${ROOT:-/home/will/evals/deep-swe-bench}"
cd "$ROOT"

WAIT_LOG="${WAIT_LOG:-results/gpt-5.5/low/logs/pi-recursive-fixed-tools-12v2-r3-w12.out}"
WAIT_PID="${WAIT_PID:-3219859}"
WAIT_PGREP="${WAIT_PGREP:-harness/run_batch.py --configs pi-recursive --subset 12_v2}"
WAIT_EXPECTED="${WAIT_EXPECTED:-36}"
POLL_SECONDS="${POLL_SECONDS:-30}"

TARGET_RUN="${TARGET_RUN:-pi-codex-goal-gpt55-low-36v2-r3-w12-rpc}"
TARGET_TRACK="${TARGET_TRACK:-runs/$TARGET_RUN/track.out}"
TARGET_LOG="${TARGET_LOG:-results/gpt-5.5/low/logs/$TARGET_RUN.out}"
TARGET_PIDFILE="${TARGET_PIDFILE:-runs/$TARGET_RUN/launcher.pid}"
SUBSET="${SUBSET:-36_v2}"
CONFIG="${CONFIG:-pi-codex-goal}"
MODEL="${MODEL:-openai-codex/gpt-5.5}"
THINKING="${THINKING:-low}"
RUNS="${RUNS:-3}"
WORKERS="${WORKERS:-12}"
AGENT_TIMEOUT="${AGENT_TIMEOUT:-5400}"
RPC_QUIESCENCE="${RPC_QUIESCENCE:-2}"

log() {
  printf '[%(%Y-%m-%dT%H:%M:%S%z)T] %s\n' -1 "$*"
}

wait_batch_alive() {
  if [[ -n "$WAIT_PID" ]] && ps -p "$WAIT_PID" >/dev/null 2>&1; then
    return 0
  fi
  pgrep -f "$WAIT_PGREP" >/dev/null 2>&1
}

wait_batch_done_line_seen() {
  [[ -f "$WAIT_LOG" ]] && grep -Eq "^\[$WAIT_EXPECTED/$WAIT_EXPECTED\] " "$WAIT_LOG"
}

count_existing_target_cells() {
  python3 - <<'PY'
from pathlib import Path
subset = [ln.strip() for ln in Path('subsets/36_v2.txt').read_text().splitlines() if ln.strip()]
base = Path('results/gpt-5.5/low/pi-codex-goal')
count = 0
for task in subset:
    for rep in range(3):
        if (base / task / f'rep{rep}' / 'result.json').exists():
            count += 1
print(count)
PY
}

ensure_no_target_launch_running() {
  if pgrep -f "harness/run_batch.py --configs $CONFIG --subset $SUBSET" >/dev/null 2>&1; then
    log "target launch already appears to be running; refusing duplicate launch"
    pgrep -af "harness/run_batch.py --configs $CONFIG --subset $SUBSET" || true
    exit 0
  fi
}

launch_target() {
  mkdir -p "$(dirname "$TARGET_TRACK")" "$(dirname "$TARGET_LOG")"
  echo $$ > "$TARGET_PIDFILE"
  local existing expected missing
  existing="$(count_existing_target_cells)"
  expected=$((36 * RUNS))
  missing=$((expected - existing))
  if (( missing <= 0 )); then
    log "target already complete: $existing/$expected cells exist; nothing to launch"
    return 0
  fi
  log "launching $CONFIG on $SUBSET: existing=$existing expected=$expected missing=$missing workers=$WORKERS timeout=${AGENT_TIMEOUT}s"
  log "track: $TARGET_TRACK"
  log "log:   $TARGET_LOG"
  set -o pipefail
  python3 harness/run_batch.py \
    --configs "$CONFIG" \
    --subset "$SUBSET" \
    --model "$MODEL" \
    --thinking "$THINKING" \
    --runs "$RUNS" \
    --workers "$WORKERS" \
    --agent-timeout "$AGENT_TIMEOUT" \
    --rpc-quiescence "$RPC_QUIESCENCE" \
    --pass-openai-codex-oauth \
    2>&1 | tee "$TARGET_TRACK" "$TARGET_LOG"
}

main() {
  log "watching $WAIT_LOG for [$WAIT_EXPECTED/$WAIT_EXPECTED] and waiting for pi-recursive process exit"
  while true; do
    if wait_batch_done_line_seen; then
      if wait_batch_alive; then
        log "saw [$WAIT_EXPECTED/$WAIT_EXPECTED]; waiting for pi-recursive process to exit"
        while wait_batch_alive; do
          sleep "$POLL_SECONDS"
        done
      fi
      log "pi-recursive batch finished; preparing target launch"
      ensure_no_target_launch_running
      launch_target
      log "target launch finished"
      return 0
    fi

    if ! wait_batch_alive; then
      log "pi-recursive process is gone but $WAIT_LOG has no [$WAIT_EXPECTED/$WAIT_EXPECTED] line; refusing target launch"
      tail -n 40 "$WAIT_LOG" || true
      return 2
    fi

    tail_line="$(grep -E '^\[[0-9]+/[0-9]+\] ' "$WAIT_LOG" 2>/dev/null | tail -n 1 || true)"
    log "still waiting; latest progress: ${tail_line:-none yet}"
    sleep "$POLL_SECONDS"
  done
}

main "$@"
