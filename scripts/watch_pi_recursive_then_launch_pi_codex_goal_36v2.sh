#!/usr/bin/env bash
# Wait for the active pi-recursive batch, then execute one already reviewed and
# confirmed pi-codex-goal launch plan. This script never compiles or confirms a
# plan on the operator's behalf.
set -Eeuo pipefail

ROOT="${ROOT:-/home/will/evals/deep-swe-bench}"
cd "$ROOT"

WAIT_LOG="${WAIT_LOG:-results/gpt-5.5/low/logs/pi-recursive-fixed-tools-12v2-r3-w12.out}"
WAIT_PID="${WAIT_PID:-3219859}"
WAIT_PGREP="${WAIT_PGREP:-harness/run_batch.py --configs pi-recursive --subset 12_v2}"
WAIT_EXPECTED="${WAIT_EXPECTED:-36}"
POLL_SECONDS="${POLL_SECONDS:-30}"

TARGET_RUN="${TARGET_RUN:-pi-codex-goal-gpt55-low-36v2-r3-w12-rpc}"
TARGET_PLAN="${TARGET_PLAN:-runs/launch-plans/$TARGET_RUN.json}"
TARGET_CONFIRMATION="${TARGET_CONFIRMATION:-}"
TARGET_TRACK="${TARGET_TRACK:-runs/$TARGET_RUN/track.out}"
TARGET_LOG="${TARGET_LOG:-results/gpt-5.5/low/logs/$TARGET_RUN.out}"
TARGET_PIDFILE="${TARGET_PIDFILE:-runs/$TARGET_RUN/launcher.pid}"

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

validate_confirmed_plan() {
  if [[ ! -f "$TARGET_PLAN" ]]; then
    log "reviewed launch plan missing: $TARGET_PLAN"
    return 2
  fi
  if [[ -z "$TARGET_CONFIRMATION" ]]; then
    log "TARGET_CONFIRMATION must contain the explicitly approved plan identity"
    return 2
  fi
  python3 - "$TARGET_PLAN" "$TARGET_CONFIRMATION" <<'PY'
import json
import sys
from pathlib import Path

plan_path = Path(sys.argv[1])
confirmation = sys.argv[2]
plan = json.loads(plan_path.read_text())
identity = plan.get("planIdentity")
if confirmation != identity:
    raise SystemExit(
        "Launch plan mismatch: TARGET_CONFIRMATION does not match "
        f"{plan_path}: planned={identity!r}, confirmed={confirmation!r}"
    )
batch_cells = plan.get("batchCells", [])
missing = sum(
    not Path(cell["resultPath"]).is_file()
    for cell in batch_cells
)
print(
    f"confirmed plan={identity} batch_cells={len(batch_cells)} "
    f"missing_result_paths={missing}"
)
PY
}

ensure_no_target_launch_running() {
  local pattern="harness.run_batch execute --plan $TARGET_PLAN"
  if pgrep -f "$pattern" >/dev/null 2>&1; then
    log "confirmed target launch already appears to be running; refusing duplicate"
    pgrep -af "$pattern" || true
    exit 0
  fi
}

launch_target() {
  mkdir -p "$(dirname "$TARGET_TRACK")" "$(dirname "$TARGET_LOG")"
  echo $$ > "$TARGET_PIDFILE"
  log "executing reviewed plan: $TARGET_PLAN"
  log "confirmed identity: $TARGET_CONFIRMATION"
  log "track: $TARGET_TRACK"
  log "log:   $TARGET_LOG"
  set -o pipefail
  python3 -m harness.run_batch execute \
    --plan "$TARGET_PLAN" \
    --confirm "$TARGET_CONFIRMATION" \
    2>&1 | tee "$TARGET_TRACK" "$TARGET_LOG"
}

main() {
  validate_confirmed_plan
  log "watching $WAIT_LOG for [$WAIT_EXPECTED/$WAIT_EXPECTED] and waiting for pi-recursive process exit"
  while true; do
    if wait_batch_done_line_seen; then
      if wait_batch_alive; then
        log "saw [$WAIT_EXPECTED/$WAIT_EXPECTED]; waiting for pi-recursive process to exit"
        while wait_batch_alive; do
          sleep "$POLL_SECONDS"
        done
      fi
      log "pi-recursive batch finished; executing pre-confirmed target plan"
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
