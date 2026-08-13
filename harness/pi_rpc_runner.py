"""Headless RPC driver for running Pi benchmark cells.

The benchmark harness should not use ``pi -p`` for extension-sensitive runs:
print mode is single-shot and can exit before extension follow-up timers fire.
This module drives ``pi --mode rpc`` as a long-lived process, sends the task as
an RPC prompt, keeps stdin open while extensions schedule follow-up work, and
stops only after Pi reports idle state plus a quiet window.

The driver intentionally does not persist the full RPC stdout stream. It keeps a
compact runner log and, when requested, filters advisor ``tool_execution_end``
events into the existing ``tool-usage.jsonl`` sidecar used by parse_usage.py.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO, Any

try:
    from harness.degeneration_watchdog import (
        DegenerationWatchdog,
        DegenerationWatchdogPolicy,
    )
except ModuleNotFoundError:  # Direct ``python harness/pi_rpc_runner.py`` use.
    from degeneration_watchdog import (  # type: ignore[no-redef]
        DegenerationWatchdog,
        DegenerationWatchdogPolicy,
    )


@dataclass
class RpcRunResult:
    """Outcome of a single Pi RPC process."""

    exit_code: int | str
    timed_out: bool = False
    quiescent: bool = False
    prompt_accepted: bool = False
    agent_end_count: int = 0
    event_counts: dict[str, int] = field(default_factory=dict)
    response_errors: list[str] = field(default_factory=list)
    degeneration_watchdog: dict[str, int | str | None] | None = None


class _RpcState:
    def __init__(self, *, now: float) -> None:
        self.lock = threading.RLock()
        self.last_activity = now
        self.event_counts: Counter[str] = Counter()
        self.agent_end_count = 0
        self.prompt_accepted = False
        self.prompt_failed = False
        self.latest_state: dict[str, Any] | None = None
        self.response_errors: list[str] = []
        self.stdout_eof = False
        self.write_error: str | None = None
        self.degeneration_watchdog: dict[str, int | str | None] | None = None


def _json_line(obj: dict[str, Any]) -> str:
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False) + "\n"


def _write_runner_log(log: IO[str], event: str, **fields: Any) -> None:
    log.write(_json_line({"event": event, **fields}))
    log.flush()


def _auto_ui_response(request: dict[str, Any]) -> dict[str, Any] | None:
    """Return a safe noninteractive response for blocking extension UI calls."""
    req_id = request.get("id")
    method = request.get("method")
    if not req_id or not isinstance(method, str):
        return None
    if method == "confirm":
        return {"type": "extension_ui_response", "id": req_id, "confirmed": False}
    if method in {"select", "input", "editor", "custom"}:
        return {"type": "extension_ui_response", "id": req_id, "cancelled": True}
    # notify/status/title/widget/editor-text requests are fire-and-forget in Pi RPC.
    return None


def _send_command(proc: subprocess.Popen[str], stdin_lock: threading.Lock,
                  state: _RpcState, command: dict[str, Any]) -> bool:
    raw = _json_line(command)
    try:
        with stdin_lock:
            if proc.stdin is None or proc.stdin.closed:
                return False
            proc.stdin.write(raw)
            proc.stdin.flush()
        return True
    except (OSError, ValueError) as exc:  # Broken pipe or concurrent close.
        with state.lock:
            state.write_error = str(exc)
        return False


def _is_idle(state_data: dict[str, Any] | None) -> bool:
    if not isinstance(state_data, dict):
        return False
    pending = state_data.get("pendingMessageCount")
    return state_data.get("isStreaming") is False and type(pending) is int and pending == 0


def _is_advisor_usage_event(obj: dict[str, Any]) -> bool:
    """Return true only for advisor tool usage events that should be persisted."""
    return obj.get("type") == "tool_execution_end" and obj.get("toolName") == "advisor"


def _advisor_usage_line(obj: dict[str, Any], raw_line: str) -> str | None:
    """Return the exact sidecar line for an advisor event, preserving raw JSON."""
    if not _is_advisor_usage_event(obj):
        return None
    return raw_line.rstrip("\n") + "\n"


def run_pi_rpc(
    cmd: list[str],
    *,
    prompt_text: str,
    stderr_path: Path,
    runner_log_path: Path,
    advisor_usage_path: Path | None = None,
    timeout_s: float,
    quiescence_s: float = 2.0,
    state_poll_s: float = 0.5,
    shutdown_timeout_s: float = 10.0,
    quiesce_after_agent_end: bool = False,
    degeneration_watchdog_policy: DegenerationWatchdogPolicy | None = None,
) -> RpcRunResult:
    """Run a Pi RPC command until idle plus quiescence or timeout.

    ``cmd`` should launch Pi in RPC mode, usually via ``docker exec -i``. The
    prompt is sent over the RPC protocol rather than as CLI text/file args.
    """
    start = time.monotonic()
    runner_log_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    if advisor_usage_path is not None:
        advisor_usage_path.parent.mkdir(parents=True, exist_ok=True)

    with stderr_path.open("w") as stderr, runner_log_path.open("w") as runner_log:
        advisor_fh = advisor_usage_path.open("w") if advisor_usage_path is not None else None
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=stderr,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        state = _RpcState(now=start)
        stdin_lock = threading.Lock()
        degeneration_watchdog = (
            DegenerationWatchdog(degeneration_watchdog_policy)
            if degeneration_watchdog_policy is not None
            else None
        )

        _write_runner_log(
            runner_log,
            "started",
            transport="rpc",
            prompt_chars=len(prompt_text),
            quiescence_s=quiescence_s,
            state_poll_s=state_poll_s,
            timeout_s=timeout_s,
            degeneration_watchdog_profile=(
                degeneration_watchdog_policy.profile
                if degeneration_watchdog_policy is not None
                else None
            ),
        )

        def handle_obj(obj: dict[str, Any], raw_line: str) -> None:
            typ = str(obj.get("type") or "unknown")
            command = obj.get("command") if typ == "response" else None
            is_state_probe_response = typ == "response" and command == "get_state"
            violation = (
                degeneration_watchdog.observe(obj)
                if degeneration_watchdog is not None
                else None
            )
            with state.lock:
                state.event_counts[typ] += 1
                if not is_state_probe_response:
                    state.last_activity = time.monotonic()

                if typ == "agent_end":
                    state.agent_end_count += 1
                elif typ == "response":
                    if command == "prompt":
                        if obj.get("success") is True:
                            state.prompt_accepted = True
                        else:
                            state.prompt_failed = True
                            state.response_errors.append(str(obj.get("error") or "prompt failed"))
                    elif command == "get_state" and obj.get("success") is True:
                        data = obj.get("data")
                        if isinstance(data, dict):
                            state.latest_state = data
                    elif obj.get("success") is False:
                        state.response_errors.append(str(obj.get("error") or f"{command} failed"))
                if violation is not None and state.degeneration_watchdog is None:
                    state.degeneration_watchdog = violation.to_dict()

            advisor_line = _advisor_usage_line(obj, raw_line)
            if advisor_line is not None and advisor_fh is not None:
                advisor_fh.write(advisor_line)
                advisor_fh.flush()
            elif typ == "extension_ui_request":
                response = _auto_ui_response(obj)
                if response is not None:
                    sent = _send_command(proc, stdin_lock, state, response)
                    _write_runner_log(
                        runner_log,
                        "extension_ui_auto_response",
                        method=obj.get("method"),
                        sent=sent,
                    )

        def read_stdout() -> None:
            assert proc.stdout is not None
            for line in proc.stdout:
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    with state.lock:
                        state.event_counts["invalid_json"] += 1
                        state.last_activity = time.monotonic()
                    _write_runner_log(runner_log, "invalid_stdout_json", bytes=len(line.encode("utf-8")))
                    continue
                if isinstance(obj, dict):
                    handle_obj(obj, line)
            with state.lock:
                state.stdout_eof = True

        reader = threading.Thread(target=read_stdout, name="pi-rpc-stdout", daemon=True)
        reader.start()

        prompt_id = "prompt-1"
        if not _send_command(proc, stdin_lock, state, {"id": prompt_id, "type": "prompt", "message": prompt_text}):
            _write_runner_log(runner_log, "prompt_send_failed")
            if advisor_fh is not None:
                advisor_fh.close()
            return RpcRunResult(exit_code=1, response_errors=["could not write prompt command"])
        _write_runner_log(runner_log, "prompt_sent", id=prompt_id, prompt_chars=len(prompt_text))

        deadline = start + timeout_s
        next_state_poll = start
        timed_out = False
        quiescent = False

        try:
            while True:
                now = time.monotonic()
                returncode = proc.poll()
                with state.lock:
                    prompt_accepted = state.prompt_accepted
                    prompt_failed = state.prompt_failed
                    latest_state = dict(state.latest_state) if state.latest_state else None
                    last_activity = state.last_activity
                    agent_end_count = state.agent_end_count
                    response_errors = list(state.response_errors)
                    write_error = state.write_error
                    degeneration_evidence = state.degeneration_watchdog

                if degeneration_evidence is not None:
                    abort_sent = _send_command(
                        proc,
                        stdin_lock,
                        state,
                        {"id": "degeneration-abort", "type": "abort"},
                    )
                    _write_runner_log(
                        runner_log,
                        "degeneration_watchdog",
                        **degeneration_evidence,
                        abort_sent=abort_sent,
                    )
                    break

                if prompt_failed or write_error:
                    _write_runner_log(
                        runner_log,
                        "rpc_error",
                        response_errors=response_errors,
                        write_error=write_error,
                    )
                    break

                if returncode is not None:
                    _write_runner_log(runner_log, "process_exited", exit_code=returncode, quiescent=False)
                    break

                if now >= deadline:
                    timed_out = True
                    _write_runner_log(runner_log, "timeout", elapsed_s=round(now - start, 3))
                    proc.kill()
                    break

                if prompt_accepted and now >= next_state_poll:
                    _send_command(
                        proc,
                        stdin_lock,
                        state,
                        {"id": f"state-{int((now - start) * 1000)}", "type": "get_state"},
                    )
                    next_state_poll = now + state_poll_s

                state_idle = _is_idle(latest_state)
                agent_end_idle = quiesce_after_agent_end and agent_end_count > 0
                if prompt_accepted and (state_idle or agent_end_idle) and now - last_activity >= quiescence_s:
                    quiescent = True
                    _write_runner_log(
                        runner_log,
                        "quiescent",
                        quiet_s=round(now - last_activity, 3),
                        agent_end_count=state.agent_end_count,
                        reason="state_idle" if state_idle else "agent_end",
                    )
                    break

                time.sleep(min(0.05, max(0.01, state_poll_s / 5)))
        finally:
            if quiescent or not timed_out:
                try:
                    if proc.stdin is not None and not proc.stdin.closed:
                        proc.stdin.close()
                except (OSError, ValueError) as error:
                    _write_runner_log(
                        runner_log,
                        "stdin_close_error",
                        error_type=type(error).__name__,
                    )
            try:
                exit_code = proc.wait(timeout=shutdown_timeout_s)
            except subprocess.TimeoutExpired:
                proc.terminate()
                try:
                    exit_code = proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    exit_code = proc.wait(timeout=2)
            reader.join(timeout=2)
            if advisor_fh is not None:
                advisor_fh.close()

        with state.lock:
            result = RpcRunResult(
                exit_code=(
                    "degeneration"
                    if state.degeneration_watchdog is not None
                    else "timeout" if timed_out else exit_code
                ),
                timed_out=timed_out,
                quiescent=quiescent,
                prompt_accepted=state.prompt_accepted,
                agent_end_count=state.agent_end_count,
                event_counts=dict(state.event_counts),
                response_errors=list(state.response_errors),
                degeneration_watchdog=state.degeneration_watchdog,
            )
        _write_runner_log(
            runner_log,
            "finished",
            exit_code=result.exit_code,
            timed_out=result.timed_out,
            quiescent=result.quiescent,
            prompt_accepted=result.prompt_accepted,
            agent_end_count=result.agent_end_count,
            event_counts=result.event_counts,
            response_errors=result.response_errors,
            degeneration_watchdog=result.degeneration_watchdog,
        )
        return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a Pi RPC process until idle plus quiescence")
    parser.add_argument("--prompt-file", required=True)
    parser.add_argument("--stderr", required=True)
    parser.add_argument("--runner-log", required=True)
    parser.add_argument("--advisor-usage")
    parser.add_argument("--timeout", type=float, required=True)
    parser.add_argument("--quiescence", type=float, default=2.0)
    parser.add_argument("--state-poll", type=float, default=0.5)
    parser.add_argument("--quiesce-after-agent-end", action="store_true",
                        help="also stop after agent_end plus the quiet window, for RPC agents without Pi-style get_state")
    parser.add_argument("cmd", nargs=argparse.REMAINDER, help="command after --, e.g. -- pi --mode rpc ...")
    args = parser.parse_args(argv)
    cmd = args.cmd[1:] if args.cmd[:1] == ["--"] else args.cmd
    if not cmd:
        parser.error("missing command after --")
    result = run_pi_rpc(
        cmd,
        prompt_text=Path(args.prompt_file).read_text(),
        stderr_path=Path(args.stderr),
        runner_log_path=Path(args.runner_log),
        advisor_usage_path=Path(args.advisor_usage) if args.advisor_usage else None,
        timeout_s=args.timeout,
        quiescence_s=args.quiescence,
        state_poll_s=args.state_poll,
        quiesce_after_agent_end=args.quiesce_after_agent_end,
    )
    if result.timed_out:
        return 124
    return int(result.exit_code) if isinstance(result.exit_code, int) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
